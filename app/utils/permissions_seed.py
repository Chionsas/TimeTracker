"""Utility module for seeding default permissions and roles"""

from sqlalchemy.exc import IntegrityError

from app import db
from app.models import Permission, Role, User
from app.utils.i18n_helpers import N_

# Category headings as the role and permission pages show them: the category key
# with underscores as spaces, capitalised. Listed here only to mark them for extraction.
PERMISSION_CATEGORY_LABELS = (
    N_("Administration"),
    N_("Clients"),
    N_("Inventory"),
    N_("Invoices"),
    N_("Issues"),
    N_("Projects"),
    N_("Reports"),
    N_("System"),
    N_("Tasks"),
    N_("Time entries"),
    N_("Users"),
)

# Define all available permissions organized by category
DEFAULT_PERMISSIONS = [
    # Time Entry Permissions
    {"name": "view_own_time_entries", "description": N_("View own time entries"), "category": "time_entries"},
    {
        "name": "view_all_time_entries",
        "description": N_("View all time entries from all users"),
        "category": "time_entries",
    },
    {"name": "create_time_entries", "description": N_("Create time entries"), "category": "time_entries"},
    {"name": "edit_own_time_entries", "description": N_("Edit own time entries"), "category": "time_entries"},
    {"name": "edit_all_time_entries", "description": N_("Edit time entries from all users"), "category": "time_entries"},
    {"name": "delete_own_time_entries", "description": N_("Delete own time entries"), "category": "time_entries"},
    {
        "name": "delete_all_time_entries",
        "description": N_("Delete time entries from all users"),
        "category": "time_entries",
    },
    # Project Permissions
    {"name": "view_projects", "description": N_("View all projects (legacy alias)"), "category": "projects"},
    {"name": "view_own_projects", "description": N_("View own projects"), "category": "projects"},
    {"name": "view_all_projects", "description": N_("View all projects"), "category": "projects"},
    {"name": "create_projects", "description": N_("Create new projects"), "category": "projects"},
    {"name": "edit_projects", "description": N_("Edit all projects (legacy alias)"), "category": "projects"},
    {"name": "edit_own_projects", "description": N_("Edit own projects"), "category": "projects"},
    {"name": "edit_all_projects", "description": N_("Edit all projects"), "category": "projects"},
    {"name": "delete_projects", "description": N_("Delete all projects (legacy alias)"), "category": "projects"},
    {"name": "delete_own_projects", "description": N_("Delete own projects"), "category": "projects"},
    {"name": "delete_all_projects", "description": N_("Delete all projects"), "category": "projects"},
    {"name": "archive_projects", "description": N_("Archive/unarchive projects"), "category": "projects"},
    {"name": "manage_project_costs", "description": N_("Manage project costs and budgets"), "category": "projects"},
    # Task Permissions
    {"name": "view_own_tasks", "description": N_("View own tasks"), "category": "tasks"},
    {"name": "view_all_tasks", "description": N_("View all tasks"), "category": "tasks"},
    {"name": "create_tasks", "description": N_("Create tasks"), "category": "tasks"},
    {"name": "edit_own_tasks", "description": N_("Edit own tasks"), "category": "tasks"},
    {"name": "edit_all_tasks", "description": N_("Edit all tasks"), "category": "tasks"},
    {"name": "delete_own_tasks", "description": N_("Delete own tasks"), "category": "tasks"},
    {"name": "delete_all_tasks", "description": N_("Delete all tasks"), "category": "tasks"},
    {"name": "assign_tasks", "description": N_("Assign tasks to users"), "category": "tasks"},
    # Client Permissions
    {"name": "view_clients", "description": N_("View all clients (legacy alias)"), "category": "clients"},
    {"name": "view_own_clients", "description": N_("View own clients"), "category": "clients"},
    {"name": "view_all_clients", "description": N_("View all clients"), "category": "clients"},
    {"name": "create_clients", "description": N_("Create new clients"), "category": "clients"},
    {"name": "edit_clients", "description": N_("Edit all clients (legacy alias)"), "category": "clients"},
    {"name": "edit_own_clients", "description": N_("Edit own clients"), "category": "clients"},
    {"name": "edit_all_clients", "description": N_("Edit all clients"), "category": "clients"},
    {"name": "delete_clients", "description": N_("Delete all clients (legacy alias)"), "category": "clients"},
    {"name": "delete_own_clients", "description": N_("Delete own clients"), "category": "clients"},
    {"name": "delete_all_clients", "description": N_("Delete all clients"), "category": "clients"},
    {"name": "manage_client_notes", "description": N_("Manage client notes"), "category": "clients"},
    # Issue Permissions
    {"name": "view_all_issues", "description": N_("View all issues from all clients"), "category": "issues"},
    {"name": "view_own_issues", "description": N_("View issues for assigned clients/projects"), "category": "issues"},
    {"name": "create_issues", "description": N_("Create new issues"), "category": "issues"},
    {"name": "edit_all_issues", "description": N_("Edit all issues"), "category": "issues"},
    {"name": "edit_own_issues", "description": N_("Edit issues for assigned clients/projects"), "category": "issues"},
    {"name": "delete_issues", "description": N_("Delete issues"), "category": "issues"},
    # Invoice Permissions
    {"name": "view_own_invoices", "description": N_("View own invoices"), "category": "invoices"},
    {"name": "view_all_invoices", "description": N_("View all invoices"), "category": "invoices"},
    {"name": "create_invoices", "description": N_("Create invoices"), "category": "invoices"},
    {"name": "edit_invoices", "description": N_("Edit invoices"), "category": "invoices"},
    {"name": "delete_invoices", "description": N_("Delete invoices"), "category": "invoices"},
    {"name": "send_invoices", "description": N_("Send invoices to clients"), "category": "invoices"},
    {"name": "manage_payments", "description": N_("Manage invoice payments"), "category": "invoices"},
    {"name": "manage_payment_gateways", "description": N_("Manage payment gateway configurations"), "category": "invoices"},
    # Report Permissions
    {"name": "view_own_reports", "description": N_("View own reports"), "category": "reports"},
    {"name": "view_all_reports", "description": N_("View reports for all users"), "category": "reports"},
    {"name": "export_reports", "description": N_("Export reports to CSV/PDF"), "category": "reports"},
    {"name": "create_saved_reports", "description": N_("Create and save custom reports"), "category": "reports"},
    # User Management Permissions
    {"name": "view_users", "description": N_("View users list"), "category": "users"},
    {"name": "create_users", "description": N_("Create new users"), "category": "users"},
    {"name": "edit_users", "description": N_("Edit user details"), "category": "users"},
    {"name": "delete_users", "description": N_("Delete users"), "category": "users"},
    {"name": "manage_user_roles", "description": N_("Assign roles to users"), "category": "users"},
    # System Permissions
    {"name": "manage_settings", "description": N_("Manage system settings"), "category": "system"},
    {"name": "view_system_info", "description": N_("View system information"), "category": "system"},
    {"name": "manage_backups", "description": N_("Create and restore backups"), "category": "system"},
    {"name": "manage_telemetry", "description": N_("Manage telemetry settings"), "category": "system"},
    {"name": "view_audit_logs", "description": N_("View audit logs"), "category": "system"},
    # Role & Permission Management (Super Admin only)
    {"name": "manage_roles", "description": N_("Create, edit, and delete roles"), "category": "administration"},
    {"name": "manage_permissions", "description": N_("Assign permissions to roles"), "category": "administration"},
    {"name": "view_permissions", "description": N_("View permissions and roles"), "category": "administration"},
    # Inventory Management Permissions
    {"name": "view_inventory", "description": N_("View inventory items and stock levels"), "category": "inventory"},
    {"name": "manage_stock_items", "description": N_("Create, edit, and delete stock items"), "category": "inventory"},
    {"name": "manage_warehouses", "description": N_("Create, edit, and delete warehouses"), "category": "inventory"},
    {"name": "view_stock_levels", "description": N_("View current stock levels"), "category": "inventory"},
    {
        "name": "manage_stock_movements",
        "description": N_("Record stock movements and adjustments"),
        "category": "inventory",
    },
    {"name": "transfer_stock", "description": N_("Transfer stock between warehouses"), "category": "inventory"},
    {"name": "view_stock_history", "description": N_("View stock movement history"), "category": "inventory"},
    {
        "name": "manage_stock_reservations",
        "description": N_("Create and manage stock reservations"),
        "category": "inventory",
    },
    {"name": "view_inventory_reports", "description": N_("View inventory reports"), "category": "inventory"},
    {
        "name": "approve_stock_adjustments",
        "description": N_("Approve stock adjustments (if approval workflow enabled)"),
        "category": "inventory",
    },
    {"name": "manage_suppliers", "description": N_("Create, edit, and delete suppliers"), "category": "inventory"},
    {
        "name": "manage_purchase_orders",
        "description": N_("Create, edit, and manage purchase orders"),
        "category": "inventory",
    },
]


