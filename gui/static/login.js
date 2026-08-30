/**
 * COSMOS 0.1 — Login with infrastructure profile selection
 */

const COSMOS_LOGIN = {
  profiles: [
    {
      id: "ADMIN",
      label: "Administrator",
      infrastructure: "Administration Infrastructure",
      description: "Full COSMOS control — user administration, audit, knowledge governance, all workbenches.",
      icon: "shield",
    },
    {
      id: "ENGINEER",
      label: "Engineer",
      infrastructure: "Engineering Workbench",
      description: "Propulsion, structures, simulation workbenches with knowledge graph and engineering chat.",
      icon: "gear",
    },
    {
      id: "USER",
      label: "User",
      infrastructure: "Standard Workspace",
      description: "Approved engineering workspace access with read-oriented knowledge and workbench modules.",
      icon: "user",
    },
    {
      id: "VIEWER",
      label: "Viewer",
      infrastructure: "Read-Only Infrastructure",
      description: "View approved knowledge, reports, and released engineering outputs without modification rights.",
      icon: "eye",
    },
  ],

  icons: {
    shield: '<svg viewBox="0 0 24 24"><path d="M12 3 4 7v6c0 5 3.5 8 8 8s8-3 8-8V7l-8-4z"/></svg>',
    gear: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M12 2v2M12 20v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M2 12h2M20 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4"/></svg>',
    user: '<svg viewBox="0 0 24 24"><circle cx="12" cy="8" r="3.5"/><path d="M5 20a7 7 0 0 1 14 0"/></svg>',
    eye: '<svg viewBox="0 0 24 24"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="2.5"/></svg>',
  },

  selectedProfile: "ENGINEER",

  init() {
    this.renderProfiles();
    this.restoreRemembered();
    this.bindEvents();
    this.updateProfileUI();
  },

  renderProfiles() {
    const grid = document.getElementById("login-profile-grid");
    if (!grid) return;
    grid.innerHTML = this.profiles
      .map(
        (profile) => `
      <button type="button" class="login-profile-btn${profile.id === this.selectedProfile ? " active" : ""}"
              data-profile="${profile.id}" aria-pressed="${profile.id === this.selectedProfile}">
        <strong>${profile.label}</strong>
        <span>${profile.infrastructure}</span>
      </button>`,
      )
      .join("");
    grid.querySelectorAll(".login-profile-btn").forEach((button) => {
      button.addEventListener("click", () => {
        this.selectedProfile = button.dataset.profile;
        grid.querySelectorAll(".login-profile-btn").forEach((node) => {
          const active = node.dataset.profile === this.selectedProfile;
          node.classList.toggle("active", active);
          node.setAttribute("aria-pressed", active ? "true" : "false");
        });
        this.updateProfileUI();
      });
    });
  },

  currentProfile() {
    return this.profiles.find((item) => item.id === this.selectedProfile) || this.profiles[1];
  },

  updateProfileUI() {
    const profile = this.currentProfile();
    const desc = document.getElementById("login-profile-desc");
    const avatar = document.getElementById("login-avatar-icon");
    if (desc) desc.textContent = profile.description;
    if (avatar) avatar.innerHTML = this.icons[profile.icon] || this.icons.user;
  },

  restoreRemembered() {
    const remembered = localStorage.getItem("cosmos_remember_login_id");
    const rememberedProfile = localStorage.getItem("cosmos_remember_profile");
    if (remembered) {
      const input = document.getElementById("login-id");
      if (input) input.value = remembered;
      const remember = document.getElementById("login-remember");
      if (remember) remember.checked = true;
    }
    if (rememberedProfile && this.profiles.some((item) => item.id === rememberedProfile)) {
      this.selectedProfile = rememberedProfile;
      this.renderProfiles();
    }
    this.updateProfileUI();
  },

  bindEvents() {
    const passwordInput = document.getElementById("password");
    const toggle = document.getElementById("password-toggle");
    toggle?.addEventListener("click", () => {
      const show = passwordInput.type === "password";
      passwordInput.type = show ? "text" : "password";
      toggle.textContent = show ? "Hide" : "Show";
    });

    document.getElementById("login-form")?.addEventListener("submit", (event) => this.handleSubmit(event));
    document.getElementById("login-forgot")?.addEventListener("click", () => {
      const error = document.getElementById("login-error");
      if (error) {
        error.textContent = "Contact your COSMOS administrator to reset credentials.";
      }
    });
  },

  async handleSubmit(event) {
    event.preventDefault();
    const error = document.getElementById("login-error");
    const submit = document.getElementById("login-submit");
    const loginId = document.getElementById("login-id")?.value?.trim() || "";
    const password = document.getElementById("password")?.value || "";
    const remember = document.getElementById("login-remember")?.checked;
    if (error) error.textContent = "";
    if (!loginId || !password) {
      if (error) error.textContent = "Enter login ID and password.";
      return;
    }
    submit.disabled = true;
    submit.textContent = "SIGNING IN…";
    const profile = this.currentProfile();
    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          login_id: loginId,
          password,
          login_profile: profile.id,
        }),
      });
      const body = await response.json();
      if (!response.ok) {
        if (error) error.textContent = body.error || "Login failed.";
        return;
      }
      if (remember) {
        localStorage.setItem("cosmos_remember_login_id", loginId);
        localStorage.setItem("cosmos_remember_profile", profile.id);
      } else {
        localStorage.removeItem("cosmos_remember_login_id");
        localStorage.removeItem("cosmos_remember_profile");
      }
      localStorage.setItem("cosmos_login_profile", profile.id);
      localStorage.setItem("cosmos_infrastructure", body.infrastructure || profile.infrastructure);
      localStorage.setItem("cosmos_login_redirect", body.redirect || "/app/workbenches");
      window.location.href = body.redirect || "/app/workbenches";
    } catch {
      if (error) error.textContent = "Could not reach COSMOS. Check the application and try again.";
    } finally {
      submit.disabled = false;
      submit.textContent = "LOGIN";
    }
  },
};

document.addEventListener("DOMContentLoaded", () => COSMOS_LOGIN.init());
