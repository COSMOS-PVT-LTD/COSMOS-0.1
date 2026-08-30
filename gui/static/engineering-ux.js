/**
 * COSMOS 0.1 — P4 Engineering UX
 * Command search, project context, properties panel, job manager,
 * notifications, recent items, keyboard shortcuts.
 */
(function engineeringUX() {
  const STORAGE = {
    project: "cosmos_project_context",
    recentWorkbenches: "cosmos_recent_workbenches",
    recentFiles: "cosmos_recent_files",
    notifications: "cosmos_notifications",
  };

  const MAX_RECENT_WB = 8;
  const MAX_RECENT_FILES = 10;
  const MAX_NOTIFICATIONS = 40;

  let commandOpen = false;
  let jobsPollTimer = null;
  let selectedCommand = 0;
  let filteredCommands = [];

  function $(id) {
    return document.getElementById(id);
  }

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function readJson(key, fallback) {
    try {
      const raw = localStorage.getItem(key);
      return raw ? JSON.parse(raw) : fallback;
    } catch {
      return fallback;
    }
  }

  function writeJson(key, value) {
    localStorage.setItem(key, JSON.stringify(value));
  }

  COSMOS.getProjectContext = function getProjectContext() {
    return readJson(STORAGE.project, {
      name: "Default Project",
      system: "",
      component: "",
    });
  };

  COSMOS.setProjectContext = function setProjectContext(context) {
    const merged = { ...COSMOS.getProjectContext(), ...context };
    writeJson(STORAGE.project, merged);
    COSMOS.renderProjectContext();
    COSMOS.notify("Project context updated", "info", merged.name);
  };

  COSMOS.trackRecentWorkbench = function trackRecentWorkbench(item) {
    if (!item?.workbench_id) return;
    const list = readJson(STORAGE.recentWorkbenches, []);
    const entry = {
      workbench_id: item.workbench_id,
      title: item.title,
      route: item.route,
      visited_at: Date.now(),
    };
    const next = [entry, ...list.filter((row) => row.workbench_id !== item.workbench_id)].slice(0, MAX_RECENT_WB);
    writeJson(STORAGE.recentWorkbenches, next);
  };

  COSMOS.trackRecentFile = function trackRecentFile(filename, meta = {}) {
    if (!filename) return;
    const list = readJson(STORAGE.recentFiles, []);
    const entry = {
      filename,
      source_id: meta.source_id || "",
      visited_at: Date.now(),
    };
    const next = [entry, ...list.filter((row) => row.filename !== filename)].slice(0, MAX_RECENT_FILES);
    writeJson(STORAGE.recentFiles, next);
  };

  COSMOS.getRecentWorkbenches = function getRecentWorkbenches() {
    return readJson(STORAGE.recentWorkbenches, []);
  };

  COSMOS.getRecentFiles = function getRecentFiles() {
    return readJson(STORAGE.recentFiles, []);
  };

  COSMOS.notify = function notify(message, level = "info", detail = "") {
    const item = {
      id: `n-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      message,
      level,
      detail,
      timestamp: new Date().toISOString(),
      read: false,
    };
    const list = readJson(STORAGE.notifications, []);
    list.unshift(item);
    writeJson(STORAGE.notifications, list.slice(0, MAX_NOTIFICATIONS));
    COSMOS.renderNotifications();
    COSMOS.showToast(message, level);
    COSMOS.updateNotificationBadge();
  };

  COSMOS.markNotificationsRead = function markNotificationsRead() {
    const list = readJson(STORAGE.notifications, []);
    list.forEach((item) => { item.read = true; });
    writeJson(STORAGE.notifications, list);
    COSMOS.updateNotificationBadge();
    COSMOS.renderNotifications();
  };

  COSMOS.showToast = function showToast(message, level = "info") {
    const root = $("cosmos-toast-root");
    if (!root) return;
    const toast = document.createElement("div");
    toast.className = `cosmos-toast ${level}`;
    toast.textContent = message;
    root.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add("visible"));
    setTimeout(() => {
      toast.classList.remove("visible");
      setTimeout(() => toast.remove(), 240);
    }, 3600);
  };

  COSMOS.renderProjectContext = function renderProjectContext() {
    const ctx = COSMOS.getProjectContext();
    const pill = $("cosmos-project-pill");
    if (pill) {
      const parts = [ctx.name];
      if (ctx.system) parts.push(ctx.system);
      if (ctx.component) parts.push(ctx.component);
      pill.textContent = parts.join(" · ");
      pill.title = "Project context — click to edit (Ctrl+Shift+P)";
    }
    const zoneProject = document.querySelector("#zone-project .zone-value");
    if (zoneProject) zoneProject.textContent = ctx.name || "Default Project";
    const meta = document.querySelector(".status-bar-meta");
    if (meta && ctx.name) {
      meta.textContent = `COSMOS 0.1 · ${ctx.name}`;
    }
  };

  COSMOS.defaultPropertyActions = function defaultPropertyActions() {
    return [
      { id: "trace", label: "Trace", ai: false },
      { id: "explain", label: "Explain", ai: true },
      { id: "compare", label: "Compare", ai: false },
      { id: "find-evidence", label: "Find Evidence", ai: true },
      { id: "propose-run", label: "Propose Next Run", ai: true },
    ];
  };

  COSMOS.sessionPropertySections = function sessionPropertySections() {
    const ctx = COSMOS.getProjectContext();
    const user = COSMOS.currentUser || {};
    return [
      {
        name: "Session",
        entries: {
          User: user.login_id || "—",
          Role: user.role || "—",
          Team: user.team || "—",
          Project: ctx.name,
          System: ctx.system || "—",
          Component: ctx.component || "—",
          Route: window.location.pathname,
        },
      },
      {
        name: "Engineering Context",
        entries: {
          Infrastructure: localStorage.getItem("cosmos_infrastructure") || "—",
          Profile: localStorage.getItem("cosmos_login_profile") || user.role || "—",
          Workspace: window.location.pathname.includes("/workbench/") ? "Workbench" : "Command",
        },
        actions: COSMOS.defaultPropertyActions(),
      },
    ];
  };

  COSMOS.mountEngineeringConsole = function mountEngineeringConsole() {
    if ($("engineering-console")) return;
    const frame = document.querySelector(".app-frame");
    if (!frame) return;
    const consoleNode = document.createElement("div");
    consoleNode.className = "engineering-console";
    consoleNode.id = "engineering-console";
    consoleNode.setAttribute("role", "region");
    consoleNode.setAttribute("aria-label", "Engineering console");
    consoleNode.innerHTML = `
      <div class="console-strip">
        <button type="button" class="console-seg" data-console="jobs" id="console-jobs-btn">
          Jobs <span class="console-count" id="console-jobs-count">0</span>
        </button>
        <button type="button" class="console-seg" data-console="solver" id="console-solver-btn">
          Solver <span class="console-val idle" id="console-solver-id">IDLE</span>
        </button>
        <button type="button" class="console-seg" data-console="convergence" id="console-convergence-btn">
          Convergence <span class="console-val idle" id="console-convergence">—</span>
        </button>
        <button type="button" class="console-seg" data-console="log" id="console-log-btn">Log</button>
        <button type="button" class="console-seg" data-console="events" id="console-events-btn">Events</button>
      </div>
      <div class="console-expand" id="console-expand-panel" hidden>
        <pre id="console-expand-body">Engineering console ready.</pre>
        <div class="console-progress" id="console-progress-wrap" hidden>
          <div class="console-progress-fill" id="console-progress-fill" style="width:0%"></div>
        </div>
      </div>`;
    frame.appendChild(consoleNode);

    const togglePanel = (panel, bodyText) => {
      const expand = $("console-expand-panel");
      const body = $("console-expand-body");
      if (!expand || !body) return;
      const isOpen = !expand.hidden && expand.dataset.panel === panel;
      document.querySelectorAll(".console-seg").forEach((seg) => seg.classList.toggle("active", seg.dataset.console === panel && !isOpen));
      if (isOpen) {
        expand.hidden = true;
        expand.dataset.panel = "";
        return;
      }
      expand.hidden = false;
      expand.dataset.panel = panel;
      body.textContent = bodyText;
      document.querySelectorAll(".console-seg").forEach((seg) => seg.classList.toggle("active", seg.dataset.console === panel));
    };

    $("console-jobs-btn")?.addEventListener("click", () => {
      COSMOS.toggleJobManager(true);
      togglePanel("jobs", COSMOS.formatConsoleJobs());
    });
    $("console-solver-btn")?.addEventListener("click", () => togglePanel("solver", COSMOS.formatConsoleSolver()));
    $("console-convergence-btn")?.addEventListener("click", () => togglePanel("convergence", COSMOS.formatConsoleConvergence()));
    $("console-log-btn")?.addEventListener("click", () => togglePanel("log", COSMOS.formatConsoleLog()));
    $("console-events-btn")?.addEventListener("click", () => togglePanel("events", COSMOS.formatConsoleEvents()));
  };

  COSMOS.formatConsoleJobs = function formatConsoleJobs() {
    const jobs = COSMOS.jobs || [];
    if (!jobs.length) return "No background jobs registered.";
    return jobs.slice(0, 12).map((job) => {
      const status = String(job.status || "UNKNOWN").toUpperCase();
      return `${job.source_id || "—"} · ${status} · ${job.job_type || "ingest"} · ${job.created_at || "—"}`;
    }).join("\n");
  };

  COSMOS.formatConsoleSolver = function formatConsoleSolver() {
    const active = (COSMOS.jobs || []).find((job) => {
      const status = String(job.status || "").toUpperCase();
      return status.includes("RUN") || status.includes("PROCESS");
    });
    if (!active) return "SOLVER STATUS: IDLE\nNo active computational solver job.";
    return [
      `JOB ID: ${active.job_id || active.source_id || "—"}`,
      `SOLVER: ${active.job_type || "knowledge-ingest"}`,
      `STATUS: ${String(active.status || "RUNNING").toUpperCase()}`,
      `START: ${active.created_at || "—"}`,
      "NOTE: Full solver telemetry requires backend solver API (MISSING DEPENDENCY).",
    ].join("\n");
  };

  COSMOS.formatConsoleConvergence = function formatConsoleConvergence() {
    const active = (COSMOS.jobs || []).find((job) => {
      const status = String(job.status || "").toUpperCase();
      return status.includes("RUN") || status.includes("PROCESS");
    });
    if (!active) return "CONVERGENCE: —\nNo running solver to report convergence.";
    return "CONVERGENCE: processing\nBackground knowledge job in progress.\nFull residual/convergence metrics require solver telemetry API.";
  };

  COSMOS.formatConsoleLog = function formatConsoleLog() {
    const user = COSMOS.currentUser?.login_id || "system";
    const ctx = COSMOS.getProjectContext();
    return [
      `[${new Date().toISOString()}] SESSION ${user}`,
      `[${new Date().toISOString()}] PROJECT ${ctx.name}`,
      `[${new Date().toISOString()}] ROUTE ${window.location.pathname}`,
      `[${new Date().toISOString()}] COSMOS engineering shell ready`,
    ].join("\n");
  };

  COSMOS.formatConsoleEvents = function formatConsoleEvents() {
    const notes = readJson(STORAGE.notifications, []).slice(0, 8);
    if (!notes.length) return "No recent system events.";
    return notes.map((item) => `${item.timestamp} · ${item.level?.toUpperCase() || "INFO"} · ${item.message}`).join("\n");
  };

  COSMOS.updateEngineeringConsole = function updateEngineeringConsole(jobs) {
    const active = (jobs || []).filter((job) => {
      const status = String(job.status || "").toUpperCase();
      return status.includes("RUN") || status.includes("PROCESS") || status.includes("PEND");
    }).length;
    const jobsCount = $("console-jobs-count");
    if (jobsCount) jobsCount.textContent = String(active);
    const solverEl = $("console-solver-id");
    const zoneSolver = $("zone-solver-value");
    const running = (jobs || []).find((job) => {
      const status = String(job.status || "").toUpperCase();
      return status.includes("RUN") || status.includes("PROCESS");
    });
    const solverLabel = running ? String(running.job_id || running.source_id || "RUN").slice(0, 12) : "IDLE";
    if (solverEl) {
      solverEl.textContent = solverLabel;
      solverEl.className = `console-val ${running ? "running" : "idle"}`;
    }
    if (zoneSolver) zoneSolver.textContent = solverLabel;
    const convergence = $("console-convergence");
    if (convergence) {
      convergence.textContent = running ? "PROC" : "—";
      convergence.className = `console-val ${running ? "running" : "idle"}`;
    }
    const progressWrap = $("console-progress-wrap");
    const progressFill = $("console-progress-fill");
    if (progressWrap && progressFill) {
      if (running) {
        progressWrap.hidden = false;
        progressFill.style.width = "42%";
      } else {
        progressWrap.hidden = true;
        progressFill.style.width = "0%";
      }
    }
    if ($("console-expand-panel")?.dataset.panel === "jobs" && !$("console-expand-panel").hidden) {
      $("console-expand-body").textContent = COSMOS.formatConsoleJobs();
    }
  };

  COSMOS.openProjectModal = function openProjectModal() {
    const ctx = COSMOS.getProjectContext();
    $("cosmos-project-name").value = ctx.name || "";
    $("cosmos-project-system").value = ctx.system || "";
    $("cosmos-project-component").value = ctx.component || "";
    $("cosmos-project-modal")?.classList.add("open");
    $("cosmos-project-name")?.focus();
  };

  COSMOS.closeProjectModal = function closeProjectModal() {
    $("cosmos-project-modal")?.classList.remove("open");
  };

  COSMOS.saveProjectModal = function saveProjectModal() {
    COSMOS.setProjectContext({
      name: $("cosmos-project-name")?.value?.trim() || "Default Project",
      system: $("cosmos-project-system")?.value?.trim() || "",
      component: $("cosmos-project-component")?.value?.trim() || "",
    });
    COSMOS.closeProjectModal();
  };

  COSMOS.showProperties = function showProperties(title, properties = {}, options = {}) {
    const panel = $("cosmos-properties-panel");
    const body = $("cosmos-properties-body");
    if (!panel || !body) return;
    $("cosmos-properties-title").textContent = title || "Properties";
    const sections = options.sections || [{ name: "Identity", entries: properties }];
    const actions = options.actions || [];
    body.innerHTML = sections
      .map((section) => {
        const entries = section.entries || {};
        const rows = Object.entries(entries)
          .map(([key, value]) => `<dt>${escapeHtml(key)}</dt><dd>${escapeHtml(String(value ?? "—"))}</dd>`)
          .join("");
        const actionHtml = section.actions?.length
          ? `<div class="cosmos-prop-actions">${section.actions
            .map((action) => `<button type="button" class="cosmos-prop-action${action.ai ? " ai-action" : ""}" data-action="${escapeHtml(action.id)}">${escapeHtml(action.label)}</button>`)
            .join("")}</div>`
          : "";
        return `<div class="cosmos-prop-section"><div class="cosmos-prop-section-head">${escapeHtml(section.name)}</div><dl>${rows}</dl>${actionHtml}</div>`;
      })
      .join("");
    if (actions.length) {
      body.innerHTML += `<div class="cosmos-prop-actions">${actions
        .map((action) => `<button type="button" class="cosmos-prop-action${action.ai ? " ai-action" : ""}" data-action="${escapeHtml(action.id)}">${escapeHtml(action.label)}</button>`)
        .join("")}</div>`;
    }
    body.querySelectorAll("[data-action]").forEach((button) => {
      button.addEventListener("click", () => {
        document.dispatchEvent(new CustomEvent("cosmos:property-action", {
          detail: { action: button.dataset.action, title, properties },
        }));
      });
    });
    panel.classList.add("open");
    panel.setAttribute("aria-hidden", "false");
  };

  COSMOS.hideProperties = function hideProperties() {
    const panel = $("cosmos-properties-panel");
    panel?.classList.remove("open");
    panel?.setAttribute("aria-hidden", "true");
  };

  COSMOS.toggleJobManager = function toggleJobManager(force) {
    const panel = $("cosmos-job-manager");
    if (!panel) return;
    const open = force !== undefined ? force : !panel.classList.contains("open");
    panel.classList.toggle("open", open);
    panel.setAttribute("aria-hidden", open ? "false" : "true");
    if (open) COSMOS.refreshJobs();
  };

  COSMOS.toggleNotifications = function toggleNotifications(force) {
    const panel = $("cosmos-notifications-panel");
    if (!panel) return;
    const open = force !== undefined ? force : !panel.classList.contains("open");
    panel.classList.toggle("open", open);
    if (open) COSMOS.markNotificationsRead();
  };

  COSMOS.toggleShortcuts = function toggleShortcuts(force) {
    const modal = $("cosmos-shortcuts-modal");
    if (!modal) return;
    const open = force !== undefined ? force : !modal.classList.contains("open");
    modal.classList.toggle("open", open);
  };

  COSMOS.closeAllOverlays = function closeAllOverlays() {
    COSMOS.closeCommandPalette();
    COSMOS.closeProjectModal();
    COSMOS.hideProperties();
    COSMOS.toggleJobManager(false);
    COSMOS.toggleNotifications(false);
    COSMOS.toggleShortcuts(false);
  };

  COSMOS.buildCommands = function buildCommands() {
    const user = COSMOS.currentUser;
    const commands = [
      { id: "nav-command", label: "Go to Command Workspace", group: "Navigation", keywords: "home launcher workbenches", run: () => { window.location.href = COSMOS.hubUrl(COSMOS.hubPageFromUrl()); } },
      { id: "nav-knowledge", label: "Open Maharshi Bharadwaj", group: "Navigation", keywords: "maharshi bharadwaj knowledge evidence graph chat", run: () => { window.location.href = "/app/workbench/knowledge"; } },
      { id: "trace-feature", label: "Trace Selected Feature", group: "Traceability", keywords: "lineage provenance evidence", run: () => COSMOS.notify("Select a feature to trace — requires active workbench selection", "info") },
      { id: "open-lineage", label: "Open Design Lineage", group: "Traceability", keywords: "revision compare branch", run: () => COSMOS.notify("Design lineage workspace not yet available", "warning") },
      { id: "run-validation", label: "Run Validation", group: "V&V", keywords: "verify validate vv", run: () => COSMOS.notify("V&V workspace not yet available", "warning") },
      { id: "project-context", label: "Edit Project Context", group: "Project", keywords: "system component workspace", run: () => COSMOS.openProjectModal() },
      { id: "job-manager", label: "Open Job Manager", group: "Tasks", keywords: "background processing ingest ocr", run: () => COSMOS.toggleJobManager(true) },
      { id: "notifications", label: "Open Notifications", group: "System", keywords: "alerts warnings", run: () => COSMOS.toggleNotifications(true) },
      { id: "shortcuts", label: "Keyboard Shortcuts", group: "Help", keywords: "keys hotkeys", run: () => COSMOS.toggleShortcuts(true) },
      { id: "profile", label: "Edit Profile", group: "Account", keywords: "photo name team", run: () => COSMOS.openProfileModal?.(user, "display_name") },
      { id: "logout", label: "Sign Out", group: "Account", keywords: "exit log out", run: async () => { await fetch("/api/auth/logout", { method: "POST" }); window.location.href = "/"; } },
    ];

    if (COSMOS.canAudit?.(user)) {
      commands.splice(2, 0, {
        id: "nav-audit",
        label: "Open Audit Trail",
        group: "Navigation",
        keywords: "compliance traceability log",
        run: () => { window.location.href = "/app/audit"; },
      });
    }
    if (COSMOS.canAdmin?.(user)) {
      commands.splice(2, 0, {
        id: "nav-admin",
        label: "Open User Administration",
        group: "Navigation",
        keywords: "register credentials users",
        run: () => { window.location.href = "/app/admin"; },
      });
    }

    if (window.location.pathname.includes("/workbench/knowledge")) {
      commands.push(
        { id: "knowledge-refresh", label: "Refresh Knowledge Workspace", group: "Knowledge", keywords: "reload sources graph", run: () => window.Maharshi?.refreshAll?.().catch(() => {}) },
        { id: "knowledge-backup", label: "Backup Knowledge Vault", group: "Knowledge", keywords: "archive export", run: () => $("mh-backup-btn")?.click() },
      );
    }

    COSMOS.getRecentWorkbenches().forEach((item) => {
      commands.push({
        id: `recent-wb-${item.workbench_id}`,
        label: `Recent Workbench: ${item.title}`,
        group: "Recent",
        keywords: item.workbench_id,
        run: () => { window.location.href = item.route; },
      });
    });

    COSMOS.getRecentFiles().forEach((item) => {
      commands.push({
        id: `recent-file-${item.filename}`,
        label: `Recent File: ${item.filename}`,
        group: "Recent",
        keywords: "document source upload",
        run: () => {
          if (window.location.pathname.includes("/workbench/knowledge") && item.source_id) {
            window.Maharshi?.openSourceViewer?.(item.source_id);
          } else {
            window.location.href = "/app/workbench/knowledge";
          }
        },
      });
    });

    if (COSMOS.workbenchCatalog?.pages) {
      COSMOS.workbenchCatalog.pages.flatMap((page) => page.items).forEach((item) => {
        commands.push({
          id: `wb-${item.workbench_id}`,
          label: `Workbench: ${item.title}`,
          group: "Workbenches",
          keywords: `${item.description} ${item.status}`,
          run: () => {
            COSMOS.trackRecentWorkbench(item);
            window.location.href = COSMOS.workbenchUrl(item.route, item.page);
          },
        });
      });
    }

    return commands;
  };

  COSMOS.openCommandPalette = function openCommandPalette() {
    const modal = $("cosmos-command-palette");
    const input = $("cosmos-command-input");
    if (!modal || !input) return;
    commandOpen = true;
    modal.classList.add("open");
    input.value = "";
    COSMOS.filterCommands("");
    input.focus();
  };

  COSMOS.closeCommandPalette = function closeCommandPalette() {
    commandOpen = false;
    $("cosmos-command-palette")?.classList.remove("open");
  };

  COSMOS.filterCommands = function filterCommands(query) {
    const q = query.trim().toLowerCase();
    const commands = COSMOS.buildCommands();
    filteredCommands = commands.filter((cmd) => {
      if (!q) return true;
      const haystack = `${cmd.label} ${cmd.group} ${cmd.keywords || ""}`.toLowerCase();
      return haystack.includes(q);
    });
    selectedCommand = 0;
    COSMOS.renderCommandResults();
  };

  COSMOS.renderCommandResults = function renderCommandResults() {
    const list = $("cosmos-command-results");
    if (!list) return;
    if (!filteredCommands.length) {
      list.innerHTML = `<div class="cosmos-command-empty">No matching commands</div>`;
      return;
    }
    let lastGroup = "";
    list.innerHTML = filteredCommands
      .map((cmd, index) => {
        let groupHtml = "";
        if (cmd.group !== lastGroup) {
          lastGroup = cmd.group;
          groupHtml = `<div class="cosmos-command-group">${escapeHtml(cmd.group)}</div>`;
        }
        return `${groupHtml}<button type="button" class="cosmos-command-item${index === selectedCommand ? " active" : ""}" data-index="${index}"><span>${escapeHtml(cmd.label)}</span><kbd>↵</kbd></button>`;
      })
      .join("");
    list.querySelectorAll(".cosmos-command-item").forEach((button) => {
      button.addEventListener("click", () => {
        const index = parseInt(button.dataset.index || "0", 10);
        COSMOS.runCommand(index);
      });
    });
  };

  COSMOS.runCommand = function runCommand(index) {
    const cmd = filteredCommands[index];
    if (!cmd) return;
    COSMOS.closeCommandPalette();
    cmd.run();
  };

  COSMOS.refreshJobs = async function refreshJobs() {
    const body = $("cosmos-job-body");
    if (!body) return;
    body.innerHTML = `<tr><td colspan="5">Loading jobs…</td></tr>`;
    try {
      const response = await fetch("/api/jobs");
      if (!response.ok) throw new Error("Could not load jobs");
      const payload = await response.json();
      COSMOS.jobs = payload.jobs || [];
      COSMOS.renderJobManager(COSMOS.jobs);
      COSMOS.updateJobBadge(COSMOS.jobs);
    } catch (error) {
      body.innerHTML = `<tr><td colspan="5">${escapeHtml(error.message || "Job API unavailable")}</td></tr>`;
    }
  };

  COSMOS.renderJobManager = function renderJobManager(jobs) {
    const body = $("cosmos-job-body");
    if (!body) return;
    if (!jobs.length) {
      body.innerHTML = `<tr><td colspan="5">No background jobs</td></tr>`;
      return;
    }
    body.innerHTML = jobs
      .slice()
      .sort((a, b) => String(b.created_at || "").localeCompare(String(a.created_at || "")))
      .slice(0, 50)
      .map((job) => {
        const status = String(job.status || "UNKNOWN").toUpperCase();
        const badge = status.includes("FAIL") ? "error" : status.includes("RUN") || status.includes("PROCESS") ? "warning" : status.includes("AVAIL") ? "success" : "info";
        return `<tr>
          <td>${escapeHtml(job.source_id || "—")}</td>
          <td><span class="cosmos-badge ${badge}">${escapeHtml(status)}</span></td>
          <td>${escapeHtml(job.job_type || "ingest")}</td>
          <td>${escapeHtml(job.created_at || "—")}</td>
          <td>${escapeHtml(job.error_message || "—")}</td>
        </tr>`;
      })
      .join("");
  };

  COSMOS.updateJobManager = function updateJobManager(jobs) {
    COSMOS.jobs = jobs || [];
    if ($("cosmos-job-manager")?.classList.contains("open")) {
      COSMOS.renderJobManager(COSMOS.jobs);
    }
    COSMOS.updateJobBadge(COSMOS.jobs);
    COSMOS.updateEngineeringConsole?.(COSMOS.jobs);
  };

  COSMOS.updateJobBadge = function updateJobBadge(jobs) {
    const active = (jobs || []).filter((job) => {
      const status = String(job.status || "").toUpperCase();
      return status.includes("RUN") || status.includes("PROCESS") || status.includes("PEND");
    }).length;
    const failed = (jobs || []).filter((job) => String(job.status || "").toUpperCase().includes("FAIL")).length;
    const badge = $("cosmos-jobs-badge");
    if (badge) {
      const count = active + failed;
      badge.textContent = count ? String(count) : "";
      badge.hidden = !count;
      badge.className = `cosmos-toolbar-badge${failed ? " error" : ""}`;
    }
    const summary = $("cosmos-jobs-summary");
    if (summary) {
      summary.textContent = `${active} active · ${failed} failed · ${(jobs || []).length} total`;
    }
  };

  COSMOS.updateNotificationBadge = function updateNotificationBadge() {
    const unread = readJson(STORAGE.notifications, []).filter((item) => !item.read).length;
    const badge = $("cosmos-notify-badge");
    if (badge) {
      badge.textContent = unread ? String(unread) : "";
      badge.hidden = !unread;
    }
  };

  COSMOS.renderNotifications = function renderNotifications() {
    const list = $("cosmos-notifications-list");
    if (!list) return;
    const items = readJson(STORAGE.notifications, []);
    if (!items.length) {
      list.innerHTML = `<div class="cosmos-empty">No notifications yet</div>`;
      return;
    }
    list.innerHTML = items
      .slice(0, 30)
      .map((item) => `<div class="cosmos-notification-item ${item.level}${item.read ? " read" : ""}"><strong>${escapeHtml(item.message)}</strong>${item.detail ? `<span>${escapeHtml(item.detail)}</span>` : ""}<time>${escapeHtml(item.timestamp)}</time></div>`)
      .join("");
  };

  COSMOS.renderRecentPanel = function renderRecentPanel() {
    const host = $("cosmos-recent-panel");
    if (!host) return;
    const workbenches = COSMOS.getRecentWorkbenches().slice(0, 5);
    const files = COSMOS.getRecentFiles().slice(0, 5);
    host.innerHTML = `
      <div class="cosmos-recent-block">
        <h4>Recent Workbenches</h4>
        ${workbenches.length ? workbenches.map((item) => `<button type="button" class="cosmos-recent-link" data-route="${escapeHtml(item.route)}">${escapeHtml(item.title)}</button>`).join("") : `<span class="cosmos-empty-inline">None yet</span>`}
      </div>
      <div class="cosmos-recent-block">
        <h4>Recent Files</h4>
        ${files.length ? files.map((item) => `<button type="button" class="cosmos-recent-link file" data-file="${escapeHtml(item.filename)}" data-source="${escapeHtml(item.source_id || "")}">${escapeHtml(item.filename)}</button>`).join("") : `<span class="cosmos-empty-inline">None yet</span>`}
      </div>`;
    host.querySelectorAll(".cosmos-recent-link[data-route]").forEach((button) => {
      button.addEventListener("click", () => { window.location.href = button.dataset.route; });
    });
    host.querySelectorAll(".cosmos-recent-link.file").forEach((button) => {
      button.addEventListener("click", () => {
        if (window.location.pathname.includes("/workbench/knowledge") && button.dataset.source) {
          window.Maharshi?.openSourceViewer?.(button.dataset.source);
        } else {
          window.location.href = "/app/workbench/knowledge";
        }
      });
    });
  };

  COSMOS.mountEngineeringChrome = function mountEngineeringChrome() {
    if ($("cosmos-engineering-root")) return;

    const root = document.createElement("div");
    root.id = "cosmos-engineering-root";
    root.innerHTML = `
      <div class="cosmos-toolbar" id="cosmos-toolbar">
        <button type="button" class="cosmos-toolbar-btn" id="cosmos-command-btn" title="Command search (Ctrl+K)" aria-label="Command search">
          <span>⌘K</span> Command
        </button>
        <button type="button" class="cosmos-toolbar-btn" id="cosmos-jobs-btn" title="Job manager (Ctrl+J)" aria-label="Job manager">
          Jobs <span class="cosmos-toolbar-badge" id="cosmos-jobs-badge" hidden></span>
        </button>
        <button type="button" class="cosmos-toolbar-btn" id="cosmos-notify-btn" title="Notifications" aria-label="Notifications">
          Alerts <span class="cosmos-toolbar-badge" id="cosmos-notify-badge" hidden></span>
        </button>
        <button type="button" class="cosmos-toolbar-btn" id="cosmos-props-btn" title="Properties panel (Ctrl+.)" aria-label="Properties panel">Properties</button>
        <button type="button" class="cosmos-project-pill cosmos-toolbar-btn" id="cosmos-project-pill" title="Project context">Default Project</button>
      </div>

      <div class="cosmos-recent-panel-wrap" id="cosmos-recent-panel"></div>

      <div class="cosmos-toast-root" id="cosmos-toast-root" aria-live="polite"></div>

      <div class="cosmos-overlay" id="cosmos-command-palette" aria-hidden="true">
        <div class="cosmos-command-card" role="dialog" aria-modal="true" aria-label="Command search">
          <input type="search" id="cosmos-command-input" placeholder="Search commands, workbenches, files…" autocomplete="off" />
          <div class="cosmos-command-results" id="cosmos-command-results"></div>
          <div class="cosmos-command-foot">↑↓ navigate · Enter run · Esc close</div>
        </div>
      </div>

      <div class="cosmos-overlay profile-modal" id="cosmos-project-modal" aria-hidden="true">
        <div class="profile-panel cosmos-project-panel">
          <div class="profile-panel-header">
            <h2>Project Context</h2>
            <button type="button" class="profile-close" id="cosmos-project-close" aria-label="Close">✕</button>
          </div>
          <p class="profile-hint">Persistent engineering context shown across COSMOS workspaces.</p>
          <label class="field-block">Project Name<input id="cosmos-project-name" /></label>
          <label class="field-block">System<input id="cosmos-project-system" placeholder="e.g. Stage-1 Propulsion" /></label>
          <label class="field-block">Component<input id="cosmos-project-component" placeholder="e.g. Pintle Injector" /></label>
          <button type="button" class="primary profile-save" id="cosmos-project-save">SAVE CONTEXT</button>
        </div>
      </div>

      <aside class="cosmos-side-panel" id="cosmos-properties-panel" aria-hidden="true">
        <div class="cosmos-side-head">
          <h3 id="cosmos-properties-title">Properties</h3>
          <button type="button" class="profile-close" id="cosmos-properties-close" aria-label="Close">✕</button>
        </div>
        <dl class="cosmos-properties-body" id="cosmos-properties-body"></dl>
      </aside>

      <aside class="cosmos-side-panel wide" id="cosmos-job-manager" aria-hidden="true">
        <div class="cosmos-side-head">
          <h3>Job Manager</h3>
          <button type="button" class="profile-close" id="cosmos-jobs-close" aria-label="Close">✕</button>
        </div>
        <p class="cosmos-side-summary" id="cosmos-jobs-summary">Background knowledge jobs</p>
        <div class="cosmos-side-table-wrap">
          <table class="clean-table">
            <thead><tr><th>Source</th><th>Status</th><th>Type</th><th>Created</th><th>Error</th></tr></thead>
            <tbody id="cosmos-job-body"></tbody>
          </table>
        </div>
        <button type="button" class="cosmos-btn secondary" id="cosmos-jobs-refresh">Refresh Jobs</button>
      </aside>

      <aside class="cosmos-side-panel" id="cosmos-notifications-panel" aria-hidden="true">
        <div class="cosmos-side-head">
          <h3>Notifications</h3>
          <button type="button" class="profile-close" id="cosmos-notify-close" aria-label="Close">✕</button>
        </div>
        <div class="cosmos-notifications-list" id="cosmos-notifications-list"></div>
      </aside>

      <div class="cosmos-overlay profile-modal" id="cosmos-shortcuts-modal" aria-hidden="true">
        <div class="profile-panel cosmos-shortcuts-panel">
          <div class="profile-panel-header">
            <h2>Keyboard Shortcuts</h2>
            <button type="button" class="profile-close" id="cosmos-shortcuts-close" aria-label="Close">✕</button>
          </div>
          <dl class="cosmos-shortcuts-list">
            <dt>Ctrl/Cmd + K</dt><dd>Command search</dd>
            <dt>Ctrl/Cmd + J</dt><dd>Job manager</dd>
            <dt>Ctrl/Cmd + Shift + P</dt><dd>Project context</dd>
            <dt>Ctrl/Cmd + .</dt><dd>Properties panel</dd>
            <dt>?</dt><dd>This help dialog</dd>
            <dt>Esc</dt><dd>Close overlays</dd>
            <dt>← / →</dt><dd>Workbench carousel (hub page)</dd>
          </dl>
        </div>
      </div>`;
    document.body.appendChild(root);

    const header = document.querySelector(".app-header");
    const toolbar = $("cosmos-toolbar");
    const badge = $("user-badge");
    if (header && toolbar && badge) {
      header.insertBefore(toolbar, badge);
    } else if (header && toolbar) {
      header.appendChild(toolbar);
    }

    const recentHost = document.getElementById("cosmos-recent-host");
    const recentWrap = document.querySelector(".cosmos-recent-panel-wrap");
    if (recentHost && recentWrap) {
      recentHost.appendChild(recentWrap);
    }

    $("cosmos-command-btn")?.addEventListener("click", () => COSMOS.openCommandPalette());
    $("cosmos-jobs-btn")?.addEventListener("click", () => COSMOS.toggleJobManager());
    $("cosmos-notify-btn")?.addEventListener("click", () => COSMOS.toggleNotifications());
    $("cosmos-props-btn")?.addEventListener("click", () => COSMOS.showProperties("Context", {}, { sections: COSMOS.sessionPropertySections() }));
    $("cosmos-project-pill")?.addEventListener("click", () => COSMOS.openProjectModal());
    $("cosmos-project-close")?.addEventListener("click", () => COSMOS.closeProjectModal());
    $("cosmos-project-save")?.addEventListener("click", () => COSMOS.saveProjectModal());
    $("cosmos-properties-close")?.addEventListener("click", () => COSMOS.hideProperties());
    $("cosmos-jobs-close")?.addEventListener("click", () => COSMOS.toggleJobManager(false));
    $("cosmos-jobs-refresh")?.addEventListener("click", () => COSMOS.refreshJobs());
    $("cosmos-notify-close")?.addEventListener("click", () => COSMOS.toggleNotifications(false));
    $("cosmos-shortcuts-close")?.addEventListener("click", () => COSMOS.toggleShortcuts(false));

    $("cosmos-command-palette")?.addEventListener("click", (event) => {
      if (event.target.id === "cosmos-command-palette") COSMOS.closeCommandPalette();
    });
    $("cosmos-project-modal")?.addEventListener("click", (event) => {
      if (event.target.id === "cosmos-project-modal") COSMOS.closeProjectModal();
    });
    $("cosmos-shortcuts-modal")?.addEventListener("click", (event) => {
      if (event.target.id === "cosmos-shortcuts-modal") COSMOS.toggleShortcuts(false);
    });

    $("cosmos-command-input")?.addEventListener("input", (event) => {
      COSMOS.filterCommands(event.target.value);
    });
    $("cosmos-command-input")?.addEventListener("keydown", (event) => {
      if (event.key === "ArrowDown") {
        event.preventDefault();
        selectedCommand = Math.min(filteredCommands.length - 1, selectedCommand + 1);
        COSMOS.renderCommandResults();
      } else if (event.key === "ArrowUp") {
        event.preventDefault();
        selectedCommand = Math.max(0, selectedCommand - 1);
        COSMOS.renderCommandResults();
      } else if (event.key === "Enter") {
        event.preventDefault();
        COSMOS.runCommand(selectedCommand);
      } else if (event.key === "Escape") {
        COSMOS.closeCommandPalette();
      }
    });

    document.addEventListener("cosmos:properties", (event) => {
      const detail = event.detail || {};
      COSMOS.showProperties(
        detail.title || "Properties",
        detail.properties || {},
        {
          sections: detail.sections || [{ name: detail.section || "Selection", entries: detail.properties || {} }],
          actions: detail.actions || detail.ai ? COSMOS.defaultPropertyActions() : [],
        },
      );
    });

    document.addEventListener("cosmos:property-action", (event) => {
      const { action } = event.detail || {};
      if (action === "explain" || action === "find-evidence" || action === "propose-run") {
        window.location.href = "/app/workbench/knowledge";
        return;
      }
      COSMOS.notify(`Action "${action}" queued — requires workbench selection context`, "info");
    });
  };

  COSMOS.bindGlobalShortcuts = function bindGlobalShortcuts() {
    document.addEventListener("keydown", (event) => {
      const mod = event.metaKey || event.ctrlKey;
      if (mod && event.key.toLowerCase() === "k") {
        event.preventDefault();
        COSMOS.openCommandPalette();
        return;
      }
      if (mod && event.key.toLowerCase() === "j") {
        event.preventDefault();
        COSMOS.toggleJobManager();
        return;
      }
      if (mod && event.shiftKey && event.key.toLowerCase() === "p") {
        event.preventDefault();
        COSMOS.openProjectModal();
        return;
      }
      if (mod && event.key === ".") {
        event.preventDefault();
        COSMOS.showProperties("Context", {}, { sections: COSMOS.sessionPropertySections() });
        return;
      }
      if (event.key === "?" && !event.target.matches("input, textarea")) {
        event.preventDefault();
        COSMOS.toggleShortcuts(true);
        return;
      }
      if (event.key === "Escape") {
        COSMOS.closeAllOverlays();
      }
    });
  };

  COSMOS.startJobPolling = function startJobPolling() {
    if (jobsPollTimer) clearInterval(jobsPollTimer);
    const poll = () => {
      fetch("/api/jobs")
        .then((response) => (response.ok ? response.json() : null))
        .then((payload) => {
          if (payload?.jobs) COSMOS.updateJobManager(payload.jobs);
        })
        .catch(() => {});
    };
    poll();
    jobsPollTimer = setInterval(poll, 12000);
  };

  COSMOS.initEngineeringUX = function initEngineeringUX() {
    COSMOS.mountEngineeringChrome();
    COSMOS.mountEngineeringConsole?.();
    COSMOS.renderProjectContext();
    COSMOS.renderNotifications();
    COSMOS.renderRecentPanel();
    COSMOS.updateNotificationBadge();
    COSMOS.bindGlobalShortcuts();
    COSMOS.startJobPolling();
    if (!sessionStorage.getItem("cosmos_ux_ready")) {
      sessionStorage.setItem("cosmos_ux_ready", "1");
      COSMOS.notify("COSMOS engineering environment ready", "info", COSMOS.getProjectContext().name);
    }
  };
})();