# Define default roles with their permissions
DEFAULT_ROLES = {
    "super_admin": {
        "description": N_("Super Administrator with full system access"),
        "is_system_role": True,
        "permissions": [p["name"] for p in DEFAULT_PERMISSIONS],  # All permissions
    },
    "admin": {
        "description": N_("Administrator with most privileges"),
        "is_system_role": True,
        "permissions": [
            # Time entries
            "view_all_time_entries",
            "create_time_entries",
            "edit_all_time_entries",
            "delete_all_time_entries",
            # Projects
            "view_projects",
            "view_all_projects",
            "create_projects",
            "edit_projects",
            "edit_all_projects",
            "delete_projects",
            "delete_all_projects",
            "archive_projects",
            "manage_project_costs",
            # Tasks
            "view_all_tasks",
            "create_tasks",
            "edit_all_tasks",
            "delete_all_tasks",
            "assign_tasks",
            # Clients
            "view_clients",
            "view_all_clients",
            "create_clients",
            "edit_clients",
            "edit_all_clients",
            "delete_clients",
            "delete_all_clients",
            "manage_client_notes",
            # Invoices
            "view_all_invoices",
            "create_invoices",
            "edit_invoices",
            "delete_invoices",
            "send_invoices",
            "manage_payments",
            "manage_payment_gateways",
            # Reports
            "view_all_reports",
            "export_reports",
            "create_saved_reports",
            # Users
            "view_users",
            "create_users",
            "edit_users",
            "delete_users",
            # System
            "manage_settings",
            "view_system_info",
            "manage_backups",
            "manage_telemetry",
            "view_audit_logs",
            # Inventory
            "view_inventory",
            "manage_stock_items",
            "manage_warehouses",
            "view_stock_levels",
            "manage_stock_movements",
            "transfer_stock",
            "view_stock_history",
            "manage_stock_reservations",
            "view_inventory_reports",
            "approve_stock_adjustments",
            "manage_suppliers",
            "manage_purchase_orders",
            # Issues
            "view_all_issues",
            "create_issues",
            "edit_all_issues",
        ],
    },
    "manager": {
        "description": N_("Team Manager with oversight capabilities"),
        "is_system_role": True,
        "permissions": [
            # Time entries
            "view_all_time_entries",
            "create_time_entries",
            "edit_own_time_entries",
            "delete_own_time_entries",
            # Projects
            "view_projects",
            "view_all_projects",
            "create_projects",
            "edit_projects",
            "edit_all_projects",
            "delete_projects",
            "delete_all_projects",
            "manage_project_costs",
            # Tasks
            "view_all_tasks",
            "create_tasks",
            "edit_all_tasks",
            "assign_tasks",
            # Clients
            "view_clients",
            "view_all_clients",
            "create_clients",
            "edit_clients",
            "edit_all_clients",
            "delete_all_clients",
            "manage_client_notes",
            # Invoices
            "view_all_invoices",
            "create_invoices",
            "edit_invoices",
            "delete_invoices",
            "send_invoices",
            "manage_payments",
            "manage_payment_gateways",
            # Reports
            "view_all_reports",
            "export_reports",
            "create_saved_reports",
            # Users
            "view_users",
            "create_users",
            "edit_users",
            "delete_users",
            "manage_user_roles",
            # Issues
            "view_all_issues",
            "view_own_issues",
            "create_issues",
            "edit_all_issues",
            "edit_own_issues",
            "delete_issues",
            # Inventory
            "view_inventory",
            "manage_stock_items",
            "manage_warehouses",
            "view_stock_levels",
            "manage_stock_movements",
            "transfer_stock",
            "view_stock_history",
            "manage_stock_reservations",
            "view_inventory_reports",
            "approve_stock_adjustments",
            "manage_suppliers",
            "manage_purchase_orders",
        ],
    },
    "user": {
        "description": N_("Standard User"),
        "is_system_role": True,
        "permissions": [
            # Time entries
            "view_own_time_entries",
            "create_time_entries",
            "edit_own_time_entries",
            "delete_own_time_entries",
            # Projects
            "view_own_projects",
            # Tasks
            "view_own_tasks",
            "create_tasks",
            "edit_own_tasks",
            "delete_own_tasks",
            # Clients
            "view_own_clients",
            # Invoices
            "view_own_invoices",
            # Reports
            "view_own_reports",
            "export_reports",
            # Inventory
            "view_inventory",
            "view_stock_levels",
        ],
    },
    "viewer": {
        "description": N_("Read-only User"),
        "is_system_role": True,
        "permissions": [
            "view_own_time_entries",
            "view_own_projects",
            "view_own_tasks",
            "view_own_clients",
            "view_own_invoices",
            "view_own_reports",
            # Inventory
            "view_inventory",
            "view_stock_levels",
        ],
    },
    "subcontractor": {
        "description": N_("User restricted to assigned clients and their projects"),
        "is_system_role": True,
        "permissions": [
            "view_own_time_entries",
            "create_time_entries",
            "edit_own_time_entries",
            "delete_own_time_entries",
            "view_own_projects",
            "view_own_tasks",
            "create_tasks",
            "edit_own_tasks",
            "delete_own_tasks",
            "view_own_clients",
            "view_own_invoices",
            "view_own_reports",
            "export_reports",
            "view_inventory",
            "view_stock_levels",
        ],
    },
}


