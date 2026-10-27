"""
Client Time Entry Approval Service
Handles client-side approval workflow for time entries
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from flask_babel import gettext as _

from app import db
from app.models import Client, TimeEntry
from app.models.client_time_approval import ClientApprovalPolicy, ClientApprovalStatus, ClientTimeApproval
from app.utils.i18n_helpers import in_client_locale

logger = logging.getLogger(__name__)


class ClientApprovalService:
    """Service for managing client-side time entry approvals"""

    def request_approval(self, time_entry_id: int, requested_by: int, comment: str = None) -> Dict[str, Any]:
        """Request client approval for a time entry"""
        time_entry = TimeEntry.query.get(time_entry_id)
        if not time_entry:
            return {"success": False, "message": _("Time entry not found"), "error": "not_found"}

        project = time_entry.project
        if not project or not project.client_id:
            return {"success": False, "message": _("Project has no associated client"), "error": "no_client"}

        client = Client.query.get(project.client_id)
        if not client:
            return {"success": False, "message": _("Client not found"), "error": "client_not_found"}

        # Check if already pending
        existing = ClientTimeApproval.query.filter_by(
            time_entry_id=time_entry_id, status=ClientApprovalStatus.PENDING
        ).first()

        if existing:
            return {"success": False, "message": _("Approval already pending"), "error": "already_pending"}

        # Create approval request
        approval = ClientTimeApproval(
            time_entry_id=time_entry_id,
            project_id=project.id,
            client_id=client.id,
            requested_by=requested_by,
            status=ClientApprovalStatus.PENDING,
            request_comment=comment,
        )
        db.session.add(approval)
        db.session.commit()

        # Real-time: emit to client portal room
        try:
            from app import socketio

            socketio.emit(
                "client_approval_update",
                {"approval_id": approval.id, "status": approval.status.value, "event": "requested"},
                room=f"client_portal_{client.id}",
            )
        except Exception as e:
            logger.debug("SocketIO emit for client approval skipped: %s", e)

        # Notify client contacts
        self._notify_client_contacts(client, approval)

        # Create in-app notification
        try:
            from app.services.client_notification_service import ClientNotificationService

            notification_service = ClientNotificationService()
            notification_service.notify_time_entry_approval(approval.id, client.id)
        except Exception as e:
            logger.error(f"Failed to create client notification for approval {approval.id}: {e}", exc_info=True)

        return {"success": True, "message": _("Approval requested"), "approval": approval.to_dict()}

    def approve(self, approval_id: int, contact_id: int, comment: str = None) -> Dict[str, Any]:
        """Approve a time entry (client-side)"""
        approval = ClientTimeApproval.query.get(approval_id)
        if not approval:
            return {"success": False, "message": _("Approval not found"), "error": "not_found"}

        if approval.status != ClientApprovalStatus.PENDING:
            return {"success": False, "message": _("Approval is not pending"), "error": "invalid_status"}

        approval.approve(contact_id, comment)
        self._emit_approval_update(approval, "approved")
        self._notify_requester(approval, "approved", comment)

        return {"success": True, "message": _("Time entry approved"), "approval": approval.to_dict()}

    def reject(self, approval_id: int, contact_id: int, reason: str) -> Dict[str, Any]:
        """Reject a time entry (client-side)"""
        approval = ClientTimeApproval.query.get(approval_id)
        if not approval:
            return {"success": False, "message": _("Approval not found"), "error": "not_found"}

        if approval.status != ClientApprovalStatus.PENDING:
            return {"success": False, "message": _("Approval is not pending"), "error": "invalid_status"}

        approval.reject(contact_id, reason)
        self._emit_approval_update(approval, "rejected")
        self._notify_requester(approval, "rejected", reason)

        return {"success": True, "message": _("Time entry rejected"), "approval": approval.to_dict()}

    def get_pending_approvals_for_client(self, client_id: int) -> List[ClientTimeApproval]:
        """Get pending approvals for a client with error handling"""
        try:
            return (
                ClientTimeApproval.query.filter_by(client_id=client_id, status=ClientApprovalStatus.PENDING)
                .order_by(ClientTimeApproval.requested_at.desc())
                .all()
            )
        except Exception as e:
            logger.error(f"Error getting pending approvals for client {client_id}: {e}", exc_info=True)
            # Rollback any failed transaction
            try:
                db.session.rollback()
            except Exception as rollback_error:
                logger.error(f"Error during rollback: {rollback_error}", exc_info=True)
            # Return empty list on error to prevent cascading failures
            return []

    def _emit_approval_update(self, approval: ClientTimeApproval, event: str):
        """Emit SocketIO event to client portal room when approval status changes."""
        if not approval.client_id:
            return
        try:
            from app import socketio

            socketio.emit(
                "client_approval_update",
                {"approval_id": approval.id, "status": approval.status.value, "event": event},
                room=f"client_portal_{approval.client_id}",
            )
        except Exception as e:
            logger.debug("SocketIO emit for client approval update skipped: %s", e)

    @in_client_locale(lambda self, *a, **k: k.get("client", a[0] if a else None))
    def _notify_client_contacts(self, client: Client, approval: ClientTimeApproval):
        """Send notifications to client contacts"""
        from app.models import Contact
        from app.utils.notification_service import NotificationService

        service = NotificationService()

        # Get client contacts
        contacts = Contact.query.filter_by(client_id=client.id, is_active=True).all()

        for contact in contacts:
            if contact.email:
                # Send email notification
                from app.utils.email import send_template_email

                try:
                    send_template_email(
                        to=contact.email,
                        subject=_("Time Entry Approval Requested - %(project)s", project=approval.time_entry.project.name),
                        template="email/client_approval_request.html",
                        approval=approval,
                        contact=contact,
                    )
                except Exception as e:
                    logger.error(f"Error sending approval email to {contact.email}: {e}")

    def _notify_requester(self, approval: ClientTimeApproval, status: str, reason: str = None):
        """Send notification to requester"""
        from app.utils.notification_service import NotificationService

        service = NotificationService()
        if status == "approved":
            message = _("Client has approved time entry %(id)s.", id=approval.time_entry_id)
            title = _("Time Entry Approved")
        else:
            message = _("Client has rejected time entry %(id)s.", id=approval.time_entry_id)
            title = _("Time Entry Rejected")
        if reason:
            message += " " + _("Reason: %(reason)s", reason=reason)

        service.send_notification(
            user_id=approval.requested_by,
            title=title,
            message=message,
            type="success" if status == "approved" else "error",
            priority="normal",
        )
