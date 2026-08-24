const COSMOS = {
  hubPage: 1,
  hubPages: 3,
  touchStartX: 0,
  touchStartY: 0,
  swipeLocked: false,
  workbenchCatalog: null,

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
    const name = document.getElementById("meta-name");
    const designation = document.getElementById("meta-designation");
    const team = document.getElementById("meta-team");
    if (badge) badge.textContent = user.display_name;
    if (name) name.textContent = user.display_name;
    if (designation) designation.textContent = `${user.designation} · ${user.employee_id}`;
    if (team) team.textContent = user.team;
    if (avatar) {
      if (user.profile_photo_url) {
        avatar.style.backgroundImage = `url('${user.profile_photo_url}?t=${Date.now()}')`;
        avatar.classList.add("has-photo");
      } else {
        avatar.style.backgroundImage = "";
        avatar.classList.remove("has-photo");
      }
    }
    const status = document.getElementById("status-bar");
    if (status) {
      status.textContent = `Signed in as ${user.login_id} (${user.role}) — COSMOS 0.1`;
    }
  },

  bindProfileTriggers(user) {
    const open = (focus) => this.openProfileModal(user, focus);
    document.getElementById("avatar")?.addEventListener("click", () => open("photo"));
    document.getElementById("meta-name")?.addEventListener("click", () => open("display_name"));
    document.getElementById("meta-designation")?.addEventListener("click", () => open("designation"));
    document.getElementById("meta-team")?.addEventListener("click", () => open("team"));
    document.getElementById("user-badge")?.addEventListener("click", () => open("role"));
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
    document.getElementById("maharshi-module")?.addEventListener("click", () => {
      const page = this.hubPageFromUrl();
      window.location.href = this.workbenchUrl("/app/workbench/knowledge", page);
    });
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

  async initShell() {
    const session = await this.session();
    if (!session) return null;
    this.applyHeader(session.user);
    this.bindProfileTriggers(session.user);
    this.bindLogout();
    this.bindMaharshi();
    this.bindProfileModalActions();
    this.bindSidebarTooltips();
    return session;
  },

  renderWorkbenchCards(items, page) {
    const track = document.getElementById("workbench-track");
    if (!track) return;
    track.innerHTML = "";
    track.dataset.page = String(page);
    items.forEach((item) => {
      const card = document.createElement("button");
      card.type = "button";
      const blendClass = ["structures", "pid", "rocket-staging"].includes(item.workbench_id) ? "art-light" : "art-dark";
      card.className = `workbench-card ${blendClass}`;
      const art = this.workbenchArt(item.workbench_id);
      card.innerHTML = `
        <div class="workbench-art-wrap">
          <img class="workbench-art-img" src="${art}" alt="${item.title}" loading="lazy"
               onerror="this.onerror=null;this.src='${this.workbenchArtFallback(item.workbench_id)}';" />
          <div class="workbench-art-vignette"></div>
        </div>
        <h3>${item.title.toUpperCase()}</h3>`;
      card.onclick = () => {
        this.rememberHubPage(page);
        window.location.href = this.workbenchUrl(item.route, page);
      };
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
    if (label) label.textContent = `Workbench Page ${page} / ${totalPages}`;
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
      if (event.pointerType === "mouse" && event.button !== 0) return;
      viewport.setPointerCapture(event.pointerId);
      onStart(event.clientX, event.clientY);
    });
    viewport.addEventListener("pointerup", (event) => {
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
    const session = await this.initShell();
    if (!session) return;
    this.hubPage = this.hubPageFromUrl();
    this.rememberHubPage(this.hubPage);
    this.workbenchCatalog = await fetch("/api/workbenches").then((r) => r.json());
    this.hubPages = this.workbenchCatalog.pages.length;
    await this.goToHubPage(this.hubPage, { animate: false });
    this.bindCarouselControls(this.hubPages);
  },

  async initAdminPanel() {
    const session = await this.initShell();
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
      tbody.innerHTML = "";
      (body.users || []).forEach((user) => {
        const row = document.createElement("tr");
        row.innerHTML = `<td>${user.login_id}</td><td>${user.display_name}</td><td>${user.role}</td><td>${user.team}</td><td>${user.employee_id}</td>`;
        tbody.appendChild(row);
      });
    };
    await loadUsers();
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
    const session = await this.initShell();
    if (!session) return;
    this.hubPage = this.hubPageFromUrl();
    const back = document.getElementById("back-link");
    if (back) back.href = this.hubUrl(this.hubPage);

    const detail = await fetch(`/api/workbenches/${workbenchId}`).then((r) => r.json());
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
          alert(`${name} is registered. Solver integration is routed through governed backend APIs.`);
        };
        modules.appendChild(button);
      });
    }
  },
};