def seed_permissions():
    """Seed default permissions into the database"""
    print("Seeding permissions...")
    created_count = 0
    existing_count = 0

    for perm_data in DEFAULT_PERMISSIONS:
        # Check if permission already exists
        existing = Permission.query.filter_by(name=perm_data["name"]).first()
        if existing:
            existing_count += 1
            # Update description if it changed
            if existing.description != perm_data["description"]:
                existing.description = perm_data["description"]
                existing.category = perm_data["category"]
            continue

        # Create new permission
        permission = Permission(
            name=perm_data["name"], description=perm_data["description"], category=perm_data["category"]
        )
        db.session.add(permission)
        created_count += 1

    try:
        db.session.commit()
        print(f"Permissions seeded: {created_count} created, {existing_count} already existed")
        return True
    except IntegrityError as e:
        db.session.rollback()
        print(f"Error seeding permissions: {e}")
        return False


def seed_roles(silent=False):
    """Seed default roles with their permissions"""
    if not silent:
        print("Seeding roles...")
    created_count = 0
    existing_count = 0
    updated_count = 0

    for role_name, role_data in DEFAULT_ROLES.items():
        # Check if role already exists
        existing = Role.query.filter_by(name=role_name).first()

        if existing:
            existing_count += 1
            # Update description if it changed
            if existing.description != role_data["description"]:
                existing.description = role_data["description"]
            role = existing
        else:
            # Create new role
            role = Role(
                name=role_name, description=role_data["description"], is_system_role=role_data["is_system_role"]
            )
            db.session.add(role)
            created_count += 1

        # Assign permissions to role
        for perm_name in role_data["permissions"]:
            permission = Permission.query.filter_by(name=perm_name).first()
            if permission and not role.has_permission(perm_name):
                role.add_permission(permission)
                updated_count += 1

    try:
        db.session.commit()
        if not silent and updated_count > 0:
            print(
                f"Roles seeded: {created_count} created, {existing_count} already existed, {updated_count} permissions added"
            )
        elif not silent:
            print(f"Roles seeded: {created_count} created, {existing_count} already existed")
        return True
    except IntegrityError as e:
        db.session.rollback()
        if not silent:
            print(f"Error seeding roles: {e}")
        return False


