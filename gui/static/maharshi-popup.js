/**
 * Maharshi Bharadwaj — draggable dock + Knowledge pop-up.
 */
(function maharshiPopupModule() {
  let mounted = false;
  let maximized = false;
  const DOCK_STORAGE = "cosmos_maharshi_dock";

  function $(id) {
    return document.getElementById(id);
  }

  function readDockState() {
    try {
      return JSON.parse(localStorage.getItem(DOCK_STORAGE) || "{}");
    } catch {
      return {};
    }
  }

  function writeDockState(state) {
    localStorage.setItem(DOCK_STORAGE, JSON.stringify(state));
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
      window.location.href = "/app/workbench/knowledge";
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

  function applyDockGeometry(dock, state) {
    if (!dock) return;
    const size = Math.max(44, Math.min(120, Number(state.size) || 56));
    dock.style.width = `${size}px`;
    dock.style.setProperty("--maharshi-dock-size", `${size}px`);
    if (Number.isFinite(state.left) && Number.isFinite(state.top)) {
      dock.style.left = `${state.left}px`;
      dock.style.top = `${state.top}px`;
      dock.style.bottom = "auto";
      dock.style.right = "auto";
    }
  }

  function bindDockInteractions(dock) {
    if (!dock || dock.dataset.bound === "1") return;
    dock.dataset.bound = "1";

    let dragging = false;
    let dragOffsetX = 0;
    let dragOffsetY = 0;
    let clickTimer = null;
    let movedDuringDrag = false;

    const persist = () => {
      const rect = dock.getBoundingClientRect();
      const size = parseFloat(dock.style.width) || dock.offsetWidth;
      writeDockState({ left: rect.left, top: rect.top, size });
    };

    dock.addEventListener("pointerdown", (event) => {
      if (event.target.closest(".maharshi-resize-handle")) return;
      if (event.pointerType === "mouse" && event.button !== 0) return;
      dragging = true;
      movedDuringDrag = false;
      const rect = dock.getBoundingClientRect();
      dragOffsetX = event.clientX - rect.left;
      dragOffsetY = event.clientY - rect.top;
      dock.setPointerCapture(event.pointerId);
      dock.classList.add("dragging");
      event.preventDefault();
    });

    dock.addEventListener("pointermove", (event) => {
      if (!dragging) return;
      movedDuringDrag = true;
      const maxLeft = window.innerWidth - dock.offsetWidth - 8;
      const maxTop = window.innerHeight - dock.offsetHeight - 8;
      const left = Math.max(8, Math.min(maxLeft, event.clientX - dragOffsetX));
      const top = Math.max(8, Math.min(maxTop, event.clientY - dragOffsetY));
      dock.style.left = `${left}px`;
      dock.style.top = `${top}px`;
      dock.style.bottom = "auto";
      dock.style.right = "auto";
    });

    const endDrag = (event) => {
      if (!dragging) return;
      dragging = false;
      dock.classList.remove("dragging");
      try {
        dock.releasePointerCapture(event.pointerId);
      } catch {
        /* ignore */
      }
      persist();
    };
    dock.addEventListener("pointerup", endDrag);
    dock.addEventListener("pointercancel", endDrag);

    dock.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      if (movedDuringDrag) return;
      if (clickTimer) {
        clearTimeout(clickTimer);
        clickTimer = null;
        return;
      }
      clickTimer = setTimeout(() => {
        clickTimer = null;
        COSMOS.openMaharshiPopup();
      }, 220);
    });

    dock.addEventListener("dblclick", (event) => {
      event.preventDefault();
      event.stopPropagation();
      if (clickTimer) {
        clearTimeout(clickTimer);
        clickTimer = null;
      }
      window.location.href = "/app/workbench/knowledge";
    });

    const handle = dock.querySelector(".maharshi-resize-handle");
    handle?.addEventListener("pointerdown", (event) => {
      event.stopPropagation();
      event.preventDefault();
      const startX = event.clientX;
      const startSize = dock.offsetWidth;
      const onMove = (moveEvent) => {
        const next = Math.max(44, Math.min(120, startSize + (moveEvent.clientX - startX)));
        dock.style.width = `${next}px`;
        dock.style.setProperty("--maharshi-dock-size", `${next}px`);
      };
      const onUp = () => {
        window.removeEventListener("pointermove", onMove);
        window.removeEventListener("pointerup", onUp);
        persist();
      };
      window.addEventListener("pointermove", onMove);
      window.addEventListener("pointerup", onUp);
    });

    dock.addEventListener("wheel", (event) => {
      if (!event.shiftKey) return;
      event.preventDefault();
      const current = dock.offsetWidth;
      const next = Math.max(44, Math.min(120, current + (event.deltaY > 0 ? -4 : 4)));
      dock.style.width = `${next}px`;
      dock.style.setProperty("--maharshi-dock-size", `${next}px`);
      persist();
    }, { passive: false });
  }

  COSMOS.mountMaharshiDock = function mountMaharshiDock(options = {}) {
    if ($("maharshi-module")) {
      bindDockInteractions($("maharshi-module"));
      return;
    }
    const dock = document.createElement("button");
    dock.type = "button";
    dock.className = "maharshi-module maharshi-dock";
    dock.id = "maharshi-module";
    dock.title = "Maharshi Bharadwaj — click for pop-up, double-click for Knowledge workbench. Drag to move; Shift+wheel or corner handle to resize.";
    dock.innerHTML = `
      <img src="/assets/maharshi_bharadwaj.png" alt="Maharshi Bharadwaj" draggable="false" />
      <span>Maharshi</span>
      <span class="maharshi-resize-handle" aria-hidden="true"></span>`;
    document.body.appendChild(dock);
    applyDockGeometry(dock, readDockState());
    bindDockInteractions(dock);
    if (options.page === "hub") {
      dock.classList.add("maharshi-dock-hub");
    }
  };

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
    const dock = document.getElementById("maharshi-module");
    if (!dock || dock.dataset.popupBound === "1") return;
    dock.dataset.popupBound = "1";
    bindDockInteractions(dock);
  };
})();
