/* Maharshi Bharadwaj — Knowledge Infrastructure client */

const Maharshi = (() => {
  let conversationId = null;
  let selectedFile = null;
  let sourcesOpen = false;
  let graphEngine = null;
  let canDelete = false;
  let uploadInProgress = false;
  let pollTimer = null;

  function setUploadStatus(text, kind) {
    const el = $("mh-upload-status");
    if (!el) return;
    el.textContent = text;
    el.classList.remove("processing", "ok", "error");
    if (kind) el.classList.add(kind);
  }

  function startPollWhileUploading() {
    stopPollWhileUploading();
    pollTimer = window.setInterval(() => {
      refreshAll({ quiet: true }).catch(() => {});
    }, 2500);
  }

  function stopPollWhileUploading() {
    if (pollTimer) {
      window.clearInterval(pollTimer);
      pollTimer = null;
    }
  }

  async function openSourceViewer(sourceId) {
    try {
      const detail = await apiGet(`/api/sources/${encodeURIComponent(sourceId)}`);
      const modal = $("mh-source-modal");
      const title = $("mh-source-modal-title");
      const meta = $("mh-source-modal-meta");
      const text = $("mh-source-modal-text");
      if (!modal || !title || !meta || !text) return;
      title.textContent = detail.title || detail.filename || sourceId;
      const jobStatus = detail.job?.status || detail.extraction?.job_status || "—";
      meta.innerHTML = [
        `<div><strong>Format:</strong> ${escapeHtml(detail.workspace_format)}</div>`,
        `<div><strong>Size:</strong> ${formatBytes(detail.size_bytes)} · <strong>Text:</strong> ${Number(detail.text_chars || detail.extraction?.text_chars || 0).toLocaleString()} chars</div>`,
        `<div><strong>Job:</strong> ${escapeHtml(jobStatus)} · <strong>Ingested:</strong> ${escapeHtml(detail.ingested_at || "—")}</div>`,
        detail.extraction?.under_recovered ? `<div style="color:#ffd166">Extraction incomplete — use Re-extract if chat answers are weak.</div>` : "",
      ].join("");
      text.textContent = detail.text_content || detail.text_preview || "No extracted text yet.";
      modal.hidden = false;
    } catch (error) {
      appendSystemMessage(String(error.message || error));
    }
  }

  function closeSourceViewer() {
    const modal = $("mh-source-modal");
    if (modal) modal.hidden = true;
  }

  function bindSourceModal() {
    $("mh-source-modal-close")?.addEventListener("click", closeSourceViewer);
    $("mh-source-modal-backdrop")?.addEventListener("click", closeSourceViewer);
    window.addEventListener("keydown", (event) => {
      if (event.key === "Escape") closeSourceViewer();
    });
  }

  async function apiGet(path) {
    let response;
    try {
      response = await fetch(path);
    } catch (error) {
      throw new Error("Could not reach COSMOS — restart the app if this persists.");
    }
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      throw new Error(payload.error || `Request failed (${response.status})`);
    }
    return response.json();
  }

  async function apiPost(path, body) {
    let response;
    try {
      response = await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
    } catch (error) {
      throw new Error("Could not reach COSMOS — restart the app if this persists.");
    }
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      throw new Error(payload.error || `Request failed (${response.status})`);
    }
    return response.json();
  }

  async function apiDelete(path) {
    const response = await fetch(path, { method: "DELETE" });
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      throw new Error(payload.error || `Delete failed (${response.status})`);
    }
    return response.json();
  }

  function $(id) {
    return document.getElementById(id);
  }

  function statusClass(status) {
    if (!status) return "warn";
    const upper = String(status).toUpperCase();
    if (upper.includes("AVAILABLE") || upper.includes("COMPLETE")) return "ok";
    if (upper.includes("FAIL") || upper.includes("BLOCK")) return "fail";
    return "warn";
  }

  function groupSources(sources) {
    const groups = {};
    for (const source of sources) {
      const key = source.project_id || "GLOBAL";
      if (!groups[key]) groups[key] = [];
      groups[key].push(source);
    }
    return Object.keys(groups)
      .sort()
      .map((key) => ({
        label: key,
        items: groups[key].sort((a, b) =>
          (a.title || a.filename || "").localeCompare(b.title || b.filename || ""),
        ),
      }));
  }

  const MAX_UPLOAD_BYTES = 100 * 1024 * 1024;

  function formatBytes(value) {
    if (!value) return "0 B";
    const units = ["B", "KB", "MB", "GB"];
    let size = value;
    let unit = 0;
    while (size >= 1024 && unit < units.length - 1) {
      size /= 1024;
      unit += 1;
    }
    return `${size.toFixed(size >= 10 || unit === 0 ? 0 : 1)} ${units[unit]}`;
  }

  function stageSelectedFile(file) {
    if (!file || uploadInProgress) return;
    const uploadBtn = $("mh-upload-btn");
    const sizeLabel = formatBytes(file.size);
    if (file.size > MAX_UPLOAD_BYTES) {
      selectedFile = null;
      if (uploadBtn) uploadBtn.disabled = true;
      setUploadStatus(`File too large (${sizeLabel}). Maximum upload size is 100 MB.`, "error");
      return;
    }
    selectedFile = file;
    if (uploadBtn) uploadBtn.disabled = false;
    setUploadStatus(`Selected: ${file.name} (${sizeLabel}) — click Upload to process`, "ok");
  }

  function clearSelectedFile() {
    selectedFile = null;
    const fileInput = $("mh-file");
    if (fileInput) fileInput.value = "";
    const uploadBtn = $("mh-upload-btn");
    if (uploadBtn) uploadBtn.disabled = true;
    setUploadStatus("No file selected", "");
  }

  function ingestSummary(payload) {
    const name = payload.source?.filename || payload.job?.source_id || "document";
    const job = payload.job || {};
    const extraction = payload.extraction || {};
    const chars = extraction.text_chars || (extraction.recovered_text || "").length || 0;
    const pages = job.checkpoint?.last_completed_page || extraction.estimated_pages || "?";
    const warnings = extraction.warnings || [];
    const failed = String(job.status || "").toUpperCase().includes("FAIL") || String(job.status || "").toUpperCase().includes("BLOCK");
    const parts = failed
      ? [`Upload failed for ${name}.`, `Job: ${job.status || "unknown"}.`]
      : [`Uploaded ${name} into knowledge infrastructure.`, `Job: ${job.status || "unknown"}.`, `Extracted ${chars.toLocaleString()} characters`];
    if (!failed && pages && pages !== "?") parts.push(`from ~${pages} pages`);
    if (warnings.includes("UNDER_RECOVERED")) {
      parts.push("Extraction looks incomplete — use Re-extract to run full OCR.");
    }
    if (job.error_message) parts.push(String(job.error_message));
    return parts.join(" ");
  }

  async function approveSource(sourceId, label) {
    try {
      const payload = await apiPost(`/api/sources/${encodeURIComponent(sourceId)}/approve`, {});
      appendSystemMessage(`Approved “${label}” — now available in knowledge (${payload.job_status}).`);
      await refreshAll();
    } catch (error) {
      appendSystemMessage(String(error.message || error));
    }
  }

  async function reprocessSource(sourceId, label) {
    if (uploadInProgress) {
      appendSystemMessage("Wait for the current upload to finish first.");
      return;
    }
    if (!window.confirm(`Re-extract “${label}”? Large PDFs can take several minutes.`)) return;
    uploadInProgress = true;
    setUploadStatus(`Re-extracting ${label}…`, "processing");
    appendSystemMessage(`Re-extracting ${label}…`);
    startPollWhileUploading();
    try {
      const payload = await apiPost("/api/reprocess", { source_id: sourceId });
      appendSystemMessage(ingestSummary(payload));
      await refreshAll();
      setUploadStatus(`Re-extracted ${label}`, "ok");
    } catch (error) {
      appendSystemMessage(String(error.message || error));
      setUploadStatus(String(error.message || error), "error");
    } finally {
      uploadInProgress = false;
      stopPollWhileUploading();
    }
  }

  function renderSourcesDrawer(sources) {
    const drawer = $("mh-sources-drawer");
    const count = $("mh-sources-count");
    if (!drawer || !count) return;
    count.textContent = `${sources.length} document${sources.length === 1 ? "" : "s"}`;
    if (!sources.length) {
      drawer.innerHTML = '<div class="mh-empty">No sources uploaded yet.</div>';
      return;
    }
    const groups = groupSources(sources);
    drawer.innerHTML = groups
      .map(
        (group) => `
      <div class="mh-source-group">
        <h3>${escapeHtml(group.label)}</h3>
        ${group.items
          .map(
            (item) => `
          <div class="mh-source-item clickable" data-source-id="${escapeHtml(item.source_id)}">
            <button type="button" class="mh-source-open" data-id="${escapeHtml(item.source_id)}">
              <div>${escapeHtml(item.title || item.filename)}</div>
              <div class="mh-source-meta">${escapeHtml(item.workspace_format)} · ${formatBytes(item.size_bytes)}${
                item.extraction
                  ? ` · ${Number(item.extraction.text_chars || 0).toLocaleString()} chars`
                  : ""
              }${item.extraction?.under_recovered ? " · needs re-extract" : ""}</div>
            </button>
            <div class="mh-btn-row" style="margin:0;">
              ${
                item.needs_approval
                  ? `<button type="button" class="mh-btn mh-approve-source" data-id="${escapeHtml(item.source_id)}" data-label="${escapeHtml(item.title || item.filename)}">Approve</button>`
                  : ""
              }
              ${
                item.can_reextract || item.extraction?.under_recovered
                  ? `<button type="button" class="mh-btn secondary mh-reprocess-source" data-id="${escapeHtml(item.source_id)}" data-label="${escapeHtml(item.title || item.filename)}">Re-extract</button>`
                  : ""
              }
              ${
                canDelete
                  ? `<button type="button" class="mh-btn danger mh-delete-source" data-id="${escapeHtml(item.source_id)}" title="Delete permanently">Delete</button>`
                  : ""
              }
            </div>
          </div>`,
          )
          .join("")}
      </div>`,
      )
      .join("");
    drawer.querySelectorAll(".mh-source-open").forEach((button) => {
      button.addEventListener("click", () => openSourceViewer(button.dataset.id));
    });
    drawer.querySelectorAll(".mh-approve-source").forEach((button) => {
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        approveSource(button.dataset.id, button.dataset.label || button.dataset.id);
      });
    });
    drawer.querySelectorAll(".mh-reprocess-source").forEach((button) => {
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        reprocessSource(button.dataset.id, button.dataset.label || button.dataset.id);
      });
    });
    drawer.querySelectorAll(".mh-delete-source").forEach((button) => {
      button.addEventListener("click", async (event) => {
        event.stopPropagation();
        const sourceId = button.dataset.id;
        const label = button.closest(".mh-source-item")?.querySelector("div div")?.textContent || sourceId;
        if (!window.confirm(`Permanently delete “${label}” from the knowledge infrastructure?`)) return;
        try {
          await apiDelete(`/api/sources/${encodeURIComponent(sourceId)}`);
          await refreshAll();
          appendSystemMessage(`Removed source ${label}.`);
        } catch (error) {
          appendSystemMessage(String(error.message || error));
        }
      });
    });
  }

  function renderJobsTable(sources, jobs) {
    const tbody = $("mh-sources-jobs-body");
    if (!tbody) return;
    const jobBySource = {};
    for (const job of jobs) jobBySource[job.source_id] = job;
    if (!sources.length) {
      tbody.innerHTML = '<tr><td colspan="5" class="mh-empty">No sources yet.</td></tr>';
      return;
    }
    tbody.innerHTML = sources
      .map((source) => {
        const job = jobBySource[source.source_id];
        const jobStatus = source.job_status || (job ? job.status : "—");
        const chars = source.extraction ? Number(source.extraction.text_chars || 0).toLocaleString() : "0";
        const approve = source.needs_approval
          ? `<button type="button" class="mh-btn mh-approve-job" data-id="${escapeHtml(source.source_id)}" data-label="${escapeHtml(source.title || source.filename)}">Approve</button>`
          : "";
        const reextract =
          source.can_reextract || source.extraction?.under_recovered
            ? `<button type="button" class="mh-btn secondary mh-reprocess-job" data-id="${escapeHtml(source.source_id)}" data-label="${escapeHtml(source.title || source.filename)}">Re-extract</button>`
            : "";
        return `<tr class="mh-source-row" data-source-id="${escapeHtml(source.source_id)}">
          <td><button type="button" class="mh-source-open mh-link-name" data-id="${escapeHtml(source.source_id)}">${escapeHtml(source.title || source.filename)}</button></td>
          <td>${escapeHtml(source.workspace_format)}</td>
          <td>${chars}</td>
          <td><span class="mh-status-pill ${statusClass(jobStatus)}">${escapeHtml(jobStatus)}</span></td>
          <td><div class="mh-btn-row" style="margin:0;">${approve}${reextract}</div></td>
        </tr>`;
      })
      .join("");
    tbody.querySelectorAll(".mh-approve-job").forEach((button) => {
      button.addEventListener("click", () => approveSource(button.dataset.id, button.dataset.label || button.dataset.id));
    });
    tbody.querySelectorAll(".mh-link-name").forEach((button) => {
      button.addEventListener("click", () => openSourceViewer(button.dataset.id));
    });
    tbody.querySelectorAll(".mh-reprocess-job").forEach((button) => {
      button.addEventListener("click", () => reprocessSource(button.dataset.id, button.dataset.label || button.dataset.id));
    });
  }

  function renderReview(items) {
    const tbody = $("mh-review-body");
    if (!tbody) return;
    if (!items.length) {
      tbody.innerHTML = '<tr><td colspan="3" class="mh-empty">No documents awaiting approval.</td></tr>';
      return;
    }
    tbody.innerHTML = items
      .map(
        (item) => `<tr>
        <td>${escapeHtml(item.title || item.source_id)}</td>
        <td>${escapeHtml(item.expression)}</td>
        <td><button type="button" class="mh-btn mh-approve-doc" data-source="${escapeHtml(item.source_id)}" data-label="${escapeHtml(item.title || item.source_id)}">Approve document</button></td>
      </tr>`,
      )
      .join("");
    tbody.querySelectorAll(".mh-approve-doc").forEach((button) => {
      button.addEventListener("click", () => approveSource(button.dataset.source, button.dataset.label || button.dataset.source));
    });
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function appendSystemMessage(text) {
    const container = $("mh-chat-messages");
    if (!container) return;
    const node = document.createElement("div");
    node.className = "mh-msg system";
    node.textContent = text;
    container.appendChild(node);
    container.scrollTop = container.scrollHeight;
  }

  function renderMessages(messages) {
    const container = $("mh-chat-messages");
    if (!container) return;
    container.innerHTML = "";
    if (!messages.length) {
      appendSystemMessage("Ask about ingested sources or approved engineering knowledge.");
      return;
    }
    for (const message of messages) {
      const node = document.createElement("div");
      node.className = `mh-msg ${message.role === "user" ? "user" : "assistant"}`;
      node.textContent = message.content;
      if (message.role === "assistant" && message.validation_state) {
        const badge = document.createElement("div");
        badge.className = "mh-evidence";
        badge.innerHTML = `<span>${escapeHtml(message.validation_state)}</span>`;
        node.appendChild(badge);
      }
      container.appendChild(node);
    }
    container.scrollTop = container.scrollHeight;
  }

  async function refreshAll(options = {}) {
    const quiet = options.quiet === true;
    const healthEl = $("mh-health");
    try {
      const [health, sourcesPayload, jobsPayload, reviewPayload, graphPayload] = await Promise.all([
        apiGet("/api/health"),
        apiGet("/api/sources"),
        apiGet("/api/jobs"),
        apiGet("/api/review"),
        apiGet("/api/graph"),
      ]);
      if (healthEl) {
        const pending = health.jobs_pending_review || 0;
        healthEl.textContent = `${health.source_count || 0} sources · ${health.jobs_available || 0} ready · ${pending} pending`;
      }
      const sources = sourcesPayload.sources || [];
      renderSourcesDrawer(sources);
      renderJobsTable(sources, jobsPayload.jobs || []);
      renderReview(reviewPayload.items || []);
      if (graphEngine) graphEngine.load(graphPayload);
    } catch (error) {
      if (healthEl) healthEl.textContent = "connection error";
      if (!quiet) appendSystemMessage(String(error.message || error));
      throw error;
    }
  }

  async function addDocument(file) {
    const uploadFile = file || selectedFile;
    if (!uploadFile || uploadInProgress) {
      if (!uploadFile) setUploadStatus("Choose a file first, then click Upload.", "error");
      return;
    }
    uploadInProgress = true;
    const dropzone = $("mh-dropzone");
    const uploadBtn = $("mh-upload-btn");
    if (uploadBtn) uploadBtn.disabled = true;
    dropzone?.classList.add("over");
    const isPdf = (uploadFile.name || "").toLowerCase().endsWith(".pdf");
    setUploadStatus(
      isPdf ? `Uploading ${uploadFile.name}… OCR may take 1–3 min` : `Uploading ${uploadFile.name}…`,
      "processing",
    );
    startPollWhileUploading();
    appendSystemMessage(
      isPdf
        ? `Processing ${uploadFile.name}. Large PDFs run OCR in the background.`
        : `Processing ${uploadFile.name}.`,
    );
    try {
      const data = new FormData();
      data.append("file", uploadFile, uploadFile.name);
      data.append("rights_status", $("mh-rights")?.value || "INTERNAL");
      let response;
      try {
        response = await fetch("/api/ingest", { method: "POST", body: data });
      } catch {
        throw new Error("Could not reach COSMOS — restart the app if this persists.");
      }
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.error || payload.job?.error_message || "Upload failed");
      const uploadedName = payload.source?.filename || uploadFile.name;
      const jobFailed = String(payload.job?.status || "").toUpperCase().includes("FAIL");
      clearSelectedFile();
      if (jobFailed) {
        setUploadStatus(`Upload failed: ${payload.job?.error_message || "processing error"}`, "error");
      } else {
        setUploadStatus(`Uploaded ${uploadedName}`, "ok");
      }
      appendSystemMessage(ingestSummary(payload));
      if (!jobFailed) {
        sourcesOpen = true;
        $("mh-sources-drawer")?.classList.add("open");
        await refreshAll();
        if (payload.source?.source_id) {
          await openSourceViewer(payload.source.source_id);
        }
      } else {
        await refreshAll();
      }
    } catch (error) {
      const message = String(error.message || error);
      setUploadStatus(message.includes("COSMOS") ? message : message || "Upload failed", "error");
      appendSystemMessage(message);
    } finally {
      uploadInProgress = false;
      dropzone?.classList.remove("over");
      stopPollWhileUploading();
      if (selectedFile && $("mh-upload-btn")) {
        $("mh-upload-btn").disabled = false;
      }
    }
  }

  async function sendChat() {
    const input = $("mh-chat-input");
    const text = input?.value?.trim();
    if (!text) return;
    const askBtn = $("mh-ask-btn");
    if (askBtn) askBtn.disabled = true;
    input.value = "";
    const container = $("mh-chat-messages");
    const pending = document.createElement("div");
    pending.className = "mh-msg user";
    pending.textContent = text;
    container.appendChild(pending);
    const thinking = document.createElement("div");
    thinking.className = "mh-msg assistant";
    thinking.textContent = "Thinking…";
    container.appendChild(thinking);
    container.scrollTop = container.scrollHeight;
    try {
      const payload = await apiPost("/api/chat", {
        conversation_id: conversationId,
        message: text,
      });
      conversationId = payload.conversation_id;
      renderMessages(payload.messages || []);
      if (payload.evidence?.length) {
        const last = container.querySelector(".mh-msg.assistant:last-child");
        if (last) {
          const evidence = document.createElement("div");
          evidence.className = "mh-evidence";
          evidence.innerHTML = payload.evidence
            .slice(0, 6)
            .map((item) => `<span>${escapeHtml(String(item).slice(0, 80))}</span>`)
            .join("");
          last.appendChild(evidence);
        }
      }
    } catch (error) {
      thinking.textContent = String(error.message || error);
    } finally {
      if (askBtn) askBtn.disabled = false;
      input?.focus();
    }
  }

  async function newConversation() {
    conversationId = null;
    renderMessages([]);
    appendSystemMessage("New conversation started.");
  }

  function bindUpload() {
    const dropzone = $("mh-dropzone");
    const fileInput = $("mh-file");
    const chooseBtn = $("mh-choose-btn");
    const uploadBtn = $("mh-upload-btn");

    chooseBtn?.addEventListener("click", (event) => {
      event.stopPropagation();
      if (!uploadInProgress) fileInput?.click();
    });

    uploadBtn?.addEventListener("click", (event) => {
      event.stopPropagation();
      addDocument();
    });

    dropzone?.addEventListener("click", (event) => {
      if (event.target.closest(".mh-btn")) return;
      if (!uploadInProgress) fileInput?.click();
    });

    fileInput?.addEventListener("change", () => stageSelectedFile(fileInput.files?.[0]));

    dropzone?.addEventListener("dragover", (event) => {
      event.preventDefault();
      dropzone.classList.add("over");
    });
    dropzone?.addEventListener("dragleave", () => dropzone.classList.remove("over"));
    dropzone?.addEventListener("drop", (event) => {
      event.preventDefault();
      dropzone.classList.remove("over");
      stageSelectedFile(event.dataTransfer.files?.[0]);
    });
  }

  function bindSourcesBar() {
    $("mh-sources-toggle")?.addEventListener("click", () => {
      sourcesOpen = !sourcesOpen;
      $("mh-sources-drawer")?.classList.toggle("open", sourcesOpen);
    });
  }

  function bindChat() {
    $("mh-ask-btn")?.addEventListener("click", sendChat);
    $("mh-new-conv-btn")?.addEventListener("click", newConversation);
    $("mh-chat-input")?.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendChat();
      }
    });
  }

  function bindPanels() {
    $("mh-refresh-btn")?.addEventListener("click", async () => {
      const btn = $("mh-refresh-btn");
      if (btn) {
        btn.disabled = true;
        btn.textContent = "Refreshing…";
      }
      try {
        await refreshAll();
        appendSystemMessage("Workspace refreshed.");
      } catch (error) {
        appendSystemMessage(String(error.message || error));
      } finally {
        if (btn) {
          btn.disabled = false;
          btn.textContent = "Refresh";
        }
      }
    });
    $("mh-backup-btn")?.addEventListener("click", async () => {
      const btn = $("mh-backup-btn");
      if (btn) btn.disabled = true;
      try {
        const payload = await apiPost("/api/backup", {});
        appendSystemMessage(`Backup saved: ${payload.filename || payload.archive}`);
      } catch (error) {
        appendSystemMessage(String(error.message || error));
      } finally {
        if (btn) btn.disabled = false;
      }
    });
  }

  class ForceGraph {
    constructor(canvas) {
      this.canvas = canvas;
      this.ctx = canvas.getContext("2d");
      this.nodes = [];
      this.edges = [];
      this.nodeMap = new Map();
      this.dragged = null;
      this.hovered = null;
      this.tooltip = $("mh-tooltip");
      this.detail = $("mh-node-detail");
      this.detailTitle = $("mh-detail-title");
      this.detailBody = $("mh-detail-body");
      this.running = true;
      this.resizeObserver = new ResizeObserver(() => this.resize());
      this.resizeObserver.observe(canvas.parentElement);
      this.bindEvents();
      this.loop();
    }

    resize() {
      const rect = this.canvas.parentElement.getBoundingClientRect();
      const ratio = window.devicePixelRatio || 1;
      this.width = rect.width;
      this.height = rect.height;
      this.canvas.width = Math.floor(rect.width * ratio);
      this.canvas.height = Math.floor(rect.height * ratio);
      this.canvas.style.width = `${rect.width}px`;
      this.canvas.style.height = `${rect.height}px`;
      this.ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    }

    load(payload) {
      const existing = new Map(this.nodes.map((node) => [node.id, node]));
      this.nodes = (payload.nodes || []).map((raw, index) => {
        const prior = existing.get(raw.id);
        const angle = (index / Math.max(1, payload.nodes.length)) * Math.PI * 2;
        const radius = Math.min(this.width, this.height) * 0.28 || 120;
        return {
          id: raw.id,
          label: raw.label || raw.id,
          kind: raw.kind || "document",
          summary: raw.summary || "",
          keywords: raw.keywords || [],
          x: prior?.x ?? this.width / 2 + Math.cos(angle) * radius,
          y: prior?.y ?? this.height / 2 + Math.sin(angle) * radius,
          vx: prior?.vx ?? 0,
          vy: prior?.vy ?? 0,
          fixed: false,
        };
      });
      this.nodeMap = new Map(this.nodes.map((node) => [node.id, node]));
      this.edges = (payload.edges || [])
        .map((edge) => ({
          source: this.nodeMap.get(edge.source),
          target: this.nodeMap.get(edge.target),
          relationship: edge.relationship,
          kind: edge.kind,
        }))
        .filter((edge) => edge.source && edge.target);
      const badgeNodes = $("mh-graph-node-count");
      const badgeEdges = $("mh-graph-edge-count");
      if (badgeNodes) badgeNodes.textContent = `${this.nodes.length} nodes`;
      if (badgeEdges) badgeEdges.textContent = `${this.edges.length} links`;
    }

    bindEvents() {
      this.canvas.addEventListener("mousemove", (event) => this.onPointerMove(event));
      this.canvas.addEventListener("mousedown", (event) => this.onPointerDown(event));
      window.addEventListener("mouseup", () => this.onPointerUp());
      this.canvas.addEventListener("click", (event) => this.onClick(event));
      $("mh-detail-close")?.addEventListener("click", () => this.detail?.classList.remove("open"));
    }

    nodeAt(x, y) {
      for (let index = this.nodes.length - 1; index >= 0; index -= 1) {
        const node = this.nodes[index];
        const radius = this.nodeRadius(node);
        const dx = x - node.x;
        const dy = y - node.y;
        if (dx * dx + dy * dy <= radius * radius) return node;
      }
      return null;
    }

    nodeRadius(node) {
      return node.kind === "document" ? 10 + Math.min(8, (node.keywords?.length || 0)) : 7;
    }

    pointer(event) {
      const rect = this.canvas.getBoundingClientRect();
      return { x: event.clientX - rect.left, y: event.clientY - rect.top };
    }

    onPointerDown(event) {
      const point = this.pointer(event);
      const node = this.nodeAt(point.x, point.y);
      if (!node) return;
      this.dragged = node;
      node.fixed = true;
      this.canvas.classList.add("dragging");
    }

    onPointerUp() {
      if (this.dragged) this.dragged.fixed = false;
      this.dragged = null;
      this.canvas.classList.remove("dragging");
    }

    onPointerMove(event) {
      const point = this.pointer(event);
      if (this.dragged) {
        this.dragged.x = point.x;
        this.dragged.y = point.y;
        this.dragged.vx = 0;
        this.dragged.vy = 0;
        return;
      }
      const node = this.nodeAt(point.x, point.y);
      this.hovered = node;
      if (node && this.tooltip) {
        this.tooltip.classList.add("visible");
        this.tooltip.style.left = `${event.clientX + 14}px`;
        this.tooltip.style.top = `${event.clientY + 14}px`;
        this.tooltip.innerHTML = `
          <div class="kind">${escapeHtml(node.kind)}</div>
          <div class="title">${escapeHtml(node.label)}</div>
          <div>${escapeHtml(node.summary || "Connected knowledge node")}</div>`;
      } else if (this.tooltip) {
        this.tooltip.classList.remove("visible");
      }
    }

    onClick(event) {
      const point = this.pointer(event);
      const node = this.nodeAt(point.x, point.y);
      if (!node || !this.detail) return;
      this.detail.classList.add("open");
      if (this.detailTitle) this.detailTitle.textContent = node.label;
      if (this.detailBody) {
        const keywords = (node.keywords || []).slice(0, 8).join(", ");
        this.detailBody.textContent = [node.summary, keywords ? `Keywords: ${keywords}` : ""]
          .filter(Boolean)
          .join("\n\n");
      }
    }

    simulate() {
      const repulsion = 420;
      const spring = 0.018;
      const damping = 0.86;
      const centerPull = 0.0025;
      const cx = this.width / 2;
      const cy = this.height / 2;

      for (let i = 0; i < this.nodes.length; i += 1) {
        for (let j = i + 1; j < this.nodes.length; j += 1) {
          const a = this.nodes[i];
          const b = this.nodes[j];
          let dx = b.x - a.x;
          let dy = b.y - a.y;
          let dist = Math.hypot(dx, dy) || 0.01;
          const force = repulsion / (dist * dist);
          dx = (dx / dist) * force;
          dy = (dy / dist) * force;
          if (!a.fixed) {
            a.vx -= dx;
            a.vy -= dy;
          }
          if (!b.fixed) {
            b.vx += dx;
            b.vy += dy;
          }
        }
      }

      for (const edge of this.edges) {
        const a = edge.source;
        const b = edge.target;
        let dx = b.x - a.x;
        let dy = b.y - a.y;
        const dist = Math.hypot(dx, dy) || 0.01;
        const rest = 90;
        const force = (dist - rest) * spring;
        dx = (dx / dist) * force;
        dy = (dy / dist) * force;
        if (!a.fixed) {
          a.vx += dx;
          a.vy += dy;
        }
        if (!b.fixed) {
          b.vx -= dx;
          b.vy -= dy;
        }
      }

      for (const node of this.nodes) {
        if (node.fixed) continue;
        node.vx += (cx - node.x) * centerPull;
        node.vy += (cy - node.y) * centerPull;
        node.vx *= damping;
        node.vy *= damping;
        node.x += node.vx;
        node.y += node.vy;
        node.x = Math.max(24, Math.min(this.width - 24, node.x));
        node.y = Math.max(24, Math.min(this.height - 24, node.y));
      }
    }

    draw() {
      const ctx = this.ctx;
      ctx.clearRect(0, 0, this.width, this.height);

      for (const edge of this.edges) {
        const highlighted =
          this.hovered &&
          (edge.source === this.hovered || edge.target === this.hovered || this.dragged === edge.source || this.dragged === edge.target);
        ctx.beginPath();
        ctx.moveTo(edge.source.x, edge.source.y);
        ctx.lineTo(edge.target.x, edge.target.y);
        ctx.strokeStyle = highlighted ? "rgba(255, 209, 102, 0.55)" : "rgba(76, 201, 240, 0.18)";
        ctx.lineWidth = highlighted ? 1.6 : 1;
        ctx.stroke();
      }

      for (const node of this.nodes) {
        const radius = this.nodeRadius(node);
        const active = node === this.hovered || node === this.dragged;
        const gradient = ctx.createRadialGradient(node.x, node.y, 1, node.x, node.y, radius * 2.2);
        if (node.kind === "document") {
          gradient.addColorStop(0, active ? "#7ee787" : "#4cc9f0");
          gradient.addColorStop(1, "rgba(15, 138, 166, 0.15)");
        } else {
          gradient.addColorStop(0, active ? "#ffd166" : "#ff8a00");
          gradient.addColorStop(1, "rgba(255, 138, 0, 0.12)");
        }
        ctx.beginPath();
        ctx.arc(node.x, node.y, radius, 0, Math.PI * 2);
        ctx.fillStyle = gradient;
        ctx.fill();
        if (active) {
          ctx.strokeStyle = "rgba(255, 255, 255, 0.65)";
          ctx.lineWidth = 1.5;
          ctx.stroke();
        }
        if (radius >= 11 || active) {
          ctx.fillStyle = "rgba(245, 247, 251, 0.92)";
          ctx.font = "10px Segoe UI, sans-serif";
          ctx.textAlign = "center";
          ctx.fillText(node.label.slice(0, 22), node.x, node.y + radius + 12);
        }
      }
    }

    loop() {
      if (!this.running) return;
      if (this.nodes.length) this.simulate();
      this.draw();
      requestAnimationFrame(() => this.loop());
    }
  }

  async function init() {
    sourcesOpen = true;
    bindUpload();
    bindSourcesBar();
    bindChat();
    bindPanels();
    bindSourceModal();
    const canvas = $("mh-graph-canvas");
    if (canvas) graphEngine = new ForceGraph(canvas);
    try {
      const session = await fetch("/api/auth/session").then((response) => response.json());
      const role = session?.user?.role || "";
      canDelete = role === "ADMIN" || role === "APPROVER";
    } catch {
      canDelete = false;
    }
    try {
      await refreshAll();
    } catch {
      setUploadStatus("Could not reach knowledge API — restart COSMOS", "error");
    }
  }

  return { init };
})();
