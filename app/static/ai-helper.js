(function () {
  function csrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute("content") || "" : "";
  }

  function el(id) {
    return document.getElementById(id);
  }

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function addMessage(role, text) {
    const root = el("aiHelperMessages");
    if (!root) return;
    const wrap = document.createElement("div");
    const isUser = role === "user";
    wrap.className = isUser ? "flex justify-end" : "flex justify-start";
    wrap.innerHTML = '<div class="max-w-[85%] rounded-xl px-3 py-2 text-sm whitespace-pre-wrap ' +
      (isUser ? "bg-primary text-white" : "bg-background-light dark:bg-background-dark text-text-light dark:text-text-dark") +
      '">' + escapeHtml(text) + "</div>";
    root.appendChild(wrap);
    root.scrollTop = root.scrollHeight;
  }

  function setStatus(text, isError) {
    const status = el("aiHelperStatus");
    if (!status) return;
    status.textContent = text || "";
    status.className = isError
      ? "text-xs text-red-600 dark:text-red-400"
      : "text-xs text-text-muted-light dark:text-text-muted-dark";
  }

  async function postJson(url, body) {
    const response = await fetch(url, {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken() },
      body: JSON.stringify(body || {}),
    });
    const data = await response.json().catch(function () { return {}; });
    if (!response.ok || data.ok === false || data.success === false) {
      throw new Error(data.error || data.message || gettext("Request failed"));
    }
    return data;
  }

  async function loadContextPreview() {
    const contextEl = el("aiHelperContext");
    const providerEl = el("aiHelperProvider");
    if (!contextEl) return;
    try {
      const response = await fetch("/api/ai/context-preview", { credentials: "same-origin" });
      const data = await response.json().catch(function () { return {}; });
      if (!response.ok || data.ok === false) {
        contextEl.textContent = data.error || gettext("AI helper is not configured.");
        return;
      }
      contextEl.textContent = JSON.stringify(data.context || {}, null, 2);
      if (providerEl && data.provider) {
        providerEl.textContent = gettext("Provider: %(provider)s · Model: %(model)s", {provider: data.provider.provider, model: data.provider.model});
      }
    } catch (err) {
      contextEl.textContent = gettext("Could not load AI context preview.");
    }
  }

  function renderActions(actions) {
    const root = el("aiHelperActions");
    if (!root) return;
    root.innerHTML = "";
    if (!actions || !actions.length) {
      root.classList.add("hidden");
      return;
    }
    root.classList.remove("hidden");
    const heading = document.createElement("p");
    heading.className = "text-sm font-semibold text-text-light dark:text-text-dark";
    heading.textContent = gettext("Suggested actions");
    root.appendChild(heading);
    actions.forEach(function (action) {
      const row = document.createElement("div");
      row.className = "rounded-lg border border-border-light dark:border-border-dark p-3 flex items-start justify-between gap-3";
      const label = action.label || action.type || gettext("Action");
      row.innerHTML = '<div class="min-w-0"><p class="text-sm font-medium">' + escapeHtml(label) +
        '</p><pre class="mt-1 text-xs text-text-muted-light dark:text-text-muted-dark whitespace-pre-wrap overflow-auto max-h-28">' +
        escapeHtml(JSON.stringify(action.payload || {}, null, 2)) + "</pre></div>";
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "shrink-0 px-3 py-1.5 rounded-lg bg-primary text-white text-sm";
      btn.textContent = gettext("Confirm");
      btn.addEventListener("click", async function () {
        btn.disabled = true;
        try {
          const result = await postJson("/api/ai/actions/confirm", { action: action });
          addMessage("assistant", gettext("Action completed: %(action)s", {action: result.type || action.type}));
          root.classList.add("hidden");
          root.innerHTML = "";
        } catch (err) {
          setStatus(err.message, true);
        } finally {
          btn.disabled = false;
        }
      });
      row.appendChild(btn);
      root.appendChild(row);
    });
  }

  function openDrawer() {
    el("aiHelperBackdrop")?.classList.remove("hidden");
    el("aiHelperDrawer")?.classList.remove("hidden");
    loadContextPreview();
    setTimeout(function () { el("aiHelperPrompt")?.focus(); }, 50);
  }

  function closeDrawer() {
    el("aiHelperBackdrop")?.classList.add("hidden");
    el("aiHelperDrawer")?.classList.add("hidden");
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-ai-helper-open]").forEach(function (button) {
      button.addEventListener("click", openDrawer);
    });
    document.querySelectorAll("[data-ai-helper-close]").forEach(function (button) {
      button.addEventListener("click", closeDrawer);
    });

    const form = el("aiHelperForm");
    const prompt = el("aiHelperPrompt");
    if (!form || !prompt) return;
    form.addEventListener("submit", async function (event) {
      event.preventDefault();
      const text = (prompt.value || "").trim();
      if (!text) return;
      prompt.value = "";
      addMessage("user", text);
      setStatus(gettext("Thinking..."));
      try {
        const data = await postJson("/api/ai/chat", { prompt: text });
        addMessage("assistant", data.reply || gettext("No response."));
        renderActions(data.actions || []);
        setStatus("");
      } catch (err) {
        addMessage("assistant", err.message || gettext("AI helper failed."));
        setStatus(err.message || gettext("AI helper failed."), true);
      }
    });
  });
})();
