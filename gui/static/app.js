const COSMOS = {
  hubPage: 1,
  hubPages: 3,
  touchStartX: 0,
  touchStartY: 0,
  swipeLocked: false,
  workbenchCatalog: null,
  currentUser: null,
  activeNav: "workbenches",
  navExpanded: false,
  auditEvents: [],
  auditPage: 1,
  auditPageSize: 25,

  NAV_ICONS: {
    command: '<svg viewBox="0 0 24 24"><rect x="3" y="3" width="8" height="8" rx="1"/><rect x="13" y="3" width="8" height="8" rx="1"/><rect x="3" y="13" width="8" height="8" rx="1"/><rect x="13" y="13" width="8" height="8" rx="1"/></svg>',
    "design-contract": '<svg viewBox="0 0 24 24"><path d="M6 4h12v16H6z"/><path d="M9 8h6M9 12h6M9 16h4"/></svg>',
    knowledge: '<svg viewBox="0 0 24 24"><circle cx="6" cy="6" r="2.5"/><circle cx="18" cy="6" r="2.5"/><circle cx="12" cy="18" r="2.5"/><path d="M8 7.5 10.5 15M16 7.5 13.5 15"/></svg>',
    propulsion: '<svg viewBox="0 0 24 24"><path d="M12 3v4M8 7l-2 2M16 7l2 2"/><path d="M10 13h4l1 8H9l1-8z"/><path d="M12 13V9"/></svg>',
    cad: '<svg viewBox="0 0 24 24"><path d="M4 8l8-4 8 4v8l-8 4-8-4z"/><path d="M12 4v16"/></svg>',
    physics: '<svg viewBox="0 0 24 24"><path d="M4 12c3-6 13-6 16 0s-13 6-16 0z"/><circle cx="12" cy="12" r="2"/></svg>',
    simulation: '<svg viewBox="0 0 24 24"><path d="M4 18h16"/><path d="M7 16V8l5-3 5 3v8"/></svg>',
    optimization: '<svg viewBox="0 0 24 24"><path d="M4 18V6M20 18V10M12 18V4"/><circle cx="4" cy="6" r="1.5"/><circle cx="20" cy="10" r="1.5"/><circle cx="12" cy="4" r="1.5"/></svg>',
    comparison: '<svg viewBox="0 0 24 24"><rect x="4" y="5" width="6" height="14" rx="1"/><rect x="14" y="5" width="6" height="14" rx="1"/></svg>',
    documentation: '<svg viewBox="0 0 24 24"><path d="M7 4h10v16H7z"/><path d="M10 8h4M10 12h4"/></svg>',
    vv: '<svg viewBox="0 0 24 24"><path d="M12 3 4 7v6c0 5 3.5 8 8 8s8-3 8-8V7l-8-4z"/><path d="M9 12l2 2 4-4"/></svg>',
    release: '<svg viewBox="0 0 24 24"><rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 1 1 8 0v3"/></svg>',
    project: '<svg viewBox="0 0 24 24"><path d="M4 7h16v12H4z"/><path d="M8 7V5h8v2"/></svg>',
    files: '<svg viewBox="0 0 24 24"><path d="M6 4h8l4 4v12H6z"/><path d="M14 4v4h4"/></svg>',
    jobs: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8"/><path d="M12 8v4l3 2"/></svg>',
    log: '<svg viewBox="0 0 24 24"><path d="M8 6h12"/><path d="M8 12h12"/><path d="M8 18h12"/><circle cx="4" cy="6" r="1"/><circle cx="4" cy="12" r="1"/><circle cx="4" cy="18" r="1"/></svg>',
    workbenches: '<svg viewBox="0 0 24 24"><rect x="3" y="3" width="8" height="8" rx="1.5"/><rect x="13" y="3" width="8" height="8" rx="1.5"/><rect x="3" y="13" width="8" height="8" rx="1.5"/><rect x="13" y="13" width="8" height="8" rx="1.5"/></svg>',
    projects: '<svg viewBox="0 0 24 24"><path d="M4 7h16v12H4z"/><path d="M8 7V5h8v2"/></svg>',
    manufacturing: '<svg viewBox="0 0 24 24"><path d="M3 18h18"/><path d="M6 18V9l4-3 4 3v9"/></svg>',
    admin: '<svg viewBox="0 0 24 24"><circle cx="12" cy="8" r="3.5"/><path d="M5 20a7 7 0 0 1 14 0"/></svg>',
    audit: '<svg viewBox="0 0 24 24"><path d="M8 6h12"/><path d="M8 12h12"/><path d="M8 18h12"/><circle cx="4" cy="6" r="1"/><circle cx="4" cy="12" r="1"/><circle cx="4" cy="18" r="1"/></svg>',
    settings: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M12 2v2M12 20v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M2 12h2M20 12h2"/></svg>',
    help: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 0 1 4.5 1.5c0 1.5-2 2-2 3.5"/><circle cx="12" cy="17" r="0.8" fill="currentColor" stroke="none"/></svg>',
    logout: '<svg viewBox="0 0 24 24"><path d="M10 7V5a2 2 0 0 1 2-2h7v18h-7a2 2 0 0 1-2-2v-2"/><path d="M3 12h10"/><path d="M7 8l-4 4 4 4"/></svg>',
  },

  WORKBENCH_DOMAINS: {
    "rocket-engine": "propulsion",
    turbopumps: "propulsion",
    pid: "documentation",
    structures: "structures",
    "rocket-staging": "propulsion",
    manufacturing: "manufacturing",
    simulation: "simulation",
    visualization: "physics",
    documentation: "documentation",
    "code-comparison": "comparison",
    plm: "release",
    knowledge: "knowledge",
  },

  ORG_OPTIONS: {
    designations: [
      "Graduate Engineer",
      "Engineer I",
      "Engineer II",
      "Senior Engineer",
      "Lead Engineer",
      "Principal Engineer",
      "Chief Engineer",
      "Propulsion Engineer",
      "Structural Engineer",
      "Systems Engineer",
      "Manufacturing Engineer",
      "Simulation Engineer",
      "Design Engineer",
      "Quality Engineer",
      "Test Engineer",
      "CAD / Design Engineer",
      "P&ID Engineer",
      "Turbomachinery Engineer",
      "Combustion Devices Engineer",
      "Avionics Engineer",
      "Project Manager",
      "Technical Fellow",
      "System Administrator",
    ],
    teams: [
      "Rocket Engine",
      "Turbopumps",
      "Structures",
      "Rocket Staging",
      "Propulsion Systems",
      "Manufacturing",
      "Simulation & Analysis",
      "Visualization & Graphs",
      "P&ID / Documentation",
      "PLM & Configuration",
      "Knowledge Architecture",
      "Quality & Assurance",
      "Test & Verification",
      "Platform / IT",
      "Executive / Leadership",
      "Cross-Functional Engineering",
    ],
    roles: [
      { value: "VIEWER", label: "VIEWER — Read-only access" },
      { value: "ENGINEER", label: "ENGINEER — Workbench & knowledge access" },
      { value: "REVIEWER", label: "REVIEWER — Review & audit visibility" },
      { value: "APPROVER", label: "APPROVER — Approval & audit visibility" },
      { value: "ADMIN", label: "ADMIN — Full administration" },
    ],
  },

  populateSelect(id, options, { labels = false } = {}) {
    const element = document.getElementById(id);
    if (!element) return;
    element.innerHTML = "";
    options.forEach((option) => {
      const node = document.createElement("option");
      if (labels && option.value) {
        node.value = option.value;
        node.textContent = option.label;
      } else {
        node.value = option;
        node.textContent = option;
      }
      element.appendChild(node);
    });
  },

  bindSidebarTooltips() {
    document.querySelectorAll(".sidebar-btn[data-tip]").forEach((button) => {
      if (button.dataset.tipBound) return;
      button.dataset.tipBound = "1";
    });
  },

  navIcon(name) {
    return `<span class="nav-icon" aria-hidden="true">${this.NAV_ICONS[name] || this.NAV_ICONS.workbenches}</span>`;
  },

  canAudit(user) {
    return COSMOS.permissions?.canAudit(user) ?? String(user?.role || "").toUpperCase() === "ADMIN";
  },

  canAdmin(user) {
    return COSMOS.permissions?.canAdmin(user) ?? String(user?.role || "").toUpperCase() === "ADMIN";
  },

  canKnowledgeAdmin(user) {
    return COSMOS.permissions?.canKnowledgeAdmin(user) ?? this.canAdmin(user);
  },

  renderSidebar(activeNav, user) {
    const sidebar = document.querySelector(".sidebar");
    if (!sidebar) return;
    this.activeNav = activeNav;
    this.navExpanded = localStorage.getItem("cosmos_nav_expanded") === "1";
    const expandedClass = this.navExpanded ? " nav-expanded" : "";
    document.querySelector(".app-body")?.classList.toggle("nav-expanded", this.navExpanded);

    // Propulsion / Physics live inside Rocket Engine workbench suite — not top-level nav.
    const primary = [
      { id: "command", label: "Command", icon: "command", href: this.hubUrl(this.hubPageFromUrl()), tip: "Workbench launcher & command workspace" },
      { id: "design-contract", label: "Design Contract", icon: "design-contract", href: null, tip: "Requirements & design contract (coming soon)", disabled: true },
      { id: "knowledge", label: "Knowledge", icon: "knowledge", href: "/app/workbench/knowledge", tip: "Maharshi Bharadwaj — evidence & knowledge infrastructure" },
      { id: "cad", label: "CAD / Geometry", icon: "cad", href: null, tip: "Parametric CAD studio (coming soon)", disabled: true },
      { id: "simulation", label: "Simulation", icon: "simulation", href: "/app/workbenches?page=2", tip: "Simulation hub — CFD, FEA, multiphysics" },
      { id: "optimization", label: "Optimization", icon: "optimization", href: null, tip: "Design space & Pareto exploration (coming soon)", disabled: true },
      { id: "comparison", label: "Comparison", icon: "comparison", href: "/app/workbenches?page=3", tip: "Comparison cockpit & OTCS validation" },
      { id: "documentation", label: "Documentation", icon: "documentation", href: null, tip: "Controlled documentation (coming soon)", disabled: true },
      { id: "vv", label: "V&V", icon: "vv", href: null, tip: "Verification & validation (coming soon)", disabled: true },
      { id: "release", label: "Release", icon: "release", href: null, tip: "Manufacturing release gate (coming soon)", disabled: true },
    ];
    const secondary = [
      { id: "project", label: "Project", icon: "project", href: null, tip: "Project context", action: "project" },
      { id: "files", label: "Files", icon: "files", href: null, tip: "Recent files (hub)", disabled: true },
      { id: "jobs", label: "Jobs", icon: "jobs", href: null, tip: "Background job manager", action: "jobs" },
      { id: "log", label: "Log", icon: "log", href: null, tip: "Engineering log (coming soon)", disabled: true },
    ];
    const system = [];
    if (this.canAudit(user)) {
      system.push({ id: "audit", label: "Audit Trail", icon: "audit", href: "/app/audit", tip: "Application audit log" });
    }
    if (this.canAdmin(user)) {
      system.push({ id: "admin", label: "Administration", icon: "admin", href: "/app/admin", tip: "User administration" });
    }
    system.push(
      { id: "settings", label: "Settings", icon: "settings", href: null, tip: "Application settings (coming soon)", disabled: true },
      { id: "help", label: "Help", icon: "help", href: null, tip: "COSMOS help (coming soon)", disabled: true },
    );

    const renderBtn = (item) => {
      const active = item.id === activeNav ? " active" : "";
      const disabled = item.disabled ? " disabled" : "";
      let action = item.disabled ? "disabled" : "";
      if (item.href) {
        action = `onclick="location.href='${item.href}'"`;
      } else if (item.action === "project") {
        action = 'onclick="COSMOS.openProjectModal?.()"';
      } else if (item.action === "jobs") {
        action = 'onclick="COSMOS.toggleJobManager?.(true)"';
      }
      return `<button type="button" class="sidebar-btn${active}${disabled}" data-nav="${item.id}" data-tip="${item.tip}" ${action} aria-label="${item.label}">${this.navIcon(item.icon)}<span class="nav-label">${item.label}</span></button>`;
    };

    sidebar.innerHTML = `
      <button type="button" class="sidebar-toggle" id="nav-expand-toggle" aria-label="Expand navigation">${this.navExpanded ? "◂ Collapse" : "▸ Expand"}</button>
      <div class="sidebar-group">
        <div class="sidebar-group-label">Workspaces</div>
        ${primary.map(renderBtn).join("")}
      </div>
      <div class="sidebar-group">
        <div class="sidebar-group-label">Secondary</div>
        ${secondary.map(renderBtn).join("")}
      </div>
      <div class="sidebar-group">
        <div class="sidebar-group-label">System</div>
        ${system.map(renderBtn).join("")}
        <button type="button" class="sidebar-btn" id="logout-btn" data-nav="logout" data-tip="Sign out of COSMOS" aria-label="Log out">${this.navIcon("logout")}<span class="nav-label">Log out</span></button>
      </div>`;

    document.getElementById("nav-expand-toggle")?.addEventListener("click", () => {
      this.navExpanded = !this.navExpanded;
      localStorage.setItem("cosmos_nav_expanded", this.navExpanded ? "1" : "0");
      document.querySelector(".app-body")?.classList.toggle("nav-expanded", this.navExpanded);
      const toggle = document.getElementById("nav-expand-toggle");
      if (toggle) toggle.textContent = this.navExpanded ? "◂ Collapse" : "▸ Expand";
    });
    this.bindLogout();
    this.bindSidebarTooltips();
  },

  setStatusBar(message, state = "ready", meta = "COSMOS 0.1") {
    const bar = document.getElementById("status-bar");
    if (!bar) return;
    const indicator = bar.querySelector(".status-indicator") || (() => {
      const node = document.createElement("span");
      node.className = "status-indicator ready";
      node.setAttribute("aria-hidden", "true");
      bar.prepend(node);
      return node;
    })();
    indicator.className = `status-indicator ${state}`;
    let textNode = bar.querySelector(".status-bar-text");
    if (!textNode) {
      textNode = document.createElement("span");
      textNode.className = "status-bar-text";
      bar.appendChild(textNode);
    }
    textNode.textContent = message;
    let metaNode = bar.querySelector(".status-bar-meta");
    if (!metaNode) {
      metaNode = document.createElement("span");
      metaNode.className = "status-bar-meta";
      bar.appendChild(metaNode);
    }
    metaNode.textContent = meta;
  },

  workbenchArt(workbenchId) {
    const png = `/assets/workbenches/${workbenchId}.png`;
    const svg = `/assets/workbenches/${workbenchId}.svg`;
    if (workbenchId === "knowledge") return "/assets/maharshi_bharadwaj.png";
    return png;
  },

  workbenchArtFallback(workbenchId) {
    return `/assets/workbenches/${workbenchId}.svg`;
  },

  hubPageFromUrl() {
    const params = new URLSearchParams(window.location.search);
    const fromUrl = parseInt(params.get("page") || "", 10);
    if (!Number.isNaN(fromUrl) && fromUrl >= 1) return fromUrl;
    const stored = parseInt(sessionStorage.getItem("cosmos_hub_page") || "1", 10);
    return Number.isNaN(stored) ? 1 : stored;
  },

  rememberHubPage(page) {
    this.hubPage = page;
    sessionStorage.setItem("cosmos_hub_page", String(page));
  },

  workbenchUrl(route, page) {
    const resolved = page || this.hubPage;
    return `${route}?page=${resolved}`;
  },

  hubUrl(page) {
    return `/app/workbenches?page=${page || this.hubPage}`;
  },

  async session() {
    const response = await fetch("/api/auth/session");
    if (!response.ok) {
      window.location.href = "/";
      return null;
    }
    return response.json();
  },

  applyHeader(user) {
    const avatar = document.getElementById("avatar");
    const badge = document.getElementById("user-badge");
    const contextPrimary = document.getElementById("header-context-primary");
    const contextSecondary = document.getElementById("header-context-secondary");
    if (badge) badge.textContent = user.display_name;
    if (contextPrimary) contextPrimary.textContent = user.display_name;
    const project = typeof this.getProjectContext === "function" ? this.getProjectContext().name : "COSMOS 0.1";
    const infrastructure = localStorage.getItem("cosmos_infrastructure") || user.team;
    const loginProfile = localStorage.getItem("cosmos_login_profile") || user.role;
    if (contextSecondary) {
      contextSecondary.textContent = `${infrastructure} · ${loginProfile}`;
    }
    if (avatar) {
      avatar.title = "Double-click to edit profile";
      if (user.profile_photo_url) {
        avatar.style.backgroundImage = `url('${user.profile_photo_url}?t=${Date.now()}')`;
        avatar.classList.add("has-photo");
      } else {
        avatar.style.backgroundImage = "";
        avatar.classList.remove("has-photo");
      }
    }
    this.currentUser = user;
    this.setStatusBar(
      `Signed in as ${user.login_id} (${user.role})`,
      "ready",
      `${project} · ${infrastructure}`,
    );
    this.applyRoleVisibility(user);
    this.renderGlobalHeaderZones?.();
  },

  applyRoleVisibility(user) {
    document.body.classList.toggle("cosmos-admin-user", this.canAdmin(user));
    document.body.classList.toggle("cosmos-knowledge-admin", this.canKnowledgeAdmin(user));
  },

  simplifyHeader() {
    document.querySelectorAll(".header-meta .header-pill-editable").forEach((node) => node.remove());
    const meta = document.querySelector(".header-meta");
    if (meta && !document.getElementById("header-context-primary")) {
      meta.innerHTML = `
        <div class="cosmos-global-zones" id="cosmos-global-zones"></div>
        <div class="header-context">
          <span class="context-primary" id="header-context-primary">COSMOS</span>
          <span class="context-secondary" id="header-context-secondary">Engineering Workspace</span>
        </div>`;
    }
    this.renderGlobalHeaderZones();
  },

  renderGlobalHeaderZones() {
    const host = document.getElementById("cosmos-global-zones");
    if (!host) return;
    const project = typeof this.getProjectContext === "function" ? this.getProjectContext() : { name: "Default Project" };
    const infrastructure = localStorage.getItem("cosmos_infrastructure") || "Engineering Workbench";
    const workspace = window.location.pathname.includes("/workbench/") ? "Workbench" : "Command";
    host.innerHTML = `
      <span class="zone-brand">COSMOS</span>
      <button type="button" class="zone-pill clickable status-active" id="zone-project" title="Project context">
        <span class="zone-label">Project</span>
        <span class="zone-value">${project.name || "Default Project"}</span>
      </button>
      <span class="zone-pill status-active" id="zone-workspace">
        <span class="zone-label">Workspace</span>
        <span class="zone-value">${workspace}</span>
      </span>
      <span class="zone-pill status-idle" id="zone-solver">
        <span class="zone-label">Solver</span>
        <span class="zone-value" id="zone-solver-value">IDLE</span>
      </span>
      <span class="zone-pill status-ready" id="zone-ai">
        <span class="zone-label">AI</span>
        <span class="zone-value">Maharshi</span>
      </span>
      <span class="zone-pill status-active" id="zone-kb">
        <span class="zone-label">KB</span>
        <span class="zone-value">Ready</span>
      </span>
      <span class="zone-pill" id="zone-security">
        <span class="zone-label">Infra</span>
        <span class="zone-value">${infrastructure}</span>
      </span>`;
    document.getElementById("zone-project")?.addEventListener("click", () => this.openProjectModal?.());
  },

  workbenchDomain(workbenchId) {
    return this.WORKBENCH_DOMAINS[workbenchId] || "general";
  },

  workbenchMeta(item) {
    return {
      design_type: item.design_type || "Engineering Module",
      revision: item.revision || "—",
      validation_state: item.validation_state || (item.status === "active" ? "ACTIVE" : "PLANNED"),
      domain: item.domain || this.workbenchDomain(item.workbench_id),
    };
  },

  mountShellFragments() {
    const frame = document.querySelector(".app-frame");
    if (!frame) return;

    if (!document.getElementById("profile-modal")) {
      const modal = document.createElement("div");
      modal.className = "profile-modal";
      modal.id = "profile-modal";
      modal.innerHTML = `
        <div class="profile-panel">
          <div class="profile-panel-header">
            <h2>Employee Profile</h2>
            <button type="button" id="profile-close" class="profile-close" aria-label="Close">✕</button>
          </div>
          <div class="profile-photo-row">
            <button type="button" class="profile-photo-preview" id="profile-photo-preview" onclick="document.getElementById('profile-photo-input').click()"></button>
            <div>
              <input type="file" id="profile-photo-input" accept="image/jpeg,image/png,image/webp" hidden />
              <p class="profile-hint">Double-click avatar to open profile.</p>
              <p><strong>Login:</strong> <span id="profile-login-id"></span></p>
              <p><strong>Role:</strong> <span id="profile-role"></span></p>
              <p><strong>Employee ID:</strong> <span id="profile-employee-id"></span></p>
            </div>
          </div>
          <label>Name<input id="profile-display-name" /></label>
          <label>Designation<input id="profile-designation" /></label>
          <label>Team<input id="profile-team" /></label>
          <label>Bio<textarea id="profile-bio" rows="3"></textarea></label>
          <div class="error-text" id="profile-error"></div>
          <button type="button" class="primary profile-save" id="profile-save">SAVE PROFILE</button>
        </div>`;
      document.body.appendChild(modal);
    }

    if (!document.getElementById("maharshi-module") && !window.location.pathname.includes("/workbench/knowledge")) {
      const fab = document.createElement("button");
      fab.type = "button";
      fab.className = "maharshi-module";
      fab.id = "maharshi-module";
      fab.title = "Maharshi Bharadwaj — Knowledge pop-up";
      fab.innerHTML = '<img src="/assets/maharshi_bharadwaj.png" alt="Maharshi Bharadwaj" /><span>MAHARSHI BHARADWAJ</span>';
      frame.appendChild(fab);
    }
  },

  bindProfileTriggers(user) {
    const open = () => this.openProfileModal(user, "display_name");
    const avatar = document.getElementById("avatar");
    avatar?.addEventListener("dblclick", open);
    document.getElementById("user-badge")?.addEventListener("click", open);
  },

  openProfileModal(user, focusField = "photo") {
    const modal = document.getElementById("profile-modal");
    if (!modal) return;
    document.getElementById("profile-display-name").value = user.display_name || "";
    document.getElementById("profile-designation").value = user.designation || "";
    document.getElementById("profile-team").value = user.team || "";
    document.getElementById("profile-bio").value = user.bio || "";
    document.getElementById("profile-employee-id").textContent = user.employee_id || "";
    document.getElementById("profile-login-id").textContent = user.login_id || "";
    document.getElementById("profile-role").textContent = user.role || "";
    const preview = document.getElementById("profile-photo-preview");
    if (user.profile_photo_url) {
      preview.style.backgroundImage = `url('${user.profile_photo_url}?t=${Date.now()}')`;
    } else {
      preview.style.backgroundImage = "";
    }
    modal.classList.add("open");
    modal.dataset.focus = focusField;
    const target = document.getElementById(`profile-${focusField}`) || document.getElementById("profile-photo-preview");
    target?.scrollIntoView({ block: "center", behavior: "smooth" });
  },

  closeProfileModal() {
    document.getElementById("profile-modal")?.classList.remove("open");
  },

  async saveProfile() {
    const payload = {
      display_name: document.getElementById("profile-display-name").value,
      designation: document.getElementById("profile-designation").value,
      team: document.getElementById("profile-team").value,
      bio: document.getElementById("profile-bio").value,
    };
    const response = await fetch("/api/profile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const body = await response.json();
    if (!response.ok) {
      document.getElementById("profile-error").textContent = body.error || "Save failed.";
      return;
    }
    document.getElementById("profile-error").textContent = "";
    this.applyHeader(body.user);
    this.closeProfileModal();
  },

  async uploadProfilePhoto(file) {
    if (!file) return;
    const data = new FormData();
    data.append("photo", file);
    const response = await fetch("/api/profile/photo", { method: "POST", body: data });
    const body = await response.json();
    if (!response.ok) {
      document.getElementById("profile-error").textContent = body.error || "Photo upload failed.";
      return;
    }
    const session = await this.session();
    if (session) this.applyHeader({ ...session.user, profile_photo_url: body.profile_photo_url });
    if (body.profile_photo_url) {
      document.getElementById("profile-photo-preview").style.backgroundImage =
        `url('${body.profile_photo_url}?t=${Date.now()}')`;
    }
  },

  bindLogout() {
    document.getElementById("logout-btn")?.addEventListener("click", async () => {
      await fetch("/api/auth/logout", { method: "POST" });
      window.location.href = "/";
    });
  },

  bindMaharshi() {
    if (typeof this.bindMaharshiPopupTrigger === "function") {
      this.bindMaharshiPopupTrigger();
    }
  },

  openWorkbench(item, page) {
    if (!item?.route) return;
    if (item.status !== "active") {
      if (typeof this.notify === "function") {
        this.notify(`${item.title} is planned — not yet available`, "warning");
      }
      return;
    }
    this.rememberHubPage(page);
    if (typeof this.trackRecentWorkbench === "function") {
      this.trackRecentWorkbench(item);
    }
    if (typeof this.setStatusBar === "function") {
      this.setStatusBar(`Opening ${item.title}…`, "processing");
    }
    window.location.href = this.workbenchUrl(item.route, page);
  },

  bindProfileModalActions() {
    document.getElementById("profile-close")?.addEventListener("click", () => this.closeProfileModal());
    document.getElementById("profile-save")?.addEventListener("click", () => this.saveProfile());
    document.getElementById("profile-photo-input")?.addEventListener("change", (event) => {
      const file = event.target.files?.[0];
      this.uploadProfilePhoto(file);
    });
    document.getElementById("profile-modal")?.addEventListener("click", (event) => {
      if (event.target.id === "profile-modal") this.closeProfileModal();
    });
  },

  async initShell(options = {}) {
    const session = await this.session();
    if (!session) return null;
    this.simplifyHeader();
    this.applyHeader(session.user);
    this.renderSidebar(options.activeNav || this.detectActiveNav(), session.user);
    this.mountShellFragments();
    this.bindProfileTriggers(session.user);
    this.bindMaharshi();
    this.bindProfileModalActions();
    if (typeof this.initEngineeringUX === "function") {
      this.initEngineeringUX();
    }
    return session;
  },

  detectActiveNav() {
    const path = window.location.pathname;
    if (path.includes("/workbench/knowledge")) return "knowledge";
    if (path.includes("/audit")) return "audit";
    if (path.includes("/admin")) return "admin";
    if (path.includes("/workbench/rocket-engine")) return "command";
    if (path.includes("/physics/")) return "command";
    if (path.includes("/workbench/")) return "command";
    const page = this.hubPageFromUrl?.() || 1;
    if (path.includes("/workbenches")) {
      if (page === 2) return "simulation";
      if (page === 3) return "comparison";
      return "command";
    }
    return "command";
  },

  renderWorkbenchCards(items, page) {
    const track = document.getElementById("workbench-track");
    if (!track) return;
    track.innerHTML = "";
    track.dataset.page = String(page);
    items.forEach((item) => {
      const card = document.createElement("button");
      card.type = "button";
      const meta = this.workbenchMeta(item);
      const blendClass = ["structures", "pid", "rocket-staging"].includes(item.workbench_id) ? "art-light" : "art-dark";
      card.className = `workbench-card domain-${meta.domain} ${blendClass}`;
      const art = this.workbenchArt(item.workbench_id);
      card.innerHTML = `
        <div class="workbench-card-meta">
          <span class="workbench-meta-chip status-${item.status === "active" ? "active" : "planned"}">${item.status}</span>
          <span class="workbench-meta-chip">${meta.revision}</span>
          <span class="workbench-meta-chip">${meta.design_type}</span>
          <span class="workbench-meta-chip">${meta.validation_state}</span>
        </div>
        <div class="workbench-art-wrap">
          <img class="workbench-art-img" src="${art}" alt="${item.title}" loading="lazy"
               onerror="this.onerror=null;this.src='${this.workbenchArtFallback(item.workbench_id)}';" />
          <div class="workbench-art-vignette"></div>
        </div>
        <div class="workbench-card-footer">
          <h3>${item.title.toUpperCase()}</h3>
          <p class="workbench-desc">${item.description || "Engineering workbench module."}</p>
        </div>`;
      card.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        this.openWorkbench(item, page);
      });
      track.appendChild(card);
    });
  },

  updatePager(page, totalPages) {
    const dots = document.getElementById("page-dots");
    if (!dots) return;
    dots.innerHTML = "";
    for (let index = 1; index <= totalPages; index += 1) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "page-dot" + (index === page ? " active" : "");
      button.title = `Page ${index}`;
      button.onclick = () => this.goToHubPage(index);
      dots.appendChild(button);
    }
    const label = document.getElementById("page-label");
    if (label) label.innerHTML = `Page <strong>${page}</strong> of <strong>${totalPages}</strong>`;
  },

  async goToHubPage(page, { animate = true } = {}) {
    if (!this.workbenchCatalog) {
      this.workbenchCatalog = await fetch("/api/workbenches").then((r) => r.json());
    }
    const catalog = this.workbenchCatalog;
    const totalPages = catalog.pages.length;
    const clamped = Math.max(1, Math.min(totalPages, page));
    const previous = this.hubPage;
    this.rememberHubPage(clamped);
    const viewport = document.getElementById("carousel-viewport");
    const active = catalog.pages.find((entry) => entry.page === clamped) || catalog.pages[0];
    if (animate && viewport && clamped !== previous) {
      viewport.classList.remove("slide-left", "slide-right");
      void viewport.offsetWidth;
      viewport.classList.add(clamped > previous ? "slide-left" : "slide-right");
      viewport.classList.add("transitioning");
      setTimeout(() => {
        viewport.classList.remove("transitioning", "slide-left", "slide-right");
      }, 360);
    }
    this.renderWorkbenchCards(active.items, clamped);
    this.updatePager(clamped, totalPages);
    const url = new URL(window.location.href);
    url.searchParams.set("page", String(clamped));
    window.history.replaceState({}, "", url.pathname + url.search);
  },

  swipeToPage(direction) {
    if (this.swipeLocked) return;
    this.swipeLocked = true;
    setTimeout(() => { this.swipeLocked = false; }, 420);
    const total = this.hubPages || 3;
    if (direction > 0) {
      this.goToHubPage(this.hubPage >= total ? 1 : this.hubPage + 1);
    } else {
      this.goToHubPage(this.hubPage <= 1 ? total : this.hubPage - 1);
    }
  },

  bindCarouselControls(totalPages) {
    document.getElementById("page-prev")?.addEventListener("click", () => this.swipeToPage(-1));
    document.getElementById("page-next")?.addEventListener("click", () => this.swipeToPage(1));

    const viewport = document.getElementById("carousel-viewport");
    if (!viewport) return;

    const onStart = (x, y) => {
      this.touchStartX = x;
      this.touchStartY = y;
    };
    const onEnd = (x, y) => {
      const dx = x - this.touchStartX;
      const dy = y - this.touchStartY;
      if (Math.abs(dx) < 50 || Math.abs(dx) < Math.abs(dy) * 1.2) return;
      this.swipeToPage(dx < 0 ? 1 : -1);
    };

    viewport.addEventListener("touchstart", (event) => {
      onStart(event.touches[0].clientX, event.touches[0].clientY);
    }, { passive: true });
    viewport.addEventListener("touchend", (event) => {
      onEnd(event.changedTouches[0].clientX, event.changedTouches[0].clientY);
    }, { passive: true });

    viewport.addEventListener("pointerdown", (event) => {
      if (event.target.closest(".workbench-card")) return;
      if (event.pointerType === "mouse" && event.button !== 0) return;
      onStart(event.clientX, event.clientY);
      this.carouselDragging = true;
    });
    viewport.addEventListener("pointerup", (event) => {
      if (event.target.closest(".workbench-card")) return;
      if (!this.carouselDragging) return;
      this.carouselDragging = false;
      onEnd(event.clientX, event.clientY);
    });

    let wheelAccum = 0;
    viewport.addEventListener("wheel", (event) => {
      const dominant = Math.abs(event.deltaX) > Math.abs(event.deltaY) ? event.deltaX : event.deltaY;
      wheelAccum += dominant;
      if (Math.abs(wheelAccum) < 80) return;
      event.preventDefault();
      this.swipeToPage(wheelAccum > 0 ? 1 : -1);
      wheelAccum = 0;
    }, { passive: false });
  },

  async initWorkbenchHub() {
    const session = await this.initShell({ activeNav: "command" });
    if (!session) return;
    this.hubPage = this.hubPageFromUrl();
    this.rememberHubPage(this.hubPage);
    this.workbenchCatalog = await fetch("/api/workbenches").then((r) => r.json());
    this.hubPages = this.workbenchCatalog.pages.length;
    await this.goToHubPage(this.hubPage, { animate: false });
    this.bindCarouselControls(this.hubPages);
    this.bindHubKeyboard();
    this.renderQuickStatus();
    document.body.classList.add("cosmos-show-recent");
    if (typeof this.renderRecentPanel === "function") {
      this.renderRecentPanel();
    }
  },

  bindHubKeyboard() {
    document.addEventListener("keydown", (event) => {
      if (event.target.matches("input, textarea, select")) return;
      if (event.key === "ArrowRight") this.swipeToPage(1);
      if (event.key === "ArrowLeft") this.swipeToPage(-1);
    });
  },

  renderQuickStatus() {
    const host = document.getElementById("quick-status");
    if (!host) return;
    const activeCount = (this.workbenchCatalog?.pages || [])
      .flatMap((page) => page.items)
      .filter((item) => item.status === "active").length;
    host.innerHTML = `
      <div class="quick-status-item"><span class="status-indicator ready"></span><span>System <strong>Ready</strong></span></div>
      <div class="quick-status-item"><span>Active workbenches <strong>${activeCount}</strong></span></div>
      <div class="quick-status-item"><span>Workspace <strong>Local</strong></span></div>
      <div class="quick-status-item"><span>Knowledge <strong>Maharshi Bharadwaj</strong></span></div>`;
  },

  async initAdminPanel() {
    const session = await this.initShell({ activeNav: "admin" });
    if (!session) return;
    if (session.user.role !== "ADMIN") {
      window.location.href = "/app/workbenches";
      return;
    }
    this.populateSelect("designation", this.ORG_OPTIONS.designations);
    this.populateSelect("team", this.ORG_OPTIONS.teams);
    this.populateSelect("role", this.ORG_OPTIONS.roles, { labels: true });
    document.getElementById("designation").value = "Engineer II";
    document.getElementById("team").value = "Rocket Engine";
    document.getElementById("role").value = "ENGINEER";

    const modal = document.getElementById("credential-modal");
    const closeCredential = () => {
      modal?.classList.remove("open");
      document.getElementById("cred-login-id").textContent = "—";
      document.getElementById("cred-password").textContent = "—";
    };
    const showCredentials = (creds) => {
      if (!creds || !modal) return;
      document.getElementById("cred-login-id").textContent = creds.login_id;
      document.getElementById("cred-password").textContent = creds.password;
      modal.classList.add("open");
    };
    document.getElementById("credential-close")?.addEventListener("click", closeCredential);
    document.getElementById("credential-ack")?.addEventListener("click", closeCredential);
    document.getElementById("copy-login-id")?.addEventListener("click", () => {
      navigator.clipboard?.writeText(document.getElementById("cred-login-id").textContent || "");
    });
    document.getElementById("copy-password")?.addEventListener("click", () => {
      navigator.clipboard?.writeText(document.getElementById("cred-password").textContent || "");
    });

    const loadUsers = async () => {
      const response = await fetch("/api/admin/users");
      const body = await response.json();
      const tbody = document.getElementById("users-body");
      if (!tbody) return;
      const filter = (document.getElementById("user-search")?.value || "").trim().toLowerCase();
      tbody.innerHTML = "";
      (body.users || [])
        .filter((user) => {
          if (!filter) return true;
          const haystack = [user.login_id, user.display_name, user.role, user.team, user.employee_id]
            .join(" ")
            .toLowerCase();
          return haystack.includes(filter);
        })
        .forEach((user) => {
          const row = document.createElement("tr");
          row.innerHTML = `<td>${user.login_id}</td><td>${user.display_name}</td><td><span class="cosmos-badge info">${user.role}</span></td><td>${user.team}</td><td>${user.employee_id}</td><td><span class="cosmos-badge success">ACTIVE</span></td>`;
          tbody.appendChild(row);
        });
    };
    await loadUsers();
    document.getElementById("user-search")?.addEventListener("input", () => loadUsers());
    document.getElementById("register-form")?.addEventListener("submit", async (event) => {
      event.preventDefault();
      const error = document.getElementById("register-error");
      if (error) error.textContent = "";
      const payload = {
        auto_generate: true,
        display_name: document.getElementById("display_name").value,
        employee_id: document.getElementById("employee_id").value,
        designation: document.getElementById("designation").value,
        team: document.getElementById("team").value,
        role: document.getElementById("role").value,
      };
      const response = await fetch("/api/admin/users", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const body = await response.json();
      if (!response.ok) {
        if (error) error.textContent = body.error || "Registration failed.";
        return;
      }
      document.getElementById("register-form")?.reset();
      document.getElementById("designation").value = "Engineer II";
      document.getElementById("team").value = "Rocket Engine";
      document.getElementById("role").value = "ENGINEER";
      await loadUsers();
      showCredentials(body.one_time_credentials);
    });
  },

  async initWorkbenchDetail(workbenchId) {
    const session = await this.initShell({ activeNav: "workbenches" });
    if (!session) return;
    this.hubPage = this.hubPageFromUrl();
    const back = document.getElementById("back-link");
    if (back) back.href = this.hubUrl(this.hubPage);

    const detail = await fetch(`/api/workbenches/${workbenchId}`).then((r) => r.json());
    if (typeof this.trackRecentWorkbench === "function") {
      this.trackRecentWorkbench({
        workbench_id: workbenchId,
        title: detail.title,
        route: `/app/workbench/${workbenchId}`,
      });
    }
    document.getElementById("workbench-title").textContent = detail.title;
    document.getElementById("workbench-description").textContent = detail.description;
    document.getElementById("workbench-status").textContent = detail.status.toUpperCase();

    const hero = document.getElementById("workbench-hero");
    if (hero) {
      const art = this.workbenchArt(workbenchId);
      hero.innerHTML = `<img src="${art}" alt="${detail.title}" onerror="this.src='${this.workbenchArtFallback(workbenchId)}'" />`;
    }

    const modules = document.getElementById("module-grid");
    if (modules) {
      modules.innerHTML = "";
      (detail.modules || []).forEach((name) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "module-btn";
        button.textContent = name.toUpperCase();
        button.onclick = () => {
          const suiteMap = {
            "Propulsion Design Suite": "nozzle-flow",
            "Nozzle Flow": "nozzle-flow",
            "Heat Transfer": "heat-transfer",
            "Chamber Structures": "structures",
            "Compressible Flow (Physics Slice)": "nozzle-flow",
          };
          if (Object.prototype.hasOwnProperty.call(suiteMap, name)) {
            window.location.href = `/app/workbench/rocket-engine?module=${suiteMap[name]}`;
            return;
          }
          alert(`${name} is registered. Solver integration is routed through governed backend APIs.`);
        };
        modules.appendChild(button);
      });
    }
  },

  async initAuditPage() {
    const session = await this.initShell({ activeNav: "audit" });
    if (!session) return;
    if (!this.canAdmin(session.user)) {
      window.location.href = "/app/workbenches";
      return;
    }

    const response = await fetch("/api/audit/events");
    const body = await response.json();
    this.auditEvents = body.events || [];
    this.auditPage = 1;

    const render = () => {
      const search = (document.getElementById("audit-search")?.value || "").trim().toLowerCase();
      const userFilter = document.getElementById("audit-user-filter")?.value || "";
      const actionFilter = document.getElementById("audit-action-filter")?.value || "";
      const filtered = this.auditEvents.filter((event) => {
        const haystack = [event.timestamp, event.login_id, event.action, event.resource, JSON.stringify(event.detail || "")]
          .join(" ")
          .toLowerCase();
        if (search && !haystack.includes(search)) return false;
        if (userFilter && event.login_id !== userFilter) return false;
        if (actionFilter && event.action !== actionFilter) return false;
        return true;
      });
      const totalPages = Math.max(1, Math.ceil(filtered.length / this.auditPageSize));
      this.auditPage = Math.min(this.auditPage, totalPages);
      const start = (this.auditPage - 1) * this.auditPageSize;
      const pageItems = filtered.slice(start, start + this.auditPageSize);

      const tbody = document.getElementById("audit-body");
      if (!tbody) return;
      tbody.innerHTML = "";
      pageItems.forEach((event, index) => {
        const row = document.createElement("tr");
        row.dataset.index = String(start + index);
        row.innerHTML = `<td>${event.timestamp}</td><td>${event.login_id}</td><td><span class="cosmos-badge info">${event.action}</span></td><td>${event.resource}</td><td>${typeof event.detail === "string" ? event.detail : JSON.stringify(event.detail || "")}</td>`;
        row.addEventListener("click", () => this.showAuditDetail(event, row));
        tbody.appendChild(row);
      });

      const summary = document.getElementById("audit-page-summary");
      if (summary) {
        summary.textContent = `Page ${this.auditPage} of ${totalPages} · ${filtered.length} records`;
      }
      document.getElementById("audit-prev")?.toggleAttribute("disabled", this.auditPage <= 1);
      document.getElementById("audit-next")?.toggleAttribute("disabled", this.auditPage >= totalPages);
    };

    const users = [...new Set(this.auditEvents.map((event) => event.login_id))].sort();
    const actions = [...new Set(this.auditEvents.map((event) => event.action))].sort();
    const userSelect = document.getElementById("audit-user-filter");
    if (userSelect) {
      userSelect.innerHTML = `<option value="">All users</option>${users.map((user) => `<option value="${user}">${user}</option>`).join("")}`;
    }
    const actionSelect = document.getElementById("audit-action-filter");
    if (actionSelect) {
      actionSelect.innerHTML = `<option value="">All actions</option>${actions.map((action) => `<option value="${action}">${action}</option>`).join("")}`;
    }

    ["audit-search", "audit-user-filter", "audit-action-filter"].forEach((id) => {
      document.getElementById(id)?.addEventListener("input", () => {
        this.auditPage = 1;
        render();
      });
      document.getElementById(id)?.addEventListener("change", () => {
        this.auditPage = 1;
        render();
      });
    });
    document.getElementById("audit-prev")?.addEventListener("click", () => {
      this.auditPage = Math.max(1, this.auditPage - 1);
      render();
    });
    document.getElementById("audit-next")?.addEventListener("click", () => {
      this.auditPage += 1;
      render();
    });
    document.getElementById("audit-page-size")?.addEventListener("change", (event) => {
      this.auditPageSize = parseInt(event.target.value, 10) || 25;
      this.auditPage = 1;
      render();
    });
    render();
    this.renderAuditDashboard(this.auditEvents);
    this.setStatusBar(`Audit log loaded · ${this.auditEvents.length} events`, "ready", "COSMOS 0.1 · Audit");
  },

  renderAuditDashboard(events) {
    const host = document.getElementById("audit-dashboard");
    if (!host) return;
    const loginEvents = events.filter((event) => String(event.action || "").includes("LOGIN")).length;
    const adminEvents = events.filter((event) => /admin|register|user/i.test(String(event.resource || ""))).length;
    const failedEvents = events.filter((event) => /fail|error|denied/i.test(String(event.detail || "") + String(event.action || ""))).length;
    const critical = events.slice(0, 5);
    host.innerHTML = `
      <div class="audit-stat-grid">
        <div class="audit-stat"><span class="label">Total Events</span><strong>${events.length}</strong></div>
        <div class="audit-stat"><span class="label">Login / Security</span><strong>${loginEvents}</strong></div>
        <div class="audit-stat"><span class="label">Administrative</span><strong>${adminEvents}</strong></div>
        <div class="audit-stat"><span class="label">Failed / Denied</span><strong>${failedEvents}</strong></div>
      </div>
      <div class="audit-recent">
        <h3>Recent Critical Events</h3>
        <ul>${critical.map((event) => `<li><strong>${event.action}</strong> · ${event.login_id} · ${event.resource}</li>`).join("") || "<li>No events yet</li>"}</ul>
      </div>`;
  },

  showAuditDetail(event, row) {
    document.querySelectorAll("#audit-body tr").forEach((node) => node.classList.remove("selected"));
    row?.classList.add("selected");
    const panel = document.getElementById("audit-detail");
    if (!panel) return;
    panel.classList.add("open");
    panel.innerHTML = `
      <h3>Event Detail</h3>
      <dl>
        <dt>Timestamp</dt><dd>${event.timestamp || "—"}</dd>
        <dt>User</dt><dd>${event.login_id || "—"}</dd>
        <dt>Action</dt><dd>${event.action || "—"}</dd>
        <dt>Resource</dt><dd>${event.resource || "—"}</dd>
        <dt>Result</dt><dd>${event.result || "Recorded"}</dd>
        <dt>Metadata</dt><dd><code>${typeof event.detail === "string" ? event.detail : JSON.stringify(event.detail || {}, null, 2)}</code></dd>
      </dl>`;
  },
};
