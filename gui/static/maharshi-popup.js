/**
 * Maharshi Bharadwaj — global Knowledge pop-up (graph + chat only).
 */
(function maharshiPopupModule() {
  let mounted = false;
  let maximized = false;

  function $(id) {
    return document.getElementById(id);
  }

  function mountPopup() {
    if (mounted || $("maharshi-popup-window")) {
      mounted = true;
      return;
    }
    const node = document.createElement("div");
    node.id = "maharshi-popup-window";
    node.className = "cosmos-window";
    node.setAttribute("aria-hidden", "true");
    node.innerHTML = `
      <div class="cosmos-window-chrome">
        <div class="cosmos-window-title">
          <img src="/assets/maharshi_bharadwaj.png" alt="" class="cosmos-window-icon" />
          <span>Maharshi Bharadwaj — Knowledge</span>
        </div>
        <div class="cosmos-window-controls">
          <button type="button" class="cosmos-window-btn" id="maharshi-popup-min" title="Minimize" aria-label="Minimize">—</button>
          <button type="button" class="cosmos-window-btn" id="maharshi-popup-max" title="Maximize" aria-label="Maximize">□</button>
          <button type="button" class="cosmos-window-btn close" id="maharshi-popup-close" title="Close" aria-label="Close">✕</button>
        </div>
      </div>
      <div class="cosmos-window-body">
        <iframe id="maharshi-popup-frame" title="Maharshi Bharadwaj Knowledge" src="about:blank"></iframe>
      </div>
      <div class="cosmos-window-foot">
        <button type="button" class="cosmos-btn secondary" id="maharshi-popup-open-full">Open Knowledge Workbench</button>
      </div>`;
    document.body.appendChild(node);

    $("maharshi-popup-close")?.addEventListener("click", () => COSMOS.closeMaharshiPopup());
    $("maharshi-popup-min")?.addEventListener("click", () => {
      node.classList.toggle("minimized");
    });
    $("maharshi-popup-max")?.addEventListener("click", () => {
      maximized = !maximized;
      node.classList.toggle("maximized", maximized);
      $("maharshi-popup-max").textContent = maximized ? "❐" : "□";
    });
    $("maharshi-popup-open-full")?.addEventListener("click", () => {
      COSMOS.closeMaharshiPopup();
      const page = COSMOS.hubPageFromUrl?.() || 1;
      window.location.href = COSMOS.workbenchUrl("/app/workbench/knowledge", page);
    });
    node.addEventListener("click", (event) => {
      if (event.target === node) COSMOS.closeMaharshiPopup();
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && node.classList.contains("open")) {
        COSMOS.closeMaharshiPopup();
      }
    });
    mounted = true;
  }

  COSMOS.openMaharshiPopup = function openMaharshiPopup() {
    mountPopup();
    const win = $("maharshi-popup-window");
    const frame = $("maharshi-popup-frame");
    if (!win || !frame) return;
    win.classList.add("open");
    win.classList.remove("minimized");
    win.setAttribute("aria-hidden", "false");
    if (!frame.src || frame.src === "about:blank") {
      frame.src = "/app/workbench/knowledge?view=compact&embed=1";
    }
    if (typeof COSMOS.notify === "function") {
      COSMOS.notify("Knowledge pop-up opened", "info", "Graph and chat only");
    }
  };

  COSMOS.closeMaharshiPopup = function closeMaharshiPopup() {
    const win = $("maharshi-popup-window");
    if (!win) return;
    win.classList.remove("open", "maximized", "minimized");
    win.setAttribute("aria-hidden", "true");
    maximized = false;
  };

  COSMOS.bindMaharshiPopupTrigger = function bindMaharshiPopupTrigger() {
    document.getElementById("maharshi-module")?.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      COSMOS.openMaharshiPopup();
    });
  };
})();