def sync_permissions_and_roles():
    """Synchronize permissions and roles - ensures all permissions exist and roles have correct permissions"""
    try:
        # First ensure all permissions exist
        seed_permissions()
        # Then ensure all roles have correct permissions
        seed_roles(silent=True)
        return True
    except Exception as e:
        print(f"Error syncing permissions and roles: {e}")
        return False


def migrate_legacy_users():
    """Migrate users with legacy 'role' field to new role system"""
    print("Migrating legacy users to new role system...")
    migrated_count = 0

    # Get all users
    users = User.query.all()

    for user in users:
        # Skip if user already has roles assigned
        if len(user.roles) > 0:
            continue

        # Map legacy role to new role system
        if user.role == "admin":
            admin_role = Role.query.filter_by(name="admin").first()
            if admin_role:
                user.add_role(admin_role)
                migrated_count += 1
        else:  # user.role == 'user' or any other value
            user_role = Role.query.filter_by(name="user").first()
            if user_role:
                user.add_role(user_role)
                migrated_count += 1

    try:
        db.session.commit()
        print(f"Migrated {migrated_count} users to new role system")
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error migrating users: {e}")
        return False


def seed_all():
    """Seed all permissions, roles, and migrate users"""
    print("Starting permission system seeding...")

    if not seed_permissions():
        return False

    if not seed_roles():
        return False

    if not migrate_legacy_users():
        return False

    print("Permission system seeding completed successfully!")
    return True
