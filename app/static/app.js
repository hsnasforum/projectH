    const transcriptEl = document.getElementById("transcript");
    const requestForm = document.getElementById("request-form");
    const sessionListEl = document.getElementById("session-list");
    const errorBox = document.getElementById("error-box");
    const noticeBox = document.getElementById("notice-box");
    const progressBox = document.getElementById("progress-box");
    const progressTitle = document.getElementById("progress-title");
    const progressDetail = document.getElementById("progress-detail");
    const progressElapsed = document.getElementById("progress-elapsed");
    const progressNote = document.getElementById("progress-note");
    const cancelRequestButton = document.getElementById("cancel-request");
    const responseBox = document.getElementById("response-box");
    const responseText = document.getElementById("response-text");
    const factStrengthBar = document.getElementById("fact-strength-bar");
    const responseOriginGroup = document.getElementById("response-origin-group");
    const responseOriginBadge = document.getElementById("response-origin-badge");
    const responseAnswerModeBadge = document.getElementById("response-answer-mode-badge");
    const responseOriginDetail = document.getElementById("response-origin-detail");
    const responseQuickMeta = document.getElementById("response-quick-meta");
    const responseQuickMetaText = document.getElementById("response-quick-meta-text");
    const responseFeedbackBox = document.getElementById("response-feedback-box");
    const responseFeedbackStatus = document.getElementById("response-feedback-status");
    const responseFeedbackButtons = Array.from(document.querySelectorAll("#response-feedback-actions .feedback-button"));
    const responseFeedbackDetailBox = document.getElementById("response-feedback-detail-box");
    const responseFeedbackReasonStatus = document.getElementById("response-feedback-reason-status");
    const responseFeedbackReasonButtons = Array.from(document.querySelectorAll("#response-feedback-reason-actions .feedback-button"));
    const responseFeedbackRetryButton = document.getElementById("response-feedback-retry");
    const responseContentVerdictBox = document.getElementById("response-content-verdict-box");
    const responseContentVerdictState = document.getElementById("response-content-verdict-state");
    const responseContentVerdictStatus = document.getElementById("response-content-verdict-status");
    const responseContentRejectButton = document.getElementById("response-content-reject");
    const responseContentReasonBox = document.getElementById("response-content-reason-box");
    const responseContentReasonStatus = document.getElementById("response-content-reason-status");
    const responseContentReasonInput = document.getElementById("response-content-reason-input");
    const responseContentReasonSubmitButton = document.getElementById("response-content-reason-submit");
    const responseCorrectionBox = document.getElementById("response-correction-box");
    const responseCorrectionState = document.getElementById("response-correction-state");
    const responseCorrectionStatus = document.getElementById("response-correction-status");
    const responseCorrectionInput = document.getElementById("response-correction-input");
    const responseCorrectionSubmitButton = document.getElementById("response-correction-submit");
    const responseCorrectionSaveRequestButton = document.getElementById("response-correction-save-request");
    const responseCandidateConfirmationBox = document.getElementById("response-candidate-confirmation-box");
    const responseCandidateConfirmationState = document.getElementById("response-candidate-confirmation-state");
    const responseCandidateConfirmationStatus = document.getElementById("response-candidate-confirmation-status");
    const responseCandidateConfirmationSubmitButton = document.getElementById("response-candidate-confirmation-submit");
    const responseSavedPathRow = document.getElementById("response-saved-path-row");
    const responseSavedPath = document.getElementById("response-saved-path");
    const responseCopyPathButton = document.getElementById("response-copy-path");
    const responseCopyTextButton = document.getElementById("response-copy-text");
    const responseSearchRecordRow = document.getElementById("response-search-record-row");
    const responseSearchRecord = document.getElementById("response-search-record");
    const responseCopySearchRecordButton = document.getElementById("response-copy-search-record");
    const previewBox = document.getElementById("preview-box");
    const previewText = document.getElementById("preview-text");
    const contextBox = document.getElementById("context-box");
    const contextText = document.getElementById("context-text");
    const suggestionsBox = document.getElementById("suggestions-box");
    const suggestionsList = document.getElementById("suggestions-list");
    const searchHistoryBox = document.getElementById("search-history-box");
    const searchHistoryMeta = document.getElementById("search-history-meta");
    const searchHistoryList = document.getElementById("search-history-list");
    const selectedBox = document.getElementById("selected-box");
    const selectedText = document.getElementById("selected-text");
    const evidenceBox = document.getElementById("evidence-box");
    const evidenceBody = document.getElementById("evidence-body");
    const evidenceHint = document.getElementById("evidence-hint");
    const evidenceScrollRegion = document.getElementById("evidence-scroll-region");
    const evidenceText = document.getElementById("evidence-text");
    const evidenceToggleButton = document.getElementById("toggle-evidence");
    const summaryChunksBox = document.getElementById("summary-chunks-box");
    const summaryChunksBody = document.getElementById("summary-chunks-body");
    const summaryChunksHint = document.getElementById("summary-chunks-hint");
    const summaryChunksScrollRegion = document.getElementById("summary-chunks-scroll-region");
    const summaryChunksText = document.getElementById("summary-chunks-text");
    const summaryChunksToggleButton = document.getElementById("toggle-summary-chunks");
    const claimCoverageBox = document.getElementById("claim-coverage-box");
    const claimCoverageBody = document.getElementById("claim-coverage-body");
    const claimCoverageHint = document.getElementById("claim-coverage-hint");
    const claimCoverageScrollRegion = document.getElementById("claim-coverage-scroll-region");
    const claimCoverageText = document.getElementById("claim-coverage-text");
    const claimCoverageToggleButton = document.getElementById("toggle-claim-coverage");
    const runtimeBox = document.getElementById("runtime-box");
    const approvalBox = document.getElementById("approval-box");
    const approvalMeta = document.getElementById("approval-meta");
    const approvalPathInput = document.getElementById("approval-path-input");
    const reissueButton = document.getElementById("reissue-button");
    const approvalCopyPathButton = document.getElementById("approval-copy-path");
    const approvalPreview = document.getElementById("approval-preview");
    const approveButton = document.getElementById("approve-button");
    const rejectButton = document.getElementById("reject-button");
    const sessionIdInput = document.getElementById("session-id");
    const sourcePathInput = document.getElementById("source-path");
    const browserFileInput = document.getElementById("browser-file-input");
    const pickFileButton = document.getElementById("pick-file-button");
    const clearPickedFileButton = document.getElementById("clear-picked-file");
    const pickedFileRow = document.getElementById("picked-file-row");
    const pickedFileName = document.getElementById("picked-file-name");
    const searchRootInput = document.getElementById("search-root");
    const searchQueryInput = document.getElementById("search-query");
    const browserFolderInput = document.getElementById("browser-folder-input");
    const pickFolderButton = document.getElementById("pick-folder-button");
    const clearPickedFolderButton = document.getElementById("clear-picked-folder");
    const pickedFolderRow = document.getElementById("picked-folder-row");
    const pickedFolderName = document.getElementById("picked-folder-name");
    const currentSessionTitleEl = document.getElementById("current-session-title");
    const currentSessionMetaEl = document.getElementById("current-session-meta");
    const reviewQueueBox = document.getElementById("review-queue-box");
    const reviewQueueStatus = document.getElementById("review-queue-status");
    const reviewQueueList = document.getElementById("review-queue-list");
    const aggregateTriggerBox = document.getElementById("aggregate-trigger-box");
    const aggregateTriggerStatus = document.getElementById("aggregate-trigger-status");
    const aggregateTriggerList = document.getElementById("aggregate-trigger-list");
    const webSearchPermissionInput = document.getElementById("web-search-permission");
    const searchOnlyCheck = document.getElementById("search-only-check");
    const newSessionButton = document.getElementById("new-session");
    const refreshSessionButton = document.getElementById("refresh-session");
    const loadSessionButton = document.getElementById("load-session");

    const state = {
      currentSessionId: APP_CONFIG.DEFAULT_SESSION_ID,
      _lastRenderedSessionUpdatedAt: "",
      defaultWebSearchPermission: APP_CONFIG.DEFAULT_WEB_SEARCH_PERMISSION,
      webSearchToolConnected: false,
      currentApproval: null,
      currentSessionMessages: [],
      isBusy: false,
      busyTimer: null,
      busyStartedAt: 0,
      currentRequestId: null,
      currentRequestSessionId: "",
      cancelRequested: false,
      selectedBrowserFile: null,
      selectedSearchFolderFiles: [],
      latestAssistantMessageId: null,
      latestAssistantUserText: "",
      latestAssistantFeedbackLabel: "",
      latestAssistantFeedbackReason: "",
      latestContentVerdictMessageId: null,
      latestContentVerdictArtifactId: "",
      latestContentVerdictOutcome: "",
      latestContentVerdictRecordedAt: "",
      latestContentReasonNote: "",
      latestContentReasonRecordedAt: "",
      latestCorrectionMessageId: null,
      latestCorrectionArtifactId: "",
      latestCorrectionBaseText: "",
      latestCorrectionRecordedText: "",
      latestCorrectionRecordedAt: "",
      latestCandidateConfirmationMessageId: null,
      latestCandidateConfirmationArtifactId: "",
      latestCandidateConfirmationCandidateId: "",
      latestCandidateConfirmationCandidateUpdatedAt: "",
      latestCandidateConfirmationRecordedAt: ""
    };

    function setText(id, value) {
      const element = document.getElementById(id);
      if (element) element.textContent = value;
    }

    function showElement(element, visible) {
      element.classList.toggle("hidden", !visible);
      if (visible) {
        element.removeAttribute("hidden");
      } else {
        element.setAttribute("hidden", "");
      }
    }

    function formatMessageWhen(value) {
      if (!value) return "";
      try {
        const date = new Date(value);
        const now = new Date();
        const sameDay = date.getFullYear() === now.getFullYear()
          && date.getMonth() === now.getMonth()
          && date.getDate() === now.getDate();
        if (sameDay) {
          return date.toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" });
        }
        return date.toLocaleString("ko-KR");
      } catch (error) {
        return String(value);
      }
    }

    function formatWhen(value) {
      if (!value) return "시간 정보 없음";
      try {
        return new Date(value).toLocaleString("ko-KR");
      } catch (error) {
        return value;
      }
    }

    function formatOrigin(origin) {
      if (!origin || typeof origin !== "object") {
        return null;
      }

      const provider = String(origin.provider || "system");
      const badge = String(origin.badge || provider || "SYSTEM");
      const label = String(origin.label || "시스템 응답");
      const model = origin.model ? String(origin.model) : "";
      const kind = String(origin.kind || "assistant");
      const answerMode = String(origin.answer_mode || "general");
      const sourceRoles = Array.isArray(origin.source_roles)
        ? origin.source_roles.map((item) => String(item || "").trim()).filter(Boolean)
        : [];
      const verificationLabel = String(origin.verification_label || "").trim();

      const answerModeLabel = formatAnswerModeLabel(answerMode);
      const isInvestigation = answerMode === C.AnswerMode.ENTITY_CARD || answerMode === C.AnswerMode.LATEST_UPDATE;

      const detailParts = [label];
      if (verificationLabel) detailParts.push(formatVerificationLabel(verificationLabel));
      if (model) detailParts.push(`모델 ${model}`);
      if (sourceRoles.length > 0) detailParts.push(`출처 유형 ${sourceRoles.map(formatSourceRoleCompact).join(", ")}`);
      if (kind === C.ResponseOriginKind.APPROVAL) detailParts.push("승인/취소 처리");
      return {
        provider,
        badge,
        detail: detailParts.join(" · "),
        answerModeBadge: isInvestigation ? answerModeLabel : "",
      };
    }

    function activeMode() {
      return document.querySelector('input[name="request_mode"]:checked')?.value || "file";
    }

    function currentProvider() {
      return document.getElementById("provider").value || "mock";
    }

    function currentModel() {
      const explicitModel = document.getElementById("model").value.trim();
      if (explicitModel) return explicitModel;
      return currentProvider() === "mock" ? "내장 모의 어댑터" : "선택형 로컬 모델";
    }

    function normalizeWebSearchPermission(value) {
      const normalized = String(value || "").trim().toLowerCase();
      if (normalized === C.WebSearchPermission.APPROVAL || normalized === C.WebSearchPermission.ENABLED) return normalized;
      return C.WebSearchPermission.DISABLED;
    }

    function formatWebSearchPermissionLabel(permission) {
      const normalized = normalizeWebSearchPermission(permission);
      if (normalized === C.WebSearchPermission.APPROVAL) {
        return state.webSearchToolConnected ? "승인 필요" : "승인 필요 · 도구 미연결";
      }
      if (normalized === C.WebSearchPermission.ENABLED) {
        return state.webSearchToolConnected ? "허용" : "허용 · 도구 미연결";
      }
      return state.webSearchToolConnected ? "차단" : "차단 · 도구 미연결";
    }

    function updateWebSearchMeta(permission) {
      setText("meta-web-search", formatWebSearchPermissionLabel(permission));
    }

    function formatFileSize(bytes) {
      const size = Number(bytes || 0);
      if (!Number.isFinite(size) || size <= 0) return "0 B";
      if (size < 1024) return `${size} B`;
      if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
      return `${(size / (1024 * 1024)).toFixed(1)} MB`;
    }

    function applyMode(mode) {
      showElement(document.getElementById("file-fields"), mode === "file");
      showElement(document.getElementById("search-fields"), mode === "search");
      showElement(document.getElementById("chat-fields"), mode === "chat");
      showElement(searchOnlyCheck, mode === "search");
      if (mode !== "search") {
        document.getElementById("search-only").checked = false;
      }
    }

    function renderSelectedBrowserFile(file) {
      state.selectedBrowserFile = file || null;
      showElement(pickedFileRow, Boolean(file));
      showElement(clearPickedFileButton, Boolean(file));
      pickedFileName.textContent = file ? `${file.name} · ${formatFileSize(file.size)}` : "";
    }

    function clearSelectedBrowserFile() {
      state.selectedBrowserFile = null;
      browserFileInput.value = "";
      renderSelectedBrowserFile(null);
    }

    function deriveFolderLabel(files) {
      const firstFile = Array.isArray(files) && files.length > 0 ? files[0] : null;
      if (!firstFile) return "선택 폴더";
      const relativePath = String(firstFile.webkitRelativePath || "").trim();
      if (relativePath.includes("/")) {
        return relativePath.split("/")[0];
      }
      return "선택 폴더";
    }

    function renderSelectedSearchFolder(files) {
      const normalizedFiles = Array.isArray(files) ? files.filter(Boolean) : [];
      state.selectedSearchFolderFiles = normalizedFiles;
      const hasFiles = normalizedFiles.length > 0;
      showElement(pickedFolderRow, hasFiles);
      showElement(clearPickedFolderButton, hasFiles);
      if (!hasFiles) {
        pickedFolderName.textContent = "";
        return;
      }

      const totalBytes = normalizedFiles.reduce((sum, file) => sum + Number(file.size || 0), 0);
      const folderLabel = deriveFolderLabel(normalizedFiles);
      pickedFolderName.textContent = `${folderLabel} · ${normalizedFiles.length}개 파일 · ${formatFileSize(totalBytes)}`;
    }

    function clearSelectedSearchFolder() {
      state.selectedSearchFolderFiles = [];
      browserFolderInput.value = "";
      renderSelectedSearchFolder([]);
    }

    function bytesToBase64(bytes) {
      let binary = "";
      const chunkSize = 0x8000;
      for (let index = 0; index < bytes.length; index += chunkSize) {
        const chunk = bytes.subarray(index, Math.min(index + chunkSize, bytes.length));
        binary += String.fromCharCode(...chunk);
      }
      return btoa(binary);
    }

    async function buildUploadedFilePayload() {
      const file = state.selectedBrowserFile;
      if (!file) return null;
      const arrayBuffer = await file.arrayBuffer();
      const bytes = new Uint8Array(arrayBuffer);
      return {
        name: file.name,
        mime_type: file.type || "",
        size_bytes: bytes.byteLength,
        content_base64: bytesToBase64(bytes),
      };
    }

    async function buildUploadedSearchFilesPayload() {
      const files = Array.isArray(state.selectedSearchFolderFiles) ? state.selectedSearchFolderFiles : [];
      if (files.length === 0) return null;

      const folderLabel = deriveFolderLabel(files);
      return Promise.all(
        files.map(async (file) => {
          const arrayBuffer = await file.arrayBuffer();
          const bytes = new Uint8Array(arrayBuffer);
          return {
            name: file.name,
            relative_path: file.webkitRelativePath || file.name,
            root_label: folderLabel,
            mime_type: file.type || "",
            size_bytes: bytes.byteLength,
            content_base64: bytesToBase64(bytes),
          };
        })
      );
    }

    async function collectPayload() {
      const payload = {
        session_id: sessionIdInput.value.trim() || state.currentSessionId,
        provider: document.getElementById("provider").value,
        model: document.getElementById("model").value.trim(),
        base_url: document.getElementById("base-url").value.trim(),
        web_search_permission: normalizeWebSearchPermission(webSearchPermissionInput.value),
        save_summary: document.getElementById("save-summary").checked,
        skip_preflight: document.getElementById("skip-preflight").checked,
        note_path: document.getElementById("note-path").value.trim(),
        selected_paths: document.getElementById("selected-paths").value.trim()
      };

      const mode = activeMode();
      const userTextValue = document.getElementById("user-text").value;
      if (mode === "file") {
        const uploadedFile = await buildUploadedFilePayload();
        if (uploadedFile) {
          payload.uploaded_file = uploadedFile;
        } else {
          payload.source_path = sourcePathInput.value.trim();
        }
        if (userTextValue) payload.user_text = userTextValue;
      } else if (mode === "search") {
        const uploadedSearchFiles = await buildUploadedSearchFilesPayload();
        if (uploadedSearchFiles && uploadedSearchFiles.length > 0) {
          payload.uploaded_search_files = uploadedSearchFiles;
        } else {
          payload.search_root = searchRootInput.value.trim();
        }
        payload.search_query = searchQueryInput.value.trim() || userTextValue;
        payload.search_limit = document.getElementById("search-limit").value.trim();
        payload.search_only = document.getElementById("search-only").checked;
        if (userTextValue) payload.user_text = userTextValue;
      } else {
        payload.user_text = userTextValue;
      }
      return payload;
    }

    function buildSharedRequestSettings() {
      return {
        session_id: sessionIdInput.value.trim() || state.currentSessionId,
        provider: document.getElementById("provider").value,
        model: document.getElementById("model").value.trim(),
        base_url: document.getElementById("base-url").value.trim(),
        web_search_permission: normalizeWebSearchPermission(webSearchPermissionInput.value),
        skip_preflight: document.getElementById("skip-preflight").checked,
      };
    }

    function createRequestId() {
      return `req-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
    }

    function providerBadge(provider) {
      const normalized = String(provider || "system").toUpperCase();
      if (normalized === "OLLAMA") return "OLLAMA";
      if (normalized === "MOCK") return "MOCK";
      return "SYSTEM";
    }

    function buildProgressMessage(mode, provider, model) {
      const badge = providerBadge(provider);
      if (mode === "approve") {
        return {
          title: "저장 승인 처리 중",
          detail: `${badge} · 승인된 노트를 안전하게 저장하는 중입니다.`,
          note: "파일 쓰기 전용 승인 흐름만 실행합니다.",
        };
      }
      if (mode === "reject") {
        return {
          title: "승인 취소 처리 중",
          detail: `${badge} · 승인 대기 작업을 정리하는 중입니다.`,
          note: "파일은 저장되지 않습니다.",
        };
      }
      if (mode === "reissue") {
        return {
          title: "승인 경로 다시 준비 중",
          detail: `${badge} · 기존 승인 요청을 새 저장 경로 기준으로 다시 만드는 중입니다.`,
          note: "파일은 저장하지 않고 승인 객체만 새로 발급합니다.",
        };
      }
      if (mode === "corrected_save") {
        return {
          title: "수정본 저장 승인 준비 중",
          detail: `${badge} · 기록된 수정본 기준으로 새 저장 승인 스냅샷을 만드는 중입니다.`,
          note: "현재 편집 중인 텍스트는 포함되지 않으며, 승인 미리보기는 요청 시점 그대로 고정됩니다.",
        };
      }
      if (mode === "follow_up") {
        return {
          title: "후속 응답 생성 중",
          detail: `${badge} · ${model} 기준으로 현재 문서 문맥을 바탕으로 답변을 생성하는 중입니다.`,
          note: provider === "ollama"
            ? "실제 로컬 모델은 첫 응답이나 긴 문맥에서 수 초 이상 걸릴 수 있습니다."
            : "모의 응답이라 비교적 빠르게 끝납니다.",
        };
      }
      if (mode === "history") {
        return {
          title: "검색 기록 불러오는 중",
          detail: `${badge} · ${model} 기준으로 최근 웹 검색 기록을 다시 여는 중입니다.`,
          note: "이미 로컬에 저장된 검색 기록만 다시 읽습니다.",
        };
      }
      const requestMode = activeMode();
      if (requestMode === "search") {
        return {
          title: "문서 검색 및 요약 중",
          detail: `${badge} · ${model} 기준으로 검색 결과를 읽고 응답을 구성하는 중입니다.`,
          note: provider === "ollama"
            ? "검색 후 선택된 문서를 다시 읽고 요약하기 때문에 시간이 더 걸릴 수 있습니다."
            : "검색 결과 기반 모의 응답을 준비하는 중입니다.",
        };
      }
      if (requestMode === "chat") {
        return {
          title: "일반 응답 생성 중",
          detail: `${badge} · ${model} 기준으로 대화 응답을 생성하는 중입니다.`,
          note: provider === "ollama"
            ? "실제 로컬 모델 추론이 진행 중입니다."
            : "모의 응답을 준비하는 중입니다.",
        };
      }
      return {
        title: "파일 요약 생성 중",
        detail: `${badge} · ${model} 기준으로 문서를 읽고 요약을 만드는 중입니다.`,
        note: provider === "ollama"
          ? "PDF나 긴 문서는 CPU 사용량이 높아지며 더 오래 걸릴 수 있습니다."
          : "내장 모의 어댑터로 흐름을 빠르게 확인하는 중입니다.",
      };
    }

    function setBusyControls(busy) {
      state.isBusy = busy;
      requestForm.classList.toggle("busy-locked", busy);
      transcriptEl.classList.toggle("busy-locked", busy);
      suggestionsList.classList.toggle("busy-locked", busy);
      searchHistoryList.classList.toggle("busy-locked", busy);
      transcriptEl.querySelectorAll("button").forEach((button) => {
        button.disabled = busy;
      });
      requestForm.querySelectorAll("button, input, textarea, select").forEach((element) => {
        element.disabled = busy;
      });
      newSessionButton.disabled = busy;
      refreshSessionButton.disabled = busy;
      loadSessionButton.disabled = busy;
      approveButton.disabled = busy || !state.currentApproval;
      reissueButton.disabled = busy || !state.currentApproval || !approvalPathInput.value.trim();
      rejectButton.disabled = busy || !state.currentApproval;
      approvalPathInput.disabled = busy || !state.currentApproval;
      approvalCopyPathButton.disabled = busy || !state.currentApproval || !state.currentApproval?.requested_path;
      responseCopyPathButton.disabled = !responseCopyPathButton.dataset.path;
      responseCopySearchRecordButton.disabled = !responseCopySearchRecordButton.dataset.path;
      suggestionsList.querySelectorAll("button").forEach((button) => {
        button.disabled = busy;
      });
      searchHistoryList.querySelectorAll("button").forEach((button) => {
        button.disabled = busy;
      });
      responseFeedbackButtons.forEach((button) => {
        button.disabled = busy || !state.latestAssistantMessageId;
      });
      responseFeedbackReasonButtons.forEach((button) => {
        button.disabled = busy || !state.latestAssistantMessageId || !["unclear", "incorrect"].includes(state.latestAssistantFeedbackLabel);
      });
      responseFeedbackRetryButton.disabled = busy || !state.latestAssistantMessageId || !["unclear", "incorrect"].includes(state.latestAssistantFeedbackLabel);
      updateContentVerdictState();
      updateCorrectionFormState();
      updateCandidateConfirmationState();
      updateCancelButton();
    }

    function updateCancelButton() {
      const visible = state.isBusy;
      showElement(cancelRequestButton, visible);
      cancelRequestButton.disabled = !visible || !state.currentRequestId || state.cancelRequested;
      cancelRequestButton.textContent = state.cancelRequested ? "취소 요청 중" : "응답 취소";
    }

    function clearBusyTimer() {
      if (state.busyTimer) {
        window.clearInterval(state.busyTimer);
        state.busyTimer = null;
      }
    }

    function setProgressElapsed() {
      const seconds = Math.max(0, (Date.now() - state.busyStartedAt) / 1000);
      progressElapsed.textContent = `${seconds.toFixed(1)}초`;
    }

    function startProgress(mode, provider, model) {
      const progress = buildProgressMessage(mode, provider, model);
      clearError();
      clearNotice();
      state.cancelRequested = false;
      progressTitle.textContent = progress.title;
      progressDetail.textContent = progress.detail;
      progressNote.textContent = progress.note;
      state.busyStartedAt = Date.now();
      setProgressElapsed();
      clearBusyTimer();
      state.busyTimer = window.setInterval(setProgressElapsed, 100);
      showElement(progressBox, true);
      setBusyControls(true);
    }

    function applyPhaseEvent(event) {
      if (!event || typeof event !== "object") return;
      showElement(progressBox, true);
      if (event.title) progressTitle.textContent = event.title;
      if (event.detail) progressDetail.textContent = event.detail;
      if (typeof event.note === "string") progressNote.textContent = event.note;
    }

    function stopProgress() {
      clearBusyTimer();
      state.currentRequestId = null;
      state.currentRequestSessionId = "";
      state.cancelRequested = false;
      showElement(progressBox, false);
      progressTitle.textContent = "응답 생성 중";
      progressDetail.textContent = "";
      progressElapsed.textContent = "0.0초";
      progressNote.textContent = "";
      setBusyControls(false);
    }

    async function fetchJson(url, options) {
      const response = await fetch(url, options);
      const data = await response.json();
      if (!response.ok || !data.ok) {
        throw new Error(data.error?.message || "요청을 처리하지 못했습니다.");
      }
      return data;
    }

    async function submitPayload(payload) {
      return fetchJson("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
    }

    function processStreamEvent(event, finalPayloadRef) {
      if (!event || typeof event !== "object") return;
      if (event.event === C.StreamEventType.PHASE) {
        applyPhaseEvent(event);
        return;
      }
      if (event.event === C.StreamEventType.RUNTIME_STATUS) {
        renderRuntime(event.runtime_status || null);
        return;
      }
      if (event.event === C.StreamEventType.RESPONSE_ORIGIN) {
        renderResponseOrigin(event.response_origin || null);
        return;
      }
      if (event.event === C.StreamEventType.TEXT_DELTA) {
        if (!finalPayloadRef._streamStarted) {
          finalPayloadRef._streamStarted = true;
          responseText.textContent = "";
        }
        responseText.textContent += event.delta || "";
        showElement(responseCopyTextButton, true);
        return;
      }
      if (event.event === C.StreamEventType.TEXT_REPLACE) {
        responseText.textContent = event.text || "";
        showElement(responseCopyTextButton, Boolean(event.text));
        return;
      }
      if (event.event === C.StreamEventType.FINAL) {
        finalPayloadRef.value = event.data || null;
        return;
      }
      if (event.event === C.StreamEventType.CANCELLED) {
        finalPayloadRef.value = {
          ok: true,
          cancelled: true,
          message: event.message || "요청을 취소했습니다.",
          request_id: event.request_id || null,
        };
        return;
      }
      if (event.event === C.StreamEventType.ERROR) {
        throw new Error(event.error?.message || "요청을 처리하지 못했습니다.");
      }
    }

    async function submitStreamPayload(payload) {
      const sessionId = String(payload.session_id || state.currentSessionId || sessionIdInput.value.trim() || APP_CONFIG.DEFAULT_SESSION_ID);
      const requestId = String(payload.request_id || createRequestId());
      const requestPayload = {
        ...payload,
        session_id: sessionId,
        request_id: requestId,
      };

      state.currentRequestId = requestId;
      state.currentRequestSessionId = sessionId;
      state.cancelRequested = false;
      updateCancelButton();

      const response = await fetch("/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestPayload)
      });

      if (!response.ok) {
        let message = "요청을 처리하지 못했습니다.";
        try {
          const data = await response.json();
          message = data.error?.message || message;
        } catch (error) {
          message = response.statusText || message;
        }
        throw new Error(message);
      }

      if (!response.body) {
        throw new Error("스트리밍 응답 본문을 읽을 수 없습니다.");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      const finalPayloadRef = { value: null };

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        while (true) {
          const newlineIndex = buffer.indexOf("\n");
          if (newlineIndex < 0) break;
          const line = buffer.slice(0, newlineIndex).trim();
          buffer = buffer.slice(newlineIndex + 1);
          if (!line) continue;
          processStreamEvent(JSON.parse(line), finalPayloadRef);
        }
      }

      if (buffer.trim()) {
        processStreamEvent(JSON.parse(buffer.trim()), finalPayloadRef);
      }

      if (!finalPayloadRef.value) {
        throw new Error("스트리밍 응답이 완료되지 않았습니다.");
      }
      return finalPayloadRef.value;
    }

    async function cancelCurrentRequest() {
      if (!state.isBusy || !state.currentRequestId || state.cancelRequested) return;

      state.cancelRequested = true;
      updateCancelButton();
      progressTitle.textContent = "취소 요청 중";
      progressDetail.textContent = "현재 스트리밍 요청을 안전하게 중단하도록 서버에 전달하는 중입니다.";
      progressNote.textContent = "이미 화면에 표시된 응답 조각은 유지하고, 이후 생성만 멈춥니다.";

      try {
        const data = await fetchJson("/api/chat/cancel", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            session_id: state.currentRequestSessionId || state.currentSessionId,
            request_id: state.currentRequestId,
          }),
        });
        if (!data.cancelled) {
          state.cancelRequested = false;
          updateCancelButton();
          renderNotice(data.message || "취소할 활성 요청을 찾지 못했습니다.");
          return;
        }
        progressNote.textContent = data.message || "취소 요청을 보냈습니다.";
      } catch (error) {
        state.cancelRequested = false;
        updateCancelButton();
        throw error;
      }
    }

    async function sendFollowUpPrompt(promptText) {
      if (state.isBusy) return;
      try {
        document.querySelector('input[name="request_mode"][value="chat"]').checked = true;
        applyMode("chat");
        document.getElementById("user-text").value = promptText;
        startProgress("follow_up", currentProvider(), currentModel());
        showElement(responseCopyTextButton, false);
        renderResponseOrigin(null);
        const data = await submitStreamPayload({
          session_id: state.currentSessionId,
          user_text: promptText,
          provider: document.getElementById("provider").value,
          model: document.getElementById("model").value.trim(),
          base_url: document.getElementById("base-url").value.trim(),
          skip_preflight: document.getElementById("skip-preflight").checked,
        });
        if (data?.cancelled) {
          renderNotice(data.message || "요청을 취소했습니다.");
          await fetchSessions();
          return;
        }
        renderResult(data);
        await fetchSessions();
      } catch (error) {
        renderError(error);
      } finally {
        stopProgress();
      }
    }

    async function sendRequest(extraPayload, progressMode = "follow_up") {
      if (state.isBusy) return null;
      try {
        startProgress(progressMode, currentProvider(), currentModel());
        showElement(responseCopyTextButton, false);
        renderResponseOrigin(null);
        const data = await submitStreamPayload({
          ...buildSharedRequestSettings(),
          ...extraPayload,
        });
        if (data?.cancelled) {
          renderNotice(data.message || "요청을 취소했습니다.");
          await fetchSessions();
          return data;
        }
        renderResult(data);
        await fetchSessions();
        return data;
      } catch (error) {
        renderError(error);
        throw error;
      } finally {
        stopProgress();
      }
    }

    function renderSessionList(sessions) {
      sessionListEl.innerHTML = "";
      if (!sessions || sessions.length === 0) {
        const empty = document.createElement("div");
        empty.className = "session-summary";
        empty.innerHTML = "<strong>세션이 없습니다.</strong><span class='hint'>첫 요청을 보내면 세션이 생성됩니다.</span>";
        sessionListEl.appendChild(empty);
        return;
      }

      sessions.forEach((session) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = `session-item ${session.session_id === state.currentSessionId ? "active" : ""}`;
        button.innerHTML = `
          <strong>${session.title || session.session_id}</strong>
          <span>업데이트 ${formatWhen(session.updated_at)} · 승인 대기 ${session.pending_approval_count || 0}건</span>
          <span>${session.last_message_preview || "아직 메시지가 없습니다."}</span>
        `;
        button.addEventListener("click", () => loadSession(session.session_id).catch(renderError));
        sessionListEl.appendChild(button);
      });
    }

    function findLatestAssistantContext(messages) {
      const items = Array.isArray(messages) ? messages : [];
      let latestAssistant = null;
      let latestUserText = "";
      let lastUserText = "";

      items.forEach((message) => {
        if (!message || typeof message !== "object") return;
        if (message.role === "user") {
          lastUserText = String(message.text || "").trim();
          return;
        }
        if (message.role === "assistant") {
          latestAssistant = message;
          latestUserText = lastUserText;
        }
      });

      return {
        assistant: latestAssistant,
        userText: latestUserText,
      };
    }

    function findMessageById(messages, messageId) {
      const normalizedMessageId = String(messageId || "").trim();
      if (!normalizedMessageId) return null;
      const items = Array.isArray(messages) ? messages : [];
      for (let index = items.length - 1; index >= 0; index -= 1) {
        const message = items[index];
        if (!message || typeof message !== "object") continue;
        if (String(message.message_id || "").trim() === normalizedMessageId) {
          return message;
        }
      }
      return null;
    }

    function findArtifactSourceMessage(messages, artifactId) {
      const normalizedArtifactId = String(artifactId || "").trim();
      if (!normalizedArtifactId) return null;
      const items = Array.isArray(messages) ? messages : [];
      for (let index = items.length - 1; index >= 0; index -= 1) {
        const message = items[index];
        if (!message || typeof message !== "object") continue;
        if (String(message.artifact_id || "").trim() !== normalizedArtifactId) continue;
        if (message.original_response_snapshot && typeof message.original_response_snapshot === "object") {
          return message;
        }
      }
      return null;
    }

    function findLatestSavedMessageForArtifact(messages, artifactId) {
      const normalizedArtifactId = String(artifactId || "").trim();
      if (!normalizedArtifactId) return null;
      const items = Array.isArray(messages) ? messages : [];
      for (let index = items.length - 1; index >= 0; index -= 1) {
        const message = items[index];
        if (!message || typeof message !== "object") continue;
        if (String(message.artifact_id || "").trim() !== normalizedArtifactId) continue;
        if (String(message.saved_note_path || "").trim()) {
          return message;
        }
      }
      return null;
    }

    function resolveCorrectionTargetMessage(messages, latestAssistantMessage) {
      if (canEditGroundedBrief(latestAssistantMessage)) {
        return latestAssistantMessage;
      }
      const sourceMessageId = String(
        latestAssistantMessage?.source_message_id
        || latestAssistantMessage?.approval?.source_message_id
        || ""
      ).trim();
      const sourceMessage = findMessageById(messages, sourceMessageId);
      if (canEditGroundedBrief(sourceMessage)) {
        return sourceMessage;
      }
      const artifactId = String(
        latestAssistantMessage?.artifact_id
        || latestAssistantMessage?.approval?.artifact_id
        || ""
      ).trim();
      const artifactSourceMessage = findArtifactSourceMessage(messages, artifactId);
      if (canEditGroundedBrief(artifactSourceMessage)) {
        return artifactSourceMessage;
      }
      return null;
    }

    function renderTranscript(messages) {
      transcriptEl.innerHTML = "";
      if (!messages || messages.length === 0) {
        const empty = document.createElement("div");
        empty.className = "message assistant";
        empty.innerHTML = '<span class="role">비서</span><pre>세션이 비어 있습니다. 첫 요청을 보내 보세요.</pre>';
        transcriptEl.appendChild(empty);
        return;
      }

      messages.forEach((message) => {
        const card = document.createElement("article");
        card.className = `message ${message.role || "assistant"}`;

        const header = document.createElement("div");
        header.className = "message-header";

        const left = document.createElement("div");
        left.className = "message-header-left";
        const role = document.createElement("span");
        role.className = "role";
        role.textContent = message.role === "user" ? "사용자" : "비서";
        left.appendChild(role);

        if (message.created_at) {
          const when = document.createElement("span");
          when.className = "message-when";
          when.textContent = formatMessageWhen(message.created_at);
          left.appendChild(when);
        }

        if (message.role !== "user" && message.status) {
          const statusBadge = document.createElement("span");
          applyStatusBadge(statusBadge, message.status);
          left.appendChild(statusBadge);
        }
        header.appendChild(left);

        if (message.role !== "user") {
          const formattedOrigin = formatOrigin(message.response_origin);
          if (formattedOrigin) {
            const originGroup = document.createElement("div");
            originGroup.className = "origin-group";

            const badge = document.createElement("span");
            badge.className = `origin-badge ${formattedOrigin.provider}`;
            badge.textContent = formattedOrigin.badge;
            originGroup.appendChild(badge);

            const detail = document.createElement("span");
            detail.className = "origin-detail";
            detail.textContent = formattedOrigin.detail;
            originGroup.appendChild(detail);

            header.appendChild(originGroup);
          }
        }

        card.appendChild(header);

        var isSearchOnly = Array.isArray(message.search_results) && message.search_results.length > 0
          && typeof message.text === "string" && message.text.startsWith("검색 결과:");
        if (!isSearchOnly) {
          const body = document.createElement("pre");
          body.textContent = message.text || "";
          card.appendChild(body);
        }

        if (Array.isArray(message.search_results) && message.search_results.length > 0) {
          const previewPanel = document.createElement("div");
          previewPanel.className = "search-preview-panel";
          message.search_results.forEach(function(sr, idx) {
            const item = document.createElement("div");
            item.className = "search-preview-item";
            const fileName = String(sr.path || "").split(/[\\/]/).filter(Boolean).pop() || "(파일명 없음)";
            const matchLabel = sr.matched_on === "filename" ? "파일명 일치" : "내용 일치";
            const nameEl = document.createElement("div");
            nameEl.className = "search-preview-name";
            nameEl.textContent = (idx + 1) + ". " + fileName;
            nameEl.title = sr.path || "";
            item.appendChild(nameEl);
            const matchEl = document.createElement("span");
            matchEl.className = "search-preview-match";
            matchEl.textContent = matchLabel;
            item.appendChild(matchEl);
            if (sr.snippet) {
              const snippetEl = document.createElement("div");
              snippetEl.className = "search-preview-snippet";
              snippetEl.textContent = sr.snippet;
              item.appendChild(snippetEl);
            }
            previewPanel.appendChild(item);
          });
          card.appendChild(previewPanel);
        }

        const metaLines = [];
        if (message.status) metaLines.push(`상태 ${compactStatusLabel(message.status)}`);
        const srcLabel = getSourceTypeLabel(message);
        if (srcLabel) metaLines.push(srcLabel);
        if (Array.isArray(message.selected_source_paths) && message.selected_source_paths.length === 1) {
          const sourceName = String(message.selected_source_paths[0] || "").split(/[\\/]/).filter(Boolean).pop() || "출처 1개";
          metaLines.push(`출처 ${sourceName}`);
        } else if (Array.isArray(message.selected_source_paths) && message.selected_source_paths.length > 1) {
          metaLines.push(`출처 ${message.selected_source_paths.length}개`);
        }
        if (Array.isArray(message.evidence) && message.evidence.length > 0) {
          metaLines.push(`근거 ${message.evidence.length}개`);
        }
        if (Array.isArray(message.summary_chunks) && message.summary_chunks.length > 0) {
          metaLines.push(`요약 구간 ${message.summary_chunks.length}개`);
        }
        if (Array.isArray(message.claim_coverage) && message.claim_coverage.length > 0) {
          const claimSummary = formatClaimCoverageSummary(message.claim_coverage);
          if (claimSummary) {
            metaLines.push(`사실 검증 ${claimSummary}`);
          }
        }
        if (message.feedback?.label) {
          const feedbackLabel = formatFeedbackLabel(message.feedback.label);
          const feedbackReason = formatFeedbackReasonLabel(message.feedback.reason || "");
          metaLines.push(`피드백 ${feedbackLabel}${feedbackReason ? ` · ${feedbackReason}` : ""}`);
        }
        if (usesCorrectedSaveSnapshot(message)) {
          metaLines.push("저장 기준 요청 시점 수정본 스냅샷");
        }
        if (usesRejectedContentVerdict(message)) {
          metaLines.push("내용 거절 기록됨");
        } else if (String(message.corrected_outcome?.outcome || "").trim().toLowerCase() === "corrected") {
          metaLines.push("교정본 기록됨");
        }
        if (message.saved_note_path) {
          metaLines.push(`저장 경로 ${compactDisplayPath(message.saved_note_path)}`);
        } else if (message.web_search_record_path) {
          metaLines.push(`검색 기록 ${compactDisplayPath(message.web_search_record_path)}`);
        } else if (message.proposed_note_path) {
          metaLines.push(`제안 경로 ${compactDisplayPath(message.proposed_note_path)}`);
        }
        if (metaLines.length > 0) {
          const meta = document.createElement("div");
          meta.className = "meta";
          meta.dataset.testid = "transcript-meta";
          meta.textContent = metaLines.join(" · ");
          card.appendChild(meta);
        }

        if (message.saved_note_path) {
          const actions = document.createElement("div");
          actions.className = "message-actions";
          const copyButton = document.createElement("button");
          copyButton.type = "button";
          copyButton.className = "copy-button subtle";
          copyButton.textContent = "저장 경로 복사";
          copyButton.addEventListener("click", () => {
            copyTextValue(message.saved_note_path, "저장 경로를 복사했습니다.").catch(renderError);
          });
          actions.appendChild(copyButton);
          card.appendChild(actions);
        }
        if (message.web_search_record_path) {
          const actions = document.createElement("div");
          actions.className = "message-actions";
          const copyButton = document.createElement("button");
          copyButton.type = "button";
          copyButton.className = "copy-button subtle";
          copyButton.textContent = "검색 기록 경로 복사";
          copyButton.addEventListener("click", () => {
            copyTextValue(message.web_search_record_path, "검색 기록 경로를 복사했습니다.").catch(renderError);
          });
          actions.appendChild(copyButton);
          card.appendChild(actions);
        }

        if (message.role !== "user" && message.message_id) {
          const feedbackControls = buildFeedbackControls(message);
          if (feedbackControls) {
            card.appendChild(feedbackControls);
          }
        }

        transcriptEl.appendChild(card);
      });
    }

    function renderRuntime(runtime) {
      if (!runtime) {
        showElement(runtimeBox, false);
        runtimeBox.innerHTML = "";
        return;
      }

      showElement(runtimeBox, true);
      runtimeBox.innerHTML = "";
      const title = document.createElement("strong");
      title.textContent = "런타임 상태";
      runtimeBox.appendChild(title);

      const body = document.createElement("pre");
      const lines = [
        `프로바이더: ${runtime.provider}`,
        `설정된 모델: ${runtime.configured_model || "선택형 로컬 모델"}`,
        `접속 가능: ${runtime.reachable}`,
        `모델 사용 가능: ${runtime.configured_model_available}`
      ];
      if (runtime.detail) lines.push(`상세: ${runtime.detail}`);
      if (runtime.version) lines.push(`버전: ${runtime.version}`);
      body.textContent = lines.join("\n");
      runtimeBox.appendChild(body);
    }

    function renderResponseOrigin(origin) {
      const formattedOrigin = formatOrigin(origin);
      showElement(responseOriginGroup, Boolean(formattedOrigin));
      if (!formattedOrigin) {
        responseOriginBadge.className = "origin-badge system";
        responseOriginBadge.textContent = "SYSTEM";
        showElement(responseAnswerModeBadge, false);
        responseOriginDetail.textContent = "";
        return;
      }

      responseOriginBadge.className = `origin-badge ${formattedOrigin.provider}`;
      responseOriginBadge.textContent = formattedOrigin.badge;
      if (formattedOrigin.answerModeBadge) {
        responseAnswerModeBadge.textContent = formattedOrigin.answerModeBadge;
        showElement(responseAnswerModeBadge, true);
      } else {
        showElement(responseAnswerModeBadge, false);
      }
      responseOriginDetail.textContent = formattedOrigin.detail;
    }

    function renderSelected(selected) {
      const items = Array.isArray(selected) ? selected : [];
      showElement(selectedBox, items.length > 0);
      selectedText.textContent = items.join("\n");
    }

    function renderPreview(preview) {
      showElement(previewBox, Boolean(preview));
      previewText.textContent = preview || "";
    }

    function truncateDisplayText(text, maxChars = 150) {
      const normalized = String(text || "").replace(/\s+/g, " ").trim();
      if (!normalized) return "";
      if (normalized.length <= maxChars) return normalized;
      return `${normalized.slice(0, maxChars - 1)}…`;
    }

    function compactDisplayPath(path) {
      const normalized = String(path || "").trim();
      if (!normalized) return "";

      const parts = normalized.split(/[\\/]/).filter(Boolean);
      if (parts.length <= 4) return normalized;
      return `.../${parts.slice(-4).join("/")}`;
    }

    function compactIdentifier(value, leading = 8, trailing = 8) {
      const normalized = String(value || "").trim();
      if (!normalized) return "";
      if (normalized.length <= leading + trailing + 1) return normalized;
      return `${normalized.slice(0, leading)}…${normalized.slice(-trailing)}`;
    }

    function sourceNameCounts(items) {
      const counts = {};
      items.forEach((item) => {
        const sourceName = item.source_name || "(출처 없음)";
        counts[sourceName] = (counts[sourceName] || 0) + 1;
      });
      return counts;
    }

    function getSourceTypeLabel(obj) {
      const kind = String(obj?.active_context?.kind || "").trim();
      if (kind === "search") return "선택 결과 요약";
      if (kind === "document" && (obj?.summary_chunks?.length || obj?.evidence?.length)) return "문서 요약";
      return null;
    }

    function compactStatusLabel(status) {
      const normalized = String(status || "").trim();
      if (!normalized) return "응답";
      if (normalized === "needs_approval") return "승인 요청";
      if (normalized === "saved") return "저장 완료";
      if (normalized === "error") return "오류";
      return normalized;
    }

    function formatFeedbackLabel(label) {
      const normalized = String(label || "").trim().toLowerCase();
      if (normalized === "helpful") return "도움 됨";
      if (normalized === "unclear") return "애매함";
      if (normalized === "incorrect") return "틀림";
      return "";
    }

    function formatFeedbackReasonLabel(reason) {
      const normalized = String(reason || "").trim().toLowerCase();
      if (normalized === "factual_error") return "사실과 다름";
      if (normalized === "irrelevant_result") return "검색과 무관";
      if (normalized === "context_miss") return "문맥 오해";
      if (normalized === "awkward_tone") return "표현 어색함";
      return "";
    }

    function formatPromotionBasisLabel(value) {
      const normalized = String(value || "").trim().toLowerCase();
      if (normalized === "explicit_confirmation") return "명시 확인";
      return normalized || "미확인";
    }

    function formatPromotionEligibilityLabel(value) {
      const normalized = String(value || "").trim().toLowerCase();
      if (normalized === "eligible_for_review") return "검토 대기";
      return normalized || "미확인";
    }

    function formatConfirmationLabel(value) {
      const normalized = String(value || "").trim().toLowerCase();
      if (normalized === "explicit_reuse_confirmation") return "재사용 확인";
      return normalized || "미확인";
    }

    function formatAggregateCandidateFamilyLabel(value) {
      const normalized = String(value || "").trim().toLowerCase();
      if (normalized === C.CandidateFamily.CORRECTION_REWRITE) return "반복 교정 묶음";
      return normalized || "검토 메모 적용 후보";
    }

    function aggregateTriggerTitle(item) {
      const aggregateKey = item && typeof item === "object" && item.aggregate_key && typeof item.aggregate_key === "object"
        ? item.aggregate_key
        : {};
      return formatAggregateCandidateFamilyLabel(aggregateKey.candidate_family);
    }

    function isAggregateTriggerUnblocked(item) {
      return String(item?.reviewed_memory_capability_status?.capability_outcome || "").trim() === "unblocked_all_required";
    }

    function aggregateTriggerBlockedHelper(item) {
      const capabilityOutcome = String(item?.reviewed_memory_capability_status?.capability_outcome || "").trim() || "미확인";
      const auditStage = String(item?.reviewed_memory_transition_audit_contract?.audit_stage || "").trim() || "미확인";
      if (isAggregateTriggerUnblocked(item)) {
        return `검토 메모 적용을 시작할 수 있습니다. 사유를 입력한 뒤 시작 버튼을 누르세요.`;
      }
      return `아직 검토 메모를 적용할 수 없습니다. capability 상태가 ${capabilityOutcome}이고 transition audit 상태가 ${auditStage} 입니다.`;
    }

    function formatSignalRefLabel(signalName) {
      const normalized = String(signalName || "").trim();
      if (normalized === "session_local_memory_signal.content_signal") return "content_signal";
      if (normalized === "session_local_memory_signal.save_signal") return "save_signal";
      return normalized || "signal";
    }

    function normalizeMultilineText(text) {
      return String(text || "").replace(/\r\n/g, "\n").trim();
    }

    function canEditGroundedBrief(message) {
      return Boolean(
        message
        && message.role !== "user"
        && message.message_id
        && message.artifact_kind === C.ArtifactKind.GROUNDED_BRIEF
        && message.original_response_snapshot
      );
    }

    function currentCorrectionSeedText(message) {
      const correctedText = normalizeMultilineText(message?.corrected_text || "");
      if (correctedText) return correctedText;
      const draftText = normalizeMultilineText(message?.original_response_snapshot?.draft_text || "");
      if (draftText) return draftText;
      return normalizeMultilineText(message?.text || "");
    }

    function usesCorrectedSaveSnapshot(item) {
      return String(item?.save_content_source || "").trim() === C.SaveContentSource.CORRECTED_TEXT;
    }

    function usesRejectedContentVerdict(item) {
      return String(item?.corrected_outcome?.outcome || "").trim().toLowerCase() === C.ContentVerdict.REJECTED;
    }

    function hasSavedHistoryForArtifact(artifactId) {
      return Boolean(findLatestSavedMessageForArtifact(state.currentSessionMessages, artifactId));
    }

    function resolveApprovalSourceMessage(approval) {
      if (!approval || typeof approval !== "object") return null;
      const sourceMessageId = String(approval.source_message_id || "").trim();
      const sourceMessage = findMessageById(state.currentSessionMessages, sourceMessageId);
      if (sourceMessage) return sourceMessage;
      return findArtifactSourceMessage(state.currentSessionMessages, approval.artifact_id);
    }

    function updateCorrectionHelperText() {
      const hasMessage = Boolean(state.latestCorrectionMessageId);
      if (!hasMessage) {
        responseCorrectionState.textContent = "";
        responseCorrectionStatus.textContent = "";
        return;
      }

      const currentText = normalizeMultilineText(responseCorrectionInput.value);
      const recordedText = normalizeMultilineText(state.latestCorrectionRecordedText);
      const hasRecordedCorrection = Boolean(recordedText);
      const hasUnrecordedEditorChange = hasRecordedCorrection && currentText !== recordedText;
      const currentApprovalMatchesArtifact = Boolean(
        state.currentApproval
        && String(state.currentApproval.artifact_id || "").trim()
        && String(state.currentApproval.artifact_id || "").trim() === String(state.latestCorrectionArtifactId || "").trim()
      );

      if (!hasRecordedCorrection) {
        responseCorrectionState.textContent = "기록된 수정본이 아직 없습니다.";
        responseCorrectionStatus.textContent = [
          "먼저 수정본 기록을 눌러야 저장 요청 버튼이 켜집니다.",
          "입력창의 미기록 텍스트는 바로 승인 스냅샷이 되지 않습니다.",
          "저장 승인과는 별도입니다.",
        ].join(" ");
        return;
      }

      if (hasUnrecordedEditorChange) {
        responseCorrectionState.textContent = "입력창 변경이 아직 다시 기록되지 않았습니다.";
        const statusParts = [
          "저장 요청 버튼은 직전 기록본으로만 동작합니다.",
          "지금 입력 중인 수정으로 저장하려면 먼저 수정본 기록을 다시 눌러 주세요.",
          "저장 승인과는 별도입니다.",
        ];
        if (currentApprovalMatchesArtifact) {
          if (usesCorrectedSaveSnapshot(state.currentApproval)) {
            statusParts.push("이미 열린 저장 승인 카드도 이전 요청 시점 스냅샷으로 그대로 유지됩니다.");
          } else {
            statusParts.push("현재 저장 승인은 기존 초안 기준이며, 수정본을 자동으로 저장하지 않습니다.");
          }
        }
        responseCorrectionStatus.textContent = statusParts.join(" ");
        return;
      }

      responseCorrectionState.textContent = state.latestCorrectionRecordedAt
        ? `기록된 수정본이 있습니다 · ${formatWhen(state.latestCorrectionRecordedAt)}`
        : "기록된 수정본이 있습니다.";
      const statusParts = [
        "저장 요청은 현재 입력창이 아니라 이미 기록된 수정본으로 새 승인 미리보기를 만듭니다.",
        "저장 승인과는 별도입니다.",
      ];
      if (currentApprovalMatchesArtifact) {
        if (usesCorrectedSaveSnapshot(state.currentApproval)) {
          statusParts.push("이미 열린 저장 승인 카드가 있으면 그 카드도 요청 시점 스냅샷으로 고정되어 있습니다.");
        } else {
          statusParts.push("현재 저장 승인은 기존 초안 기준이며, 수정본을 자동으로 저장하지 않습니다.");
        }
      }
      responseCorrectionStatus.textContent = statusParts.join(" ");
    }

    function updateCorrectionFormState() {
      const hasMessage = Boolean(state.latestCorrectionMessageId);
      const currentText = normalizeMultilineText(responseCorrectionInput.value);
      const baseText = normalizeMultilineText(state.latestCorrectionBaseText);
      const hasChange = Boolean(currentText) && currentText !== baseText;
      const hasRecordedCorrection = Boolean(normalizeMultilineText(state.latestCorrectionRecordedText));
      responseCorrectionInput.disabled = state.isBusy || !hasMessage;
      responseCorrectionSubmitButton.disabled = state.isBusy || !hasMessage || !hasChange;
      responseCorrectionSaveRequestButton.disabled = state.isBusy || !hasMessage || !hasRecordedCorrection;
      if (!hasMessage) {
        responseCorrectionSaveRequestButton.title = "";
      } else if (!hasRecordedCorrection) {
        responseCorrectionSaveRequestButton.title = "먼저 수정본 기록 후 저장 요청할 수 있습니다.";
      } else if (currentText !== normalizeMultilineText(state.latestCorrectionRecordedText)) {
        responseCorrectionSaveRequestButton.title = "현재 기록된 수정본으로 저장 요청합니다. 입력 중인 변경을 반영하려면 먼저 다시 기록해 주세요.";
      } else {
        responseCorrectionSaveRequestButton.title = "현재 기록된 수정본으로 저장 요청합니다.";
      }
      updateCorrectionHelperText();
    }

    function renderCorrectionEditor(message) {
      const editable = canEditGroundedBrief(message);
      showElement(responseCorrectionBox, editable);
      state.latestCorrectionMessageId = editable ? String(message.message_id || "") : null;
      state.latestCorrectionArtifactId = editable ? String(message.artifact_id || "") : "";
      state.latestCorrectionBaseText = editable ? currentCorrectionSeedText(message) : "";
      state.latestCorrectionRecordedText = editable ? normalizeMultilineText(message?.corrected_text || "") : "";
      state.latestCorrectionRecordedAt = editable ? String(message?.corrected_outcome?.recorded_at || "") : "";

      if (!editable) {
        responseCorrectionInput.value = "";
        updateCorrectionFormState();
        return;
      }

      responseCorrectionInput.value = state.latestCorrectionBaseText;
      updateCorrectionFormState();
    }

    function updateCandidateConfirmationState() {
      const hasCandidate = Boolean(
        state.latestCandidateConfirmationMessageId
        && state.latestCandidateConfirmationCandidateId
        && state.latestCandidateConfirmationCandidateUpdatedAt
      );
      const currentApprovalMatchesArtifact = Boolean(
        state.currentApproval
        && String(state.currentApproval.artifact_id || "").trim()
        && String(state.currentApproval.artifact_id || "").trim() === String(state.latestCandidateConfirmationArtifactId || "").trim()
      );
      const isConfirmed = Boolean(state.latestCandidateConfirmationRecordedAt);

      showElement(responseCandidateConfirmationBox, hasCandidate);
      responseCandidateConfirmationSubmitButton.disabled = state.isBusy || !hasCandidate || isConfirmed;

      if (!hasCandidate) {
        responseCandidateConfirmationState.textContent = "";
        responseCandidateConfirmationStatus.textContent = "";
        responseCandidateConfirmationSubmitButton.title = "";
        return;
      }

      if (isConfirmed) {
        responseCandidateConfirmationState.textContent = state.latestCandidateConfirmationRecordedAt
          ? `재사용 확인 기록됨 · ${formatWhen(state.latestCandidateConfirmationRecordedAt)}`
          : "재사용 확인 기록됨";
        const statusParts = [
          "현재 기록된 수정 방향을 나중에도 다시 써도 된다는 positive reuse confirmation만 남겼습니다.",
          "저장 승인, 내용 거절, 거절 메모와는 별도입니다.",
        ];
        if (currentApprovalMatchesArtifact) {
          statusParts.push("이미 열린 저장 승인 카드와도 별개로 유지됩니다.");
        }
        responseCandidateConfirmationStatus.textContent = statusParts.join(" ");
        responseCandidateConfirmationSubmitButton.title = "이미 현재 수정 방향 재사용 확인이 기록되었습니다.";
        return;
      }

      responseCandidateConfirmationState.textContent = "현재 수정 방향 재사용 확인은 아직 없습니다.";
      const statusParts = [
        "이 버튼은 현재 기록된 수정 방향을 나중에도 다시 써도 된다는 positive reuse confirmation만 남깁니다.",
        "저장 승인, 내용 거절, 거절 메모, 피드백과는 별도입니다.",
      ];
      if (currentApprovalMatchesArtifact) {
        statusParts.push("이미 열린 저장 승인 카드와도 섞이지 않습니다.");
      }
      responseCandidateConfirmationStatus.textContent = statusParts.join(" ");
      responseCandidateConfirmationSubmitButton.title = "현재 기록된 수정 방향 재사용 확인을 남깁니다.";
    }

    function renderCandidateConfirmationControl(message) {
      const editable = canEditGroundedBrief(message);
      const candidate = editable && message?.session_local_candidate && typeof message.session_local_candidate === "object"
        ? message.session_local_candidate
        : null;
      const confirmationRecord = candidate && message?.candidate_confirmation_record && typeof message.candidate_confirmation_record === "object"
        ? message.candidate_confirmation_record
        : null;

      state.latestCandidateConfirmationMessageId = candidate ? String(message.message_id || "") : null;
      state.latestCandidateConfirmationArtifactId = candidate ? String(message.artifact_id || "") : "";
      state.latestCandidateConfirmationCandidateId = candidate ? String(candidate.candidate_id || "") : "";
      state.latestCandidateConfirmationCandidateUpdatedAt = candidate ? String(candidate.updated_at || "") : "";
      state.latestCandidateConfirmationRecordedAt = confirmationRecord ? String(confirmationRecord.recorded_at || "") : "";

      updateCandidateConfirmationState();
    }

    function setFeedbackButtonsState(container, selectedLabel, disabled) {
      const buttons = Array.from(container.querySelectorAll(".feedback-button"));
      buttons.forEach((button) => {
        const value = String(button.dataset.feedbackValue || "");
        button.classList.toggle("active", Boolean(selectedLabel) && value === selectedLabel);
        button.disabled = Boolean(disabled);
      });
    }

    function buildFeedbackControls(message) {
      if (!message || message.role === "user" || !message.message_id) return null;

      const wrapper = document.createElement("div");
      wrapper.className = "feedback-bar";

      const status = document.createElement("div");
      status.className = "hint";
      const currentLabel = formatFeedbackLabel(message.feedback?.label || "");
      const currentReason = formatFeedbackReasonLabel(message.feedback?.reason || "");
      status.textContent = currentLabel
        ? `현재 피드백: ${currentLabel}${currentReason ? ` · ${currentReason}` : ""}`
        : "이 응답이 실제로 도움이 되었는지 표시해 두면 나중에 품질을 다듬는 데 쓸 수 있습니다.";
      wrapper.appendChild(status);

      const actions = document.createElement("div");
      actions.className = "feedback-actions";
      [
        ["helpful", "도움 됨"],
        ["unclear", "애매함"],
        ["incorrect", "틀림"],
      ].forEach(([value, label]) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "feedback-button";
        button.dataset.feedbackValue = value;
        button.textContent = label;
        button.disabled = state.isBusy;
        if (message.feedback?.label === value) {
          button.classList.add("active");
        }
        button.addEventListener("click", () => {
          submitFeedback(message.message_id, value, message.feedback?.reason || "").catch(renderError);
        });
        actions.appendChild(button);
      });
      wrapper.appendChild(actions);
      return wrapper;
    }

    function applyStatusBadge(element, status) {
      if (!element) return;
      const normalized = String(status || "answer").trim() || "answer";
      element.className = `status-pill ${normalized.replace(/_/g, "-")}`;
      element.textContent = compactStatusLabel(normalized);
    }

    function setCollapsiblePanel(panel, body, toggleButton, visible, labelText) {
      showElement(panel, visible);
      if (!visible) {
        body.classList.add("hidden");
        if (toggleButton) toggleButton.textContent = "펼치기";
        return;
      }
      body.classList.add("hidden");
      if (toggleButton) {
        toggleButton.textContent = labelText ? `${labelText} 펼치기` : "펼치기";
      }
    }

    function togglePanelBody(body, toggleButton, collapsedLabel, expandedLabel) {
      const hidden = body.classList.toggle("hidden");
      if (toggleButton) {
        toggleButton.textContent = hidden ? collapsedLabel : expandedLabel;
      }
    }

    function renderPanelHint(element, message) {
      if (!element) return;
      const text = String(message || "").trim();
      showElement(element, Boolean(text));
      element.textContent = text;
    }

    async function copyTextValue(text, successMessage = "경로를 복사했습니다.") {
      const value = String(text || "").trim();
      if (!value) return;
      if (navigator.clipboard?.writeText) {
        try {
          await navigator.clipboard.writeText(value);
          renderNotice(successMessage);
        } catch (_clipboardError) {
          renderNotice("클립보드 복사에 실패했습니다. 브라우저 권한을 확인하거나 텍스트를 직접 선택해 복사해 주세요.");
        }
        return;
      }

      const helper = document.createElement("textarea");
      helper.value = value;
      helper.style.position = "fixed";
      helper.style.opacity = "0";
      document.body.appendChild(helper);
      helper.select();
      const copied = document.execCommand("copy");
      document.body.removeChild(helper);
      if (copied) {
        renderNotice(successMessage);
      } else {
        renderNotice("클립보드 복사에 실패했습니다. 텍스트를 직접 선택해 복사해 주세요.");
      }
    }

    function renderResponseSummary(response, runtime) {
      const responseStatus = response?.status || "";
      const parts = [];
      if (responseStatus) parts.push(`상태 ${compactStatusLabel(responseStatus)}`);
      const srcLabel = getSourceTypeLabel(response);
      if (srcLabel) parts.push(srcLabel);
      if (response?.selected_source_paths?.length === 1) {
        const sourceName = String(response.selected_source_paths[0] || "").split(/[\\/]/).filter(Boolean).pop() || "출처 1개";
        parts.push(`출처 ${sourceName}`);
      } else if (response?.selected_source_paths?.length > 1) {
        parts.push(`출처 ${response.selected_source_paths.length}개`);
      }
      if (response?.evidence?.length) parts.push(`근거 ${response.evidence.length}개`);
      if (response?.summary_chunks?.length) parts.push(`요약 구간 ${response.summary_chunks.length}개`);
      if (runtime?.provider) parts.push(`런타임 ${runtime.provider}`);
      if (response?.requires_approval) parts.push("승인 대기");
      if (response?.feedback?.label) {
        const feedbackLabel = formatFeedbackLabel(response.feedback.label);
        const feedbackReason = formatFeedbackReasonLabel(response.feedback.reason || "");
        parts.push(`피드백 ${feedbackLabel}${feedbackReason ? ` · ${feedbackReason}` : ""}`);
      }
      if (usesCorrectedSaveSnapshot(response)) {
        parts.push("저장 기준 요청 시점 수정본 스냅샷");
      }
      if (usesRejectedContentVerdict(response)) {
        parts.push("내용 거절 기록됨");
      } else if (String(response?.corrected_outcome?.outcome || "").trim().toLowerCase() === "corrected") {
        parts.push("교정본 기록됨");
      }
      showElement(responseQuickMeta, parts.length > 0 || Boolean(response?.saved_note_path) || Boolean(response?.web_search_record_path));
      responseQuickMetaText.textContent = parts.join(" · ");

      const savedPath = response?.saved_note_path || "";
      showElement(responseSavedPathRow, Boolean(savedPath));
      responseSavedPath.textContent = savedPath ? compactDisplayPath(savedPath) : "";
      responseCopyPathButton.dataset.path = savedPath;

      const searchRecordPath = response?.web_search_record_path || "";
      showElement(responseSearchRecordRow, Boolean(searchRecordPath));
      responseSearchRecord.textContent = searchRecordPath ? compactDisplayPath(searchRecordPath) : "";
      responseCopySearchRecordButton.dataset.path = searchRecordPath;
    }

    function renderResponseFeedback(message, userText = "") {
      state.latestAssistantMessageId = message?.message_id || null;
      state.latestAssistantUserText = String(userText || "").trim();
      state.latestAssistantFeedbackLabel = String(message?.feedback?.label || "");
      state.latestAssistantFeedbackReason = String(message?.feedback?.reason || "");
      showElement(responseFeedbackBox, Boolean(message && message.message_id));
      if (!message || !message.message_id) {
        responseFeedbackStatus.textContent = "";
        responseFeedbackReasonStatus.textContent = "";
        setFeedbackButtonsState(responseFeedbackBox, "", true);
        showElement(responseFeedbackDetailBox, false);
        setFeedbackButtonsState(responseFeedbackDetailBox, "", true);
        responseFeedbackRetryButton.disabled = true;
        return;
      }

      const currentLabel = formatFeedbackLabel(message.feedback?.label || "");
      const currentReason = formatFeedbackReasonLabel(message.feedback?.reason || "");
      responseFeedbackStatus.textContent = currentLabel
        ? `현재 선택된 피드백: ${currentLabel}${currentReason ? ` · ${currentReason}` : ""}`
        : "방금 응답이 실제로 도움이 되었는지 표시해 두시면, 나중에 어떤 답변이 애매했는지 추적할 수 있습니다.";
      setFeedbackButtonsState(responseFeedbackBox, String(message.feedback?.label || ""), state.isBusy);

      const needsReason = ["unclear", "incorrect"].includes(String(message.feedback?.label || ""));
      showElement(responseFeedbackDetailBox, needsReason);
      if (!needsReason) {
        responseFeedbackReasonStatus.textContent = "";
        setFeedbackButtonsState(responseFeedbackDetailBox, "", true);
        responseFeedbackRetryButton.disabled = true;
        return;
      }

      responseFeedbackReasonStatus.textContent = currentReason
        ? `현재 문제 유형: ${currentReason}`
        : "어떤 점이 문제였는지 고르면, 같은 세션 문맥에서 다시 답변할 때 더 명확하게 반영할 수 있습니다.";
      setFeedbackButtonsState(responseFeedbackDetailBox, String(message.feedback?.reason || ""), state.isBusy);
      responseFeedbackRetryButton.disabled = state.isBusy;
    }

    function updateContentVerdictState() {
      const hasMessage = Boolean(state.latestContentVerdictMessageId);
      const currentApprovalMatchesArtifact = Boolean(
        state.currentApproval
        && String(state.currentApproval.artifact_id || "").trim()
        && String(state.currentApproval.artifact_id || "").trim() === String(state.latestContentVerdictArtifactId || "").trim()
      );
      const isRejected = state.latestContentVerdictOutcome === "rejected";

      responseContentRejectButton.disabled = state.isBusy || !hasMessage || isRejected;
      if (!hasMessage) {
        responseContentVerdictState.textContent = "";
        responseContentVerdictStatus.textContent = "";
        responseContentRejectButton.title = "";
        updateContentReasonNoteState();
        return;
      }

      if (isRejected) {
        responseContentVerdictState.textContent = state.latestContentVerdictRecordedAt
          ? `내용 거절 기록됨 · ${formatWhen(state.latestContentVerdictRecordedAt)}`
          : "내용 거절 기록됨";
        const statusParts = [
          "이 답변 내용을 거절로 기록했습니다.",
          "저장 승인 거절과는 별도입니다.",
          "아래 수정본 기록이나 저장 요청은 계속 별도 흐름으로 사용할 수 있습니다.",
        ];
        if (currentApprovalMatchesArtifact) {
          statusParts.push("이미 열린 저장 승인 카드는 그대로 유지되며 자동 취소되지 않습니다.");
        }
        if (hasSavedHistoryForArtifact(state.latestContentVerdictArtifactId)) {
          statusParts.push("이미 저장된 노트와 경로는 그대로 남고, 이번 내용 거절은 최신 판정만 바꿉니다.");
        }
        responseContentVerdictStatus.textContent = statusParts.join(" ");
        responseContentRejectButton.title = "이미 내용 거절로 기록되었습니다.";
        updateContentReasonNoteState();
        return;
      }

      if (state.latestContentVerdictOutcome === "corrected") {
        responseContentVerdictState.textContent = "최신 내용 판정은 기록된 수정본입니다.";
      } else if (state.latestContentVerdictOutcome === "accepted_as_is") {
        responseContentVerdictState.textContent = "최신 내용 판정은 원문 저장 승인입니다.";
      } else {
        responseContentVerdictState.textContent = "내용 거절은 아직 기록되지 않았습니다.";
      }
      const statusParts = [
        "저장 승인 거절과는 별도입니다.",
        "이 버튼을 누르면 grounded-brief 원문 응답에 내용 거절을 즉시 기록합니다.",
      ];
      if (currentApprovalMatchesArtifact) {
        statusParts.push("이미 열린 저장 승인 카드는 그대로 유지되며 자동 취소되지 않습니다.");
      }
      responseContentVerdictStatus.textContent = statusParts.join(" ");
      responseContentRejectButton.title = "이 답변 내용을 거절로 기록합니다.";
      updateContentReasonNoteState();
    }

    function updateContentReasonNoteState() {
      const hasMessage = Boolean(state.latestContentVerdictMessageId);
      const isRejected = state.latestContentVerdictOutcome === "rejected";
      const showReasonBox = hasMessage && isRejected;
      const currentNote = normalizeMultilineText(responseContentReasonInput.value);
      const recordedNote = normalizeMultilineText(state.latestContentReasonNote);

      showElement(responseContentReasonBox, showReasonBox);
      responseContentReasonInput.disabled = state.isBusy || !showReasonBox;
      responseContentReasonSubmitButton.disabled = state.isBusy || !showReasonBox || !currentNote;

      if (!showReasonBox) {
        responseContentReasonStatus.textContent = "";
        responseContentReasonSubmitButton.title = "";
        return;
      }

      if (recordedNote && !currentNote) {
        responseContentReasonStatus.textContent = "빈 제출로 기록된 거절 메모를 지우는 동작은 아직 지원하지 않습니다.";
        responseContentReasonSubmitButton.title = "빈 메모 제출은 아직 지원하지 않습니다.";
        return;
      }

      if (currentNote && currentNote !== recordedNote) {
        responseContentReasonStatus.textContent = recordedNote
          ? "수정 중인 거절 메모가 아직 다시 기록되지 않았습니다."
          : "선택 사항입니다. 내용 거절만으로도 판정은 유효하고, 이 메모는 그 기록을 보강합니다.";
        responseContentReasonSubmitButton.title = "현재 입력한 거절 메모를 source message에 기록합니다.";
        return;
      }

      if (recordedNote) {
        responseContentReasonStatus.textContent = state.latestContentReasonRecordedAt
          ? `기록된 거절 메모가 있습니다 · ${formatWhen(state.latestContentReasonRecordedAt)}`
          : "기록된 거절 메모가 있습니다.";
        responseContentReasonSubmitButton.title = "같은 source message의 거절 메모를 다시 기록합니다.";
        return;
      }

      responseContentReasonStatus.textContent = "선택 사항입니다. 비워 두면 메모 기록 버튼이 켜지지 않으며, 내용 거절만으로도 현재 verdict는 유효합니다.";
      responseContentReasonSubmitButton.title = "메모를 입력하면 같은 source message에 기록합니다.";
    }

    function renderContentVerdictControl(message) {
      const editable = canEditGroundedBrief(message);
      showElement(responseContentVerdictBox, editable);
      state.latestContentVerdictMessageId = editable ? String(message.message_id || "") : null;
      state.latestContentVerdictArtifactId = editable ? String(message.artifact_id || "") : "";
      state.latestContentVerdictOutcome = editable
        ? String(message?.corrected_outcome?.outcome || "").trim().toLowerCase()
        : "";
      state.latestContentVerdictRecordedAt = editable ? String(message?.corrected_outcome?.recorded_at || "") : "";
      state.latestContentReasonNote = editable ? normalizeMultilineText(message?.content_reason_record?.reason_note || "") : "";
      state.latestContentReasonRecordedAt = editable ? String(message?.content_reason_record?.recorded_at || "") : "";
      responseContentReasonInput.value = state.latestContentReasonNote || "";

      if (!editable) {
        responseContentVerdictState.textContent = "";
        responseContentVerdictStatus.textContent = "";
        responseContentRejectButton.title = "";
        responseContentReasonStatus.textContent = "";
        responseContentReasonSubmitButton.title = "";
        return;
      }

      updateContentVerdictState();
    }

    async function submitFeedback(messageId, feedbackLabel, feedbackReason = "") {
      if (!messageId || state.isBusy) return;
      const data = await fetchJson("/api/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: state.currentSessionId,
          message_id: messageId,
          feedback_label: feedbackLabel,
          feedback_reason: feedbackReason || undefined,
        }),
      });
      if (data.session) {
        renderSession(data.session);
        renderApproval((data.session.pending_approvals || []).slice(-1)[0] || null);
        const latestAssistantContext = findLatestAssistantContext(data.session.messages || []);
        renderCorrectionEditor(
          resolveCorrectionTargetMessage(data.session.messages || [], latestAssistantContext.assistant)
        );
      }
      const reasonText = formatFeedbackReasonLabel(feedbackReason);
      renderNotice(
        `피드백을 '${formatFeedbackLabel(feedbackLabel)}'${reasonText ? ` · '${reasonText}'` : ""}으로 기록했습니다.`
      );
    }

    async function submitCorrection() {
      if (state.isBusy || !state.latestCorrectionMessageId) return;
      const data = await fetchJson("/api/correction", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: state.currentSessionId,
          message_id: state.latestCorrectionMessageId,
          corrected_text: responseCorrectionInput.value,
        }),
      });
      if (data.session) {
        renderSession(data.session);
        renderApproval((data.session.pending_approvals || []).slice(-1)[0] || null);
        const latestAssistantContext = findLatestAssistantContext(data.session.messages || []);
        renderCorrectionEditor(
          resolveCorrectionTargetMessage(data.session.messages || [], latestAssistantContext.assistant)
        );
      }
      renderNotice("수정본을 기록했습니다. 저장 승인은 별도 흐름으로 유지됩니다.");
    }

    async function submitCandidateConfirmation() {
      if (
        state.isBusy
        || !state.latestCandidateConfirmationMessageId
        || !state.latestCandidateConfirmationCandidateId
        || !state.latestCandidateConfirmationCandidateUpdatedAt
      ) return;
      const data = await fetchJson("/api/candidate-confirmation", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: state.currentSessionId,
          message_id: state.latestCandidateConfirmationMessageId,
          candidate_id: state.latestCandidateConfirmationCandidateId,
          candidate_updated_at: state.latestCandidateConfirmationCandidateUpdatedAt,
        }),
      });
      if (data.session) {
        renderSession(data.session);
        renderApproval((data.session.pending_approvals || []).slice(-1)[0] || null);
      }
      renderNotice("현재 수정 방향을 나중에도 다시 써도 된다는 확인을 기록했습니다. 저장 승인과는 별도입니다.");
    }

    async function submitCandidateReviewAccept(item) {
      if (state.isBusy || !item || typeof item !== "object") return;
      const sourceMessageId = String(item.source_message_id || "").trim();
      const candidateId = String(item.candidate_id || "").trim();
      const confirmationRef = Array.isArray(item.supporting_confirmation_refs)
        ? item.supporting_confirmation_refs.find((ref) => ref && typeof ref === "object")
        : null;
      const candidateUpdatedAt = String(confirmationRef?.candidate_updated_at || "").trim();
      if (!sourceMessageId || !candidateId || !candidateUpdatedAt) return;

      const data = await fetchJson("/api/candidate-review", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: state.currentSessionId,
          message_id: sourceMessageId,
          candidate_id: candidateId,
          candidate_updated_at: candidateUpdatedAt,
          review_action: "accept",
        }),
      });
      if (data.session) {
        renderSession(data.session);
        renderApproval((data.session.pending_approvals || []).slice(-1)[0] || null);
      }
      renderNotice("검토 후보를 수락했습니다. 아직 적용되지는 않았습니다.");
    }

    async function submitContentVerdict() {
      if (state.isBusy || !state.latestContentVerdictMessageId || state.latestContentVerdictOutcome === "rejected") return;
      const data = await fetchJson("/api/content-verdict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: state.currentSessionId,
          message_id: state.latestContentVerdictMessageId,
          content_verdict: "rejected",
        }),
      });
      if (data.session) {
        renderSession(data.session);
        renderApproval((data.session.pending_approvals || []).slice(-1)[0] || null);
      }
      const savedHistoryExists = hasSavedHistoryForArtifact(
        String(data?.artifact_id || state.latestContentVerdictArtifactId || "").trim()
      );
      renderNotice(
        savedHistoryExists
          ? "내용 거절을 기록했습니다. 이미 저장된 노트는 그대로 유지되며 최신 내용 판정만 바뀝니다."
          : "내용 거절을 기록했습니다. 저장 승인 거절과는 별도입니다."
      );
    }

    async function submitContentReasonNote() {
      if (state.isBusy || !state.latestContentVerdictMessageId || state.latestContentVerdictOutcome !== "rejected") return;
      const reasonNote = normalizeMultilineText(responseContentReasonInput.value);
      if (!reasonNote) return;
      const data = await fetchJson("/api/content-reason-note", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: state.currentSessionId,
          message_id: state.latestContentVerdictMessageId,
          reason_note: reasonNote,
        }),
      });
      if (data.session) {
        renderSession(data.session);
        renderApproval((data.session.pending_approvals || []).slice(-1)[0] || null);
      }
      renderNotice("거절 메모를 기록했습니다. 내용 거절 판정은 그대로 유지됩니다.");
    }

    async function submitCorrectedSaveRequest() {
      if (state.isBusy || !state.latestCorrectionMessageId || !normalizeMultilineText(state.latestCorrectionRecordedText)) return;
      try {
        startProgress("corrected_save", "system", "승인 워크플로");
        responseText.textContent = "";
        showElement(responseCopyTextButton, false);
        renderResponseOrigin({ provider: "system", badge: "SYSTEM", label: "시스템 응답", kind: C.ResponseOriginKind.APPROVAL });
        const data = await submitStreamPayload({
          session_id: state.currentSessionId,
          corrected_save_message_id: state.latestCorrectionMessageId,
        });
        if (data?.cancelled) {
          renderNotice(data.message || "요청을 취소했습니다.");
          await fetchSessions();
          return;
        }
        renderResult(data);
        await fetchSessions();
        if (data?.response?.status === "needs_approval") {
          renderNotice("기록된 수정본 기준 저장 승인을 만들었습니다.");
        }
      } finally {
        stopProgress();
      }
    }

    async function retryLatestAssistantWithFeedback() {
      if (state.isBusy || !state.latestAssistantMessageId || !state.latestAssistantFeedbackLabel) return;
      const feedbackLabel = formatFeedbackLabel(state.latestAssistantFeedbackLabel);
      const feedbackReason = formatFeedbackReasonLabel(state.latestAssistantFeedbackReason);
      const basePrompt = state.latestAssistantUserText || "방금 답변";
      const guidance = feedbackReason
        ? `${feedbackLabel} 이유는 '${feedbackReason}'입니다.`
        : `${feedbackLabel} 피드백이 있었습니다.`;
      const retryPrompt = `${basePrompt}\n\n방금 답변은 ${guidance} 같은 세션 문맥과 근거를 기준으로 더 정확하고 관련성 높게 다시 답변해 주세요. 불필요한 잡정보는 줄이고 수정된 최종 답만 간결하게 보여 주세요.`;
      await sendRequest(
        {
          user_text: retryPrompt,
          retry_feedback_label: state.latestAssistantFeedbackLabel,
          retry_feedback_reason: state.latestAssistantFeedbackReason || undefined,
          retry_target_message_id: state.latestAssistantMessageId,
        },
        "follow_up"
      );
    }

    function renderEvidence(evidence) {
      const items = Array.isArray(evidence) ? evidence.filter((item) => item && typeof item === "object") : [];
      setCollapsiblePanel(evidenceBox, evidenceBody, evidenceToggleButton, items.length > 0, `근거 ${items.length}개`);
      if (items.length === 0) {
        renderPanelHint(evidenceHint, "");
        evidenceText.textContent = "";
        return;
      }

      const uniquePaths = [...new Set(items.map((item) => String(item.source_path || "").trim()).filter(Boolean))];
      const sharedPath = uniquePaths.length === 1 ? uniquePaths[0] : "";
      const sharedSourceName = sharedPath ? (items[0]?.source_name || "(출처 없음)") : "";
      const counts = sourceNameCounts(items);
      const lines = [];
      if (sharedPath) {
        lines.push(`공통 출처: ${sharedSourceName}`);
        lines.push(`경로: ${compactDisplayPath(sharedPath)}`);
        lines.push("");
      }

      items.forEach((item, index) => {
        const label = item.label || "문서 근거";
        const sourceName = item.source_name || "(출처 없음)";
        const sourcePath = item.source_path || "";
        const sourceRole = item.source_role || "";
        const snippet = truncateDisplayText(item.snippet || "");
        const duplicateName = counts[sourceName] > 1;
        const roleSuffix = sourceRole ? ` [${formatSourceRoleCompact(sourceRole)}]` : "";
        const titleSuffix = sharedPath ? roleSuffix : ` · ${sourceName}${roleSuffix}`;
        lines.push(`${index + 1}. ${label}${titleSuffix}`);
        if (!sharedPath && duplicateName && sourcePath) {
          lines.push(`   경로: ${compactDisplayPath(sourcePath)}`);
        }
        lines.push(`   근거: ${snippet}`);
      });
      renderPanelHint(
        evidenceHint,
        items.length > 3 ? "근거가 많으면 이 패널 안에서 스크롤해 이어서 확인하실 수 있습니다." : ""
      );
      if (evidenceScrollRegion) evidenceScrollRegion.scrollTop = 0;
      evidenceText.textContent = lines.join("\n");
    }

    function renderSummaryChunks(summaryChunks) {
      const items = Array.isArray(summaryChunks) ? summaryChunks.filter((item) => item && typeof item === "object") : [];
      setCollapsiblePanel(summaryChunksBox, summaryChunksBody, summaryChunksToggleButton, items.length > 0, `구간 ${items.length}개`);
      if (items.length === 0) {
        renderPanelHint(summaryChunksHint, "");
        summaryChunksText.textContent = "";
        return;
      }

      const uniquePaths = [...new Set(items.map((item) => String(item.source_path || "").trim()).filter(Boolean))];
      const sharedPath = uniquePaths.length === 1 ? uniquePaths[0] : "";
      const sharedSourceName = sharedPath ? (items[0]?.source_name || "(출처 없음)") : "";
      const counts = sourceNameCounts(items);
      const totalChunkCounts = items
        .map((item) => Number(item.total_chunks || 0))
        .filter((value) => Number.isFinite(value) && value > 0);
      const maxTotalChunks = totalChunkCounts.length > 0 ? Math.max(...totalChunkCounts) : 0;
      const lines = [];
      if (sharedPath) {
        lines.push(`공통 출처: ${sharedSourceName}`);
        lines.push(`경로: ${compactDisplayPath(sharedPath)}`);
        lines.push("");
      }

      items.forEach((item, index) => {
        const sourceName = item.source_name || "(출처 없음)";
        const sourcePath = item.source_path || "";
        const chunkIndex = Number(item.chunk_index || 0);
        const totalChunks = Number(item.total_chunks || 0);
        const selectedLine = truncateDisplayText(item.selected_line || "");
        const chunkLocation = chunkIndex > 0 && totalChunks > 0
          ? `전체 ${totalChunks}개 중 ${chunkIndex}번째`
          : (item.chunk_id || `chunk-${index + 1}`);

        const duplicateName = counts[sourceName] > 1;
        const titleSuffix = sharedPath ? "" : ` · ${sourceName}`;
        lines.push(`${index + 1}. 대표 구간${titleSuffix}`);
        lines.push(`   위치: ${chunkLocation}`);
        if (!sharedPath && duplicateName && sourcePath) {
          lines.push(`   경로: ${compactDisplayPath(sourcePath)}`);
        }
        lines.push(`   반영 내용: ${selectedLine}`);
      });
      renderPanelHint(
        summaryChunksHint,
        maxTotalChunks > items.length
          ? `여기에는 전체 ${maxTotalChunks}개 구간을 모두 나열하지 않고, 최종 요약에 실제 반영된 대표 구간 ${items.length}개만 보여줍니다. 항목이 많으면 이 패널 안에서 스크롤해 이어서 확인하실 수 있습니다.`
          : (items.length > 3 ? "대표 구간이 많으면 이 패널 안에서 스크롤해 이어서 확인하실 수 있습니다." : "")
      );
      if (summaryChunksScrollRegion) summaryChunksScrollRegion.scrollTop = 0;
      summaryChunksText.textContent = lines.join("\n");
    }

    function summarizeClaimCoverageCounts(claimCoverage) {
      const items = Array.isArray(claimCoverage) ? claimCoverage.filter((item) => item && typeof item === "object") : [];
      const counts = { strong: 0, weak: 0, missing: 0 };
      items.forEach((item) => {
        const status = String(item.status || "").trim();
        if (status === C.CoverageStatus.STRONG) counts.strong += 1;
        else if (status === C.CoverageStatus.WEAK) counts.weak += 1;
        else if (status === C.CoverageStatus.MISSING) counts.missing += 1;
      });
      return counts;
    }

    function renderFactStrengthBar(claimCoverage) {
      const counts = summarizeClaimCoverageCounts(claimCoverage);
      const total = counts.strong + counts.weak + counts.missing;
      if (total === 0) {
        showElement(factStrengthBar, false);
        return;
      }
      factStrengthBar.innerHTML = "";
      const label = document.createElement("span");
      label.textContent = "사실 검증:";
      label.style.fontWeight = "600";
      factStrengthBar.appendChild(label);
      if (counts.strong > 0) {
        const group = document.createElement("span");
        group.className = "fact-group";
        const badge = document.createElement("span");
        badge.className = "fact-count strong";
        badge.textContent = counts.strong;
        group.appendChild(badge);
        group.appendChild(document.createTextNode(" 교차 확인"));
        factStrengthBar.appendChild(group);
      }
      if (counts.weak > 0) {
        const group = document.createElement("span");
        group.className = "fact-group";
        const badge = document.createElement("span");
        badge.className = "fact-count weak";
        badge.textContent = counts.weak;
        group.appendChild(badge);
        group.appendChild(document.createTextNode(" 단일 출처"));
        factStrengthBar.appendChild(group);
      }
      if (counts.missing > 0) {
        const group = document.createElement("span");
        group.className = "fact-group";
        const badge = document.createElement("span");
        badge.className = "fact-count missing";
        badge.textContent = counts.missing;
        group.appendChild(badge);
        group.appendChild(document.createTextNode(" 미확인"));
        factStrengthBar.appendChild(group);
      }
      showElement(factStrengthBar, true);
    }

    function formatClaimCoverageSummary(claimCoverage) {
      const counts = summarizeClaimCoverageCounts(claimCoverage);
      return formatClaimCoverageCountSummary(counts);
    }

    function formatClaimCoverageCountSummary(counts) {
      const normalized = counts && typeof counts === "object" ? counts : {};
      const parts = [];
      if (Number(normalized.strong || 0) > 0) parts.push(`교차 확인 ${Number(normalized.strong || 0)}`);
      if (Number(normalized.weak || 0) > 0) parts.push(`단일 출처 ${Number(normalized.weak || 0)}`);
      if (Number(normalized.missing || 0) > 0) parts.push(`미확인 ${Number(normalized.missing || 0)}`);
      return parts.join(" · ");
    }

    function formatAnswerModeLabel(answerMode) {
      const normalized = String(answerMode || C.AnswerMode.GENERAL).trim();
      if (normalized === C.AnswerMode.ENTITY_CARD) return "설명 카드";
      if (normalized === C.AnswerMode.LATEST_UPDATE) return "최신 확인";
      return "일반 검색";
    }

    function formatSourceRoleWithTrust(sourceRole) {
      const role = String(sourceRole || "").trim();
      if (!role) return "";
      const trustMap = {
        "공식 기반": "높음",
        "백과 기반": "높음",
        "데이터 기반": "높음",
        "보조 기사": "보통",
        "설명형 출처": "보통",
        "보조 커뮤니티": "낮음",
        "보조 출처": "낮음",
      };
      const trust = trustMap[role];
      return trust ? `${role} (신뢰도 ${trust})` : role;
    }

    function formatSourceRoleCompact(sourceRole) {
      const role = String(sourceRole || "").trim();
      if (!role) return "";
      const trustMap = {
        "공식 기반": "높음",
        "백과 기반": "높음",
        "데이터 기반": "높음",
        "보조 기사": "보통",
        "설명형 출처": "보통",
        "보조 커뮤니티": "낮음",
        "보조 출처": "낮음",
      };
      const trust = trustMap[role];
      return trust ? `${role}(${trust})` : role;
    }

    function formatVerificationLabel(label) {
      const normalized = String(label || "").trim();
      if (!normalized) return "";
      const strongLabels = ["공식+기사 교차 확인", "공식 확인 중심", "기사 교차 확인", "설명형 다중 출처 합의"];
      const mediumLabels = ["공식 단일 출처", "설명형 단일 출처"];
      if (strongLabels.includes(normalized)) return `검증: ${normalized} [강]`;
      if (mediumLabels.includes(normalized)) return `검증: ${normalized} [중]`;
      return `검증: ${normalized} [약]`;
    }

    function verificationStrengthClass(label) {
      const normalized = String(label || "").trim();
      const strongLabels = ["공식+기사 교차 확인", "공식 확인 중심", "기사 교차 확인", "설명형 다중 출처 합의"];
      const mediumLabels = ["공식 단일 출처", "설명형 단일 출처"];
      if (strongLabels.includes(normalized)) return "ver-strong";
      if (mediumLabels.includes(normalized)) return "ver-medium";
      return "ver-weak";
    }

    function formatVerificationBadge(label) {
      const normalized = String(label || "").trim();
      if (!normalized) return "";
      const strongLabels = ["공식+기사 교차 확인", "공식 확인 중심", "기사 교차 확인", "설명형 다중 출처 합의"];
      const mediumLabels = ["공식 단일 출처", "설명형 단일 출처"];
      if (strongLabels.includes(normalized)) return `검증 강`;
      if (mediumLabels.includes(normalized)) return `검증 중`;
      return `검증 약`;
    }

    function sourceRoleTrustClass(sourceRole) {
      const role = String(sourceRole || "").trim();
      const highRoles = ["공식 기반", "백과 기반", "데이터 기반"];
      const mediumRoles = ["보조 기사", "설명형 출처"];
      if (highRoles.includes(role)) return "trust-high";
      if (mediumRoles.includes(role)) return "trust-medium";
      return "trust-low";
    }

    function formatClaimRenderedAs(renderedAs) {
      const normalized = String(renderedAs || "").trim();
      if (normalized === "fact_card") return "사실 카드 반영";
      if (normalized === "uncertain") return "불확실 정보 반영";
      if (normalized === "not_rendered") return "아직 본문 미반영";
      return "";
    }

    function formatClaimProgress(item) {
      if (!item || typeof item !== "object") return "";
      const label = String(item.progress_label || "").trim();
      const previousLabel = String(item.previous_status_label || "").trim();
      const currentLabel = String(item.status_label || "").trim();
      if (!label) return "";
      if (!previousLabel || previousLabel === currentLabel) return label;
      return `${label} (${previousLabel} → ${currentLabel})`;
    }

    function renderClaimCoverage(claimCoverage, progressSummary = "") {
      const items = Array.isArray(claimCoverage) ? claimCoverage.filter((item) => item && typeof item === "object") : [];
      const summaryLabel = formatClaimCoverageSummary(items);
      setCollapsiblePanel(
        claimCoverageBox,
        claimCoverageBody,
        claimCoverageToggleButton,
        items.length > 0,
        summaryLabel || `슬롯 ${items.length}개`
      );
      if (items.length === 0) {
        renderPanelHint(claimCoverageHint, "");
        claimCoverageText.textContent = "";
        return;
      }

      const progressText = String(progressSummary || "").trim();
      const lines = [];
      items.forEach((item, index) => {
        const slot = item.slot || `슬롯 ${index + 1}`;
        const statusLabel = item.status_label || "검증 상태";
        const value = truncateDisplayText(item.value || "", 200);
        const supportCount = Number(item.support_count || 0);
        const candidateCount = Number(item.candidate_count || 0);
        const sourceRole = item.source_role || "";
        const renderedAs = formatClaimRenderedAs(item.rendered_as);
        const progressLabel = formatClaimProgress(item);
        const focusPrefix = item.is_focus_slot ? "재조사 대상 · " : "";

        lines.push(`${index + 1}. [${statusLabel}] ${slot}${focusPrefix ? ` · ${focusPrefix.replace(/ · $/, "")}` : ""}`);
        if (value) {
          lines.push(`   값: ${value}`);
        }
        if (statusLabel === "미확인") {
          lines.push(`   → 추가 출처가 필요합니다.`);
        } else if (statusLabel === "단일 출처") {
          lines.push(`   → 1개 출처만 확인됨. 교차 검증이 권장됩니다.`);
        }
        if (sourceRole) {
          lines.push(`   출처 유형: ${formatSourceRoleWithTrust(sourceRole)}`);
        }
        const metaParts = [];
        if (supportCount > 0) metaParts.push(`근거 ${supportCount}건`);
        if (candidateCount > supportCount) metaParts.push(`후보 ${candidateCount}건`);
        if (renderedAs) metaParts.push(`표시: ${renderedAs}`);
        if (progressLabel) metaParts.push(`변화: ${progressLabel}`);
        if (metaParts.length > 0) {
          lines.push(`   ${metaParts.join(" · ")}`);
        }
      });

      renderPanelHint(
        claimCoverageHint,
        progressText
          ? `${progressText} 교차 확인은 여러 출처 합의, 단일 출처는 신뢰 가능한 1개 출처 기준, 미확인은 추가 조사 필요 상태입니다.`
          : "교차 확인은 여러 출처 합의, 단일 출처는 신뢰 가능한 1개 출처 기준, 미확인은 추가 조사 필요 상태입니다."
      );
      if (claimCoverageScrollRegion) claimCoverageScrollRegion.scrollTop = 0;
      claimCoverageText.textContent = lines.join("\n");
    }

    function renderContext(context) {
      showElement(contextBox, Boolean(context));
      if (!context) {
        contextText.textContent = "";
        return;
      }

      const lines = [
        `문맥 종류: ${context.kind || "document"}`,
        `현재 문서: ${context.label || "(이름 없음)"}`,
      ];
      if (Array.isArray(context.source_paths) && context.source_paths.length > 0) {
        lines.push(`출처: ${context.source_paths.join(", ")}`);
      }
      if (context.record_path) {
        lines.push(`검색 기록: ${compactDisplayPath(context.record_path)}`);
      }
      if (context.summary_hint) {
        lines.push("");
        lines.push(context.summary_hint);
      }
      contextText.textContent = lines.join("\n");
    }

    function renderSuggestions(suggestions) {
      const items = Array.isArray(suggestions) ? suggestions.filter(Boolean) : [];
      showElement(suggestionsBox, items.length > 0);
      suggestionsList.innerHTML = "";
      items.forEach((promptText) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "secondary";
        button.textContent = promptText;
        button.addEventListener("click", () => {
          sendFollowUpPrompt(promptText);
        });
        suggestionsList.appendChild(button);
      });
    }

    function renderReviewQueue(items) {
      const reviewItems = Array.isArray(items) ? items.filter((item) => item && typeof item === "object") : [];
      showElement(reviewQueueBox, reviewItems.length > 0);
      reviewQueueList.innerHTML = "";

      if (reviewItems.length === 0) {
        reviewQueueStatus.textContent = "";
        return;
      }

      reviewQueueStatus.textContent = "현재 후보는 검토 수락만 기록할 수 있습니다. 아직 적용, 편집, 거절은 열지 않았습니다.";
      reviewItems.forEach((item) => {
        const card = document.createElement("article");
        card.className = "history-item";
        card.setAttribute("data-testid", "review-queue-item");

        const header = document.createElement("div");
        header.className = "history-item-header";

        const titleWrap = document.createElement("div");
        titleWrap.className = "history-item-title";
        const title = document.createElement("strong");
        title.textContent = item.statement || item.candidate_family || "검토 후보";
        titleWrap.appendChild(title);

        const meta = document.createElement("span");
        meta.textContent = [
          `기준 ${formatPromotionBasisLabel(item.promotion_basis)}`,
          `상태 ${formatPromotionEligibilityLabel(item.promotion_eligibility)}`,
          item.updated_at ? `업데이트 ${formatWhen(item.updated_at)}` : "",
        ].filter(Boolean).join(" · ");
        titleWrap.appendChild(meta);
        header.appendChild(titleWrap);
        card.appendChild(header);

        const anchor = document.createElement("div");
        anchor.className = "history-item-summary";
        anchor.textContent = [
          `artifact ${compactIdentifier(item.artifact_id, 10, 10)}`,
          `source ${compactIdentifier(item.source_message_id, 8, 8)}`,
        ].filter(Boolean).join(" · ");
        card.appendChild(anchor);

        const signalRefs = Array.isArray(item.supporting_signal_refs)
          ? item.supporting_signal_refs
            .map((ref) => formatSignalRefLabel(ref?.signal_name))
            .filter(Boolean)
          : [];
        if (signalRefs.length > 0) {
          const support = document.createElement("div");
          support.className = "history-item-summary";
          support.textContent = `근거 신호 ${signalRefs.join(", ")}`;
          card.appendChild(support);
        }

        const confirmationRef = Array.isArray(item.supporting_confirmation_refs)
          ? item.supporting_confirmation_refs.find((ref) => ref && typeof ref === "object")
          : null;
        if (confirmationRef) {
          const confirmation = document.createElement("div");
          confirmation.className = "history-item-summary";
          confirmation.textContent = [
            `확인 ${formatConfirmationLabel(confirmationRef.confirmation_label)}`,
            confirmationRef.recorded_at ? formatWhen(confirmationRef.recorded_at) : "",
          ].filter(Boolean).join(" · ");
          card.appendChild(confirmation);
        }

        const candidateUpdatedAt = String(confirmationRef?.candidate_updated_at || "").trim();
        if (item.source_message_id && item.candidate_id && candidateUpdatedAt) {
          const actions = document.createElement("div");
          actions.className = "button-row";

          const acceptButton = document.createElement("button");
          acceptButton.type = "button";
          acceptButton.className = "secondary";
          acceptButton.textContent = "검토 수락";
          acceptButton.setAttribute("data-testid", "review-queue-accept");
          acceptButton.addEventListener("click", () => {
            submitCandidateReviewAccept(item);
          });
          actions.appendChild(acceptButton);
          card.appendChild(actions);
        }

        reviewQueueList.appendChild(card);
      });
    }

    function renderAggregateTriggerSection(items) {
      const aggregateItems = Array.isArray(items) ? items.filter((item) => item && typeof item === "object") : [];
      showElement(aggregateTriggerBox, aggregateItems.length > 0);
      aggregateTriggerList.innerHTML = "";

      if (aggregateItems.length === 0) {
        aggregateTriggerStatus.textContent = "";
        return;
      }

      const hasUnblockedItem = aggregateItems.some((item) => isAggregateTriggerUnblocked(item));
      aggregateTriggerStatus.textContent = hasUnblockedItem
        ? "검토 메모 적용을 시작할 수 있는 묶음이 있습니다."
        : "현재 반복 교정 묶음은 aggregate 단위 경계만 보여주며, 아직 시작할 수 없습니다.";
      aggregateItems.forEach((item) => {
        const aggregateKey = item.aggregate_key && typeof item.aggregate_key === "object" ? item.aggregate_key : {};
        const capabilityOutcome = String(item.reviewed_memory_capability_status?.capability_outcome || "").trim() || "미확인";
        const auditStage = String(item.reviewed_memory_transition_audit_contract?.audit_stage || "").trim() || "미확인";
        const planningTargetLabel = String(item.reviewed_memory_planning_target_ref?.target_label || "").trim();
        const card = document.createElement("article");
        card.className = "history-item";
        card.setAttribute("data-testid", "aggregate-trigger-item");

        const header = document.createElement("div");
        header.className = "history-item-header";

        const titleWrap = document.createElement("div");
        titleWrap.className = "history-item-title";
        const title = document.createElement("strong");
        title.textContent = aggregateTriggerTitle(item);
        titleWrap.appendChild(title);

        const meta = document.createElement("span");
        meta.textContent = [
          Number.isFinite(Number(item.recurrence_count)) ? `반복 ${Number(item.recurrence_count)}회` : "",
          item.last_seen_at ? `마지막 확인 ${formatWhen(item.last_seen_at)}` : "",
          `capability ${capabilityOutcome}`,
          `audit ${auditStage}`,
        ].filter(Boolean).join(" · ");
        titleWrap.appendChild(meta);
        header.appendChild(titleWrap);
        card.appendChild(header);

        const identitySummary = document.createElement("div");
        identitySummary.className = "history-item-summary";
        identitySummary.textContent = [
          `family ${String(aggregateKey.candidate_family || "").trim() || "미확인"}`,
          `fingerprint ${compactIdentifier(aggregateKey.normalized_delta_fingerprint, 8, 8) || "미확인"}`,
        ].join(" · ");
        card.appendChild(identitySummary);

        if (planningTargetLabel) {
          const planningTarget = document.createElement("div");
          planningTarget.className = "history-item-summary";
          planningTarget.textContent = `계획 타깃 ${planningTargetLabel}`;
          card.appendChild(planningTarget);
        }

        const unblocked = isAggregateTriggerUnblocked(item);
        const transitionRecord = item.reviewed_memory_transition_record && typeof item.reviewed_memory_transition_record === "object"
          ? item.reviewed_memory_transition_record
          : null;
        const conflictVisibilityRecord = item.reviewed_memory_conflict_visibility_record && typeof item.reviewed_memory_conflict_visibility_record === "object"
          ? item.reviewed_memory_conflict_visibility_record
          : null;
        const recordStage = transitionRecord ? String(transitionRecord.record_stage || "").trim() : "";
        const hasEmittedRecord = recordStage === C.RecordStage.EMITTED;
        const hasAppliedPending = recordStage === C.RecordStage.APPLIED_PENDING;
        const hasAppliedResult = recordStage === C.RecordStage.APPLIED_WITH_RESULT;
        const hasStopped = recordStage === C.RecordStage.STOPPED;
        const hasReversed = recordStage === C.RecordStage.REVERSED;

        const helper = document.createElement("div");
        helper.className = "history-item-summary";
        helper.setAttribute("data-testid", "aggregate-trigger-helper");
        helper.textContent = hasReversed && conflictVisibilityRecord
          ? "충돌 확인이 완료되었습니다. 현재 aggregate 범위의 충돌 상태가 기록되었습니다."
          : hasReversed
          ? "검토 메모 적용이 되돌려졌습니다. 적용 효과가 완전히 철회되었습니다."
          : hasStopped
            ? "검토 메모 적용이 중단되었습니다. 이후 응답에 교정 패턴이 반영되지 않습니다."
            : hasAppliedResult
            ? "검토 메모 적용 효과가 활성화되었습니다. 이후 응답에 교정 패턴이 반영됩니다."
          : hasAppliedPending
            ? "검토 메모 적용이 실행되었습니다. 결과 확정 버튼을 눌러 주세요."
            : hasEmittedRecord
            ? `transition record가 발행되었습니다. 적용 실행 버튼을 눌러 주세요.`
            : aggregateTriggerBlockedHelper(item);
        card.appendChild(helper);

        const actions = document.createElement("div");
        actions.className = "button-row";

        const aggregateFingerprint = String(aggregateKey.normalized_delta_fingerprint || "").trim();

        if (hasReversed) {
          const reversedLabel = document.createElement("span");
          reversedLabel.className = "hint";
          reversedLabel.setAttribute("data-testid", "aggregate-trigger-reversed");
          reversedLabel.textContent = `적용 되돌림 완료 (${String(transitionRecord.canonical_transition_id || "").trim()})`;
          actions.appendChild(reversedLabel);

          if (conflictVisibilityRecord) {
            const conflictLabel = document.createElement("span");
            conflictLabel.className = "hint";
            conflictLabel.setAttribute("data-testid", "aggregate-trigger-conflict-checked");
            const entryCount = typeof conflictVisibilityRecord.conflict_entry_count === "number"
              ? conflictVisibilityRecord.conflict_entry_count : 0;
            conflictLabel.textContent = `충돌 확인 완료 (${String(conflictVisibilityRecord.canonical_transition_id || "").trim()} · 항목 ${entryCount}건)`;
            actions.appendChild(conflictLabel);

            const conflictEntries = Array.isArray(conflictVisibilityRecord.conflict_entries)
              ? conflictVisibilityRecord.conflict_entries : [];
            if (conflictEntries.length > 0) {
              const conflictList = document.createElement("ul");
              conflictList.className = "history-item-summary";
              conflictList.setAttribute("data-testid", "aggregate-trigger-conflict-entries");
              for (const entry of conflictEntries) {
                const li = document.createElement("li");
                li.textContent = `${String(entry.conflict_category || "")} — ${String(entry.detail || "")}`;
                conflictList.appendChild(li);
              }
              actions.appendChild(conflictList);
            }
          } else {
            const conflictCheckButton = document.createElement("button");
            conflictCheckButton.type = "button";
            conflictCheckButton.setAttribute("data-testid", "aggregate-trigger-conflict-check");
            conflictCheckButton.textContent = "충돌 확인";
            conflictCheckButton.addEventListener("click", async () => {
              conflictCheckButton.disabled = true;
              try {
                const data = await fetchJson("/api/aggregate-transition-conflict-check", {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({
                    session_id: state.currentSessionId,
                    aggregate_fingerprint: aggregateFingerprint,
                    canonical_transition_id: String(transitionRecord.canonical_transition_id || "").trim(),
                  }),
                });
                renderNotice(`충돌 확인이 완료되었습니다. (${data.canonical_transition_id})`);
                if (data.session) {
                  renderSession(data.session);
                }
              } catch (error) {
                renderError(error);
              }
            });
            actions.appendChild(conflictCheckButton);
          }
        } else if (hasStopped) {
          const stoppedLabel = document.createElement("span");
          stoppedLabel.className = "hint";
          stoppedLabel.setAttribute("data-testid", "aggregate-trigger-stopped");
          stoppedLabel.textContent = `적용 중단됨 (${String(transitionRecord.canonical_transition_id || "").trim()})`;
          actions.appendChild(stoppedLabel);

          const reverseButton = document.createElement("button");
          reverseButton.type = "button";
          reverseButton.className = "danger";
          reverseButton.textContent = "적용 되돌리기";
          reverseButton.setAttribute("data-testid", "aggregate-trigger-reverse");
          reverseButton.addEventListener("click", async () => {
            reverseButton.disabled = true;
            try {
              const data = await fetchJson("/api/aggregate-transition-reverse", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  session_id: state.currentSessionId,
                  aggregate_fingerprint: aggregateFingerprint,
                  canonical_transition_id: String(transitionRecord.canonical_transition_id || "").trim(),
                }),
              });
              renderNotice(`검토 메모 적용이 되돌려졌습니다. (${data.canonical_transition_id})`);
              if (data.session) {
                renderSession(data.session);
              }
            } catch (error) {
              renderError(error);
            }
          });
          actions.appendChild(reverseButton);
        } else if (hasAppliedResult) {
          const resultLabel = document.createElement("span");
          resultLabel.className = "hint";
          resultLabel.setAttribute("data-testid", "aggregate-trigger-result");
          const appliedEffect = transitionRecord.apply_result && typeof transitionRecord.apply_result === "object"
            ? String(transitionRecord.apply_result.applied_effect_kind || "").trim()
            : "";
          resultLabel.textContent = `결과 확정 완료 (${String(transitionRecord.canonical_transition_id || "").trim()}${appliedEffect ? ` · ${appliedEffect}` : ""})`;
          actions.appendChild(resultLabel);

          const stopButton = document.createElement("button");
          stopButton.type = "button";
          stopButton.className = "danger";
          stopButton.textContent = "적용 중단";
          stopButton.setAttribute("data-testid", "aggregate-trigger-stop");
          stopButton.addEventListener("click", async () => {
            stopButton.disabled = true;
            try {
              const data = await fetchJson("/api/aggregate-transition-stop", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  session_id: state.currentSessionId,
                  aggregate_fingerprint: aggregateFingerprint,
                  canonical_transition_id: String(transitionRecord.canonical_transition_id || "").trim(),
                }),
              });
              renderNotice(`검토 메모 적용이 중단되었습니다. (${data.canonical_transition_id})`);
              if (data.session) {
                renderSession(data.session);
              }
            } catch (error) {
              renderError(error);
            }
          });
          actions.appendChild(stopButton);
        } else if (hasAppliedPending) {
          const resultButton = document.createElement("button");
          resultButton.type = "button";
          resultButton.className = "primary";
          resultButton.textContent = "검토 메모 적용 결과 확정";
          resultButton.setAttribute("data-testid", "aggregate-trigger-confirm-result");
          resultButton.addEventListener("click", async () => {
            resultButton.disabled = true;
            try {
              const data = await fetchJson("/api/aggregate-transition-result", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  session_id: state.currentSessionId,
                  aggregate_fingerprint: aggregateFingerprint,
                  canonical_transition_id: String(transitionRecord.canonical_transition_id || "").trim(),
                }),
              });
              renderNotice(`검토 메모 적용 결과가 확정되었습니다. (${data.canonical_transition_id})`);
              if (data.session) {
                renderSession(data.session);
              }
            } catch (error) {
              renderError(error);
            }
          });
          actions.appendChild(resultButton);
        } else if (hasEmittedRecord) {
          const applyButton = document.createElement("button");
          applyButton.type = "button";
          applyButton.className = "primary";
          applyButton.textContent = "검토 메모 적용 실행";
          applyButton.setAttribute("data-testid", "aggregate-trigger-apply");
          applyButton.addEventListener("click", async () => {
            applyButton.disabled = true;
            try {
              const data = await fetchJson("/api/aggregate-transition-apply", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  session_id: state.currentSessionId,
                  aggregate_fingerprint: aggregateFingerprint,
                  canonical_transition_id: String(transitionRecord.canonical_transition_id || "").trim(),
                }),
              });
              renderNotice(`검토 메모 적용이 실행되었습니다. (${data.canonical_transition_id})`);
              if (data.session) {
                renderSession(data.session);
              }
            } catch (error) {
              renderError(error);
            }
          });
          actions.appendChild(applyButton);
        } else if (unblocked) {
          const noteInput = document.createElement("textarea");
          noteInput.className = "correction-input";
          noteInput.rows = 2;
          noteInput.placeholder = "적용 사유를 입력하세요 (필수)";
          noteInput.setAttribute("data-testid", "aggregate-trigger-note");
          card.appendChild(noteInput);

          const startButton = document.createElement("button");
          startButton.type = "button";
          startButton.className = "primary";
          startButton.textContent = "검토 메모 적용 시작";
          startButton.disabled = true;
          startButton.title = "사유를 입력하면 시작할 수 있습니다.";
          startButton.setAttribute("data-testid", "aggregate-trigger-start");
          noteInput.addEventListener("input", () => {
            startButton.disabled = !noteInput.value.trim();
          });
          startButton.addEventListener("click", async () => {
            const note = noteInput.value.trim();
            if (!note) return;
            startButton.disabled = true;
            try {
              const data = await fetchJson("/api/aggregate-transition", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  session_id: state.currentSessionId,
                  aggregate_fingerprint: aggregateFingerprint,
                  operator_reason_or_note: note,
                }),
              });
              renderNotice(`transition record가 발행되었습니다. (${data.canonical_transition_id})`);
              if (data.session) {
                renderSession(data.session);
              }
            } catch (error) {
              renderError(error);
            }
          });
          actions.appendChild(startButton);
        } else {
          const startButton = document.createElement("button");
          startButton.type = "button";
          startButton.className = "secondary";
          startButton.textContent = "검토 메모 적용 시작";
          startButton.disabled = true;
          startButton.title = aggregateTriggerBlockedHelper(item);
          startButton.setAttribute("data-testid", "aggregate-trigger-start");
          actions.appendChild(startButton);
        }
        card.appendChild(actions);

        aggregateTriggerList.appendChild(card);
      });
    }

    function renderSearchHistory(historyItems) {
      const items = Array.isArray(historyItems) ? historyItems.filter((item) => item && typeof item === "object") : [];
      showElement(searchHistoryBox, items.length > 0);
      searchHistoryList.innerHTML = "";
      searchHistoryMeta.textContent = items.length > 0 ? `최근 ${items.length}건` : "";
      if (items.length === 0) {
        return;
      }

      items.forEach((item) => {
        const card = document.createElement("article");
        card.className = "history-item";

        const header = document.createElement("div");
        header.className = "history-item-header";

        const titleWrap = document.createElement("div");
        titleWrap.className = "history-item-title";
        const title = document.createElement("strong");
        title.textContent = item.query || "검색 기록";
        titleWrap.appendChild(title);
        const answerMode = String(item.answer_mode || "").trim();
        const isInvestigation = answerMode === C.AnswerMode.ENTITY_CARD || answerMode === C.AnswerMode.LATEST_UPDATE;
        const badgeRow = document.createElement("div");
        badgeRow.className = "history-badge-row";
        let hasBadges = false;
        if (isInvestigation) {
          const modeBadge = document.createElement("span");
          modeBadge.className = "answer-mode-badge";
          modeBadge.textContent = formatAnswerModeLabel(answerMode);
          badgeRow.appendChild(modeBadge);
          hasBadges = true;
        }
        if (item.verification_label) {
          const verBadge = document.createElement("span");
          verBadge.className = `verification-badge ${verificationStrengthClass(item.verification_label)}`;
          verBadge.textContent = formatVerificationBadge(item.verification_label);
          badgeRow.appendChild(verBadge);
          hasBadges = true;
        }
        const headerSourceRoles = Array.isArray(item.source_roles)
          ? item.source_roles.map((role) => String(role || "").trim()).filter(Boolean)
          : [];
        if (headerSourceRoles.length > 0) {
          const uniqueRoles = [...new Set(headerSourceRoles)];
          uniqueRoles.forEach((role) => {
            const roleBadge = document.createElement("span");
            roleBadge.className = `source-role-badge ${sourceRoleTrustClass(role)}`;
            roleBadge.textContent = formatSourceRoleCompact(role);
            badgeRow.appendChild(roleBadge);
          });
          hasBadges = true;
        }
        if (hasBadges) {
          titleWrap.appendChild(badgeRow);
        }
        const meta = document.createElement("span");
        const resultCount = Number(item.result_count || 0);
        const pageCount = Number(item.page_count || 0);
        meta.textContent = `${formatWhen(item.created_at)} · 결과 ${resultCount}개${pageCount > 0 ? ` · 원문 ${pageCount}건` : ""}`;
        titleWrap.appendChild(meta);
        header.appendChild(titleWrap);
        card.appendChild(header);

        if (item.summary_head) {
          const summary = document.createElement("div");
          summary.className = "history-item-summary";
          summary.textContent = item.summary_head;
          card.appendChild(summary);
        }

        const detailLines = [];
        if (!isInvestigation) {
          detailLines.push(formatAnswerModeLabel(item.answer_mode));
        }
        const claimCoverageSummary = formatClaimCoverageCountSummary(item.claim_coverage_summary);
        if (claimCoverageSummary) {
          detailLines.push(`사실 검증 ${claimCoverageSummary}`);
        }
        if (detailLines.length > 0) {
          const detailMeta = document.createElement("div");
          detailMeta.className = "meta";
          detailMeta.textContent = detailLines.join(" · ");
          card.appendChild(detailMeta);
        }

        const pagePreviews = Array.isArray(item.pages_preview)
          ? item.pages_preview.filter((page) => page && typeof page === "object")
          : [];
        if (pagePreviews.length > 0) {
          const detailWrap = document.createElement("div");
          detailWrap.className = "history-item-detail";

          const toggleButton = document.createElement("button");
          toggleButton.type = "button";
          toggleButton.className = "secondary";
          toggleButton.textContent = `원문 미리보기 ${pagePreviews.length}건 펼치기`;
          detailWrap.appendChild(toggleButton);

          const hint = document.createElement("div");
          hint.className = "hint";
          hint.textContent = "검색 결과 링크에서 실제로 저장한 원문 발췌와 짧은 본문 미리보기입니다.";
          detailWrap.appendChild(hint);

          const pagesBody = document.createElement("div");
          pagesBody.className = "history-pages hidden";

          pagePreviews.forEach((page, index) => {
            const pageCard = document.createElement("article");
            pageCard.className = "history-page-preview";

            const pageTitle = document.createElement("strong");
            pageTitle.textContent = `${index + 1}. ${page.title || "원문 페이지"}`;
            pageCard.appendChild(pageTitle);

            const pageMeta = document.createElement("div");
            pageMeta.className = "history-page-meta";
            const metaLines = [];
            if (page.url) metaLines.push(`링크: ${page.url}`);
            if (page.char_count) metaLines.push(`저장 길이: ${page.char_count}자`);
            pageMeta.textContent = metaLines.join(" · ");
            pageCard.appendChild(pageMeta);

            if (page.excerpt) {
              const excerpt = document.createElement("p");
              excerpt.textContent = `발췌: ${page.excerpt}`;
              pageCard.appendChild(excerpt);
            }

            if (page.text_preview) {
              const textPreview = document.createElement("p");
              textPreview.textContent = `본문 미리보기: ${page.text_preview}`;
              pageCard.appendChild(textPreview);
            }

            pagesBody.appendChild(pageCard);
          });

          toggleButton.addEventListener("click", () => {
            const hidden = pagesBody.classList.toggle("hidden");
            toggleButton.textContent = hidden
              ? `원문 미리보기 ${pagePreviews.length}건 펼치기`
              : `원문 미리보기 ${pagePreviews.length}건 접기`;
          });

          detailWrap.appendChild(pagesBody);
          card.appendChild(detailWrap);
        }

        const actions = document.createElement("div");
        actions.className = "history-item-actions";

        const loadButton = document.createElement("button");
        loadButton.type = "button";
        loadButton.className = "secondary";
        loadButton.textContent = "다시 불러오기";
        loadButton.disabled = state.isBusy;
        loadButton.addEventListener("click", () => {
          loadWebSearchRecord(item.record_id).catch(renderError);
        });
        actions.appendChild(loadButton);

        const copyButton = document.createElement("button");
        copyButton.type = "button";
        copyButton.className = "copy-button subtle";
        copyButton.textContent = "검색 기록 경로 복사";
        copyButton.disabled = !item.record_path;
        copyButton.addEventListener("click", () => {
          copyTextValue(item.record_path || "", "검색 기록 경로를 복사했습니다.").catch(renderError);
        });
        actions.appendChild(copyButton);

        card.appendChild(actions);
        searchHistoryList.appendChild(card);
      });
    }

    async function loadWebSearchRecord(recordId) {
      if (!recordId || state.isBusy) return;
      await sendRequest({
        user_text: "",
        load_web_search_record_id: recordId,
      }, "history");
    }

    function renderApproval(approval) {
      state.currentApproval = approval || null;
      showElement(approvalBox, Boolean(approval));
      approvalMeta.innerHTML = "";
      approvalPathInput.value = "";
      approvalPreview.textContent = "";
      approveButton.disabled = true;
      reissueButton.disabled = true;
      rejectButton.disabled = !approval;
      approvalCopyPathButton.disabled = !approval;

      if (!approval) {
        updateContentVerdictState();
        updateCorrectionHelperText();
        return;
      }

      const lines = [
        `작업: ${approval.kind}`,
        `approval_id: ${approval.approval_id}`,
        `요청 경로: ${approval.requested_path}`,
        `덮어쓰기 필요: ${approval.overwrite ? "예" : "아니오"}`,
        `생성 시각: ${formatWhen(approval.created_at)}`
      ];
      const approvalSourceMessage = resolveApprovalSourceMessage(approval);
      const hasRecordedCorrection = Boolean(normalizeMultilineText(approvalSourceMessage?.corrected_text || ""));
      if (Array.isArray(approval.source_paths) && approval.source_paths.length > 0) {
        lines.push(`출처: ${approval.source_paths.join(", ")}`);
      }
      if (usesCorrectedSaveSnapshot(approval)) {
        lines.push("저장 기준: 기록된 수정본 스냅샷");
        lines.push("이 미리보기는 저장 요청 시점에 고정되며, 나중에 수정본을 다시 기록해도 자동으로 바뀌지 않습니다.");
        lines.push("더 새 수정본을 저장하려면 응답 카드에서 새 저장 요청을 다시 만들어야 합니다.");
      } else if (hasRecordedCorrection) {
        lines.push("저장 기준: 원래 grounded brief 초안");
        lines.push("기록된 수정본은 이 승인 카드에 자동으로 반영되지 않습니다. 수정본 저장은 응답 카드의 별도 저장 요청으로만 진행됩니다.");
      }
      if (approval.overwrite) {
        lines.push("⚠ 이 경로에 기존 파일이 있습니다. 승인하면 기존 파일을 덮어씁니다.");
      }

      approvalMeta.innerHTML = lines.map((line) => `<span>${line}</span>`).join("");
      approvalPathInput.value = approval.requested_path || "";
      approvalPreview.textContent = approval.preview_markdown || "";
      approveButton.disabled = state.isBusy;
      reissueButton.disabled = state.isBusy || !approvalPathInput.value.trim();
      approvalCopyPathButton.disabled = !approval.requested_path;
      updateContentVerdictState();
      updateCorrectionHelperText();
    }

    function renderSession(session) {
      const incomingId = session.session_id || "";
      const incomingUpdatedAt = session.updated_at || "";
      if (
        incomingId === state.currentSessionId
        && incomingUpdatedAt
        && state._lastRenderedSessionUpdatedAt
        && incomingUpdatedAt < state._lastRenderedSessionUpdatedAt
      ) {
        return;
      }
      state._lastRenderedSessionUpdatedAt = incomingUpdatedAt;
      state.currentSessionId = session.session_id;
      state.currentSessionMessages = Array.isArray(session.messages) ? session.messages : [];
      sessionIdInput.value = state.currentSessionId;
      setText("meta-session", state.currentSessionId);
      const sessionWebSearchPermission = normalizeWebSearchPermission(session.permissions?.web_search || state.defaultWebSearchPermission);
      webSearchPermissionInput.value = sessionWebSearchPermission;
      updateWebSearchMeta(sessionWebSearchPermission);
      currentSessionTitleEl.textContent = session.title || session.session_id;
      currentSessionMetaEl.textContent = `메시지 ${session.messages?.length || 0}개 · 승인 대기 ${session.pending_approvals?.length || 0}건 · 웹 검색 ${formatWebSearchPermissionLabel(sessionWebSearchPermission)} · 마지막 업데이트 ${formatWhen(session.updated_at)}`;
      renderReviewQueue(session.review_queue_items || []);
      renderAggregateTriggerSection(session.recurrence_aggregate_candidates || []);
      renderTranscript(session.messages || []);
      const latestAssistantContext = findLatestAssistantContext(session.messages || []);
      const latestAssistantMessage = latestAssistantContext.assistant;
      const correctionTargetMessage = resolveCorrectionTargetMessage(session.messages || [], latestAssistantMessage);
      showElement(responseBox, Boolean(latestAssistantMessage));
      if (latestAssistantMessage) {
        responseText.textContent = latestAssistantMessage.text || "응답 본문이 없습니다.";
        showElement(responseCopyTextButton, Boolean(latestAssistantMessage.text));
        renderResponseOrigin(latestAssistantMessage.response_origin || null);
        renderResponseSummary(latestAssistantMessage, null);
        renderResponseFeedback(latestAssistantMessage, latestAssistantContext.userText);
        renderContentVerdictControl(correctionTargetMessage);
        renderCorrectionEditor(correctionTargetMessage);
        renderCandidateConfirmationControl(correctionTargetMessage);
        renderEvidence(latestAssistantMessage.evidence || []);
        renderSummaryChunks(latestAssistantMessage.summary_chunks || []);
        renderClaimCoverage(
          latestAssistantMessage.claim_coverage || [],
          latestAssistantMessage.claim_coverage_progress_summary || latestAssistantMessage.active_context?.claim_coverage_progress_summary || ""
        );
        renderFactStrengthBar(latestAssistantMessage.claim_coverage || []);
      } else {
        responseText.textContent = "아직 보낸 요청이 없습니다.";
        showElement(responseCopyTextButton, false);
        renderResponseOrigin(null);
        renderResponseSummary(null, null);
        renderResponseFeedback(null);
        renderContentVerdictControl(null);
        renderCorrectionEditor(null);
        renderCandidateConfirmationControl(null);
        renderEvidence([]);
        renderSummaryChunks([]);
        renderClaimCoverage([], "");
        renderFactStrengthBar([]);
      }
      renderContext(session.active_context || null);
      const sessionSuggestions = latestAssistantMessage?.follow_up_suggestions || session.active_context?.suggested_prompts || [];
      renderSuggestions(sessionSuggestions);
      renderSearchHistory(session.web_search_history || []);
    }

    function renderResult(data) {
      clearError();
      if (data.session) {
        renderSession(data.session);
      }
      showElement(responseBox, true);
      responseText.textContent = data.response?.text || "응답 본문이 없습니다.";
      showElement(responseCopyTextButton, Boolean(data.response?.text));
      renderResponseOrigin(data.response?.response_origin || null);
      renderResponseSummary(data.response || null, data.runtime_status || null);
      const latestAssistantContext = findLatestAssistantContext(data.session?.messages || []);
      const correctionTargetMessage = resolveCorrectionTargetMessage(data.session?.messages || [], latestAssistantContext.assistant);
      renderResponseFeedback(latestAssistantContext.assistant, latestAssistantContext.userText);
      renderContentVerdictControl(correctionTargetMessage);
      renderCorrectionEditor(correctionTargetMessage);
      renderCandidateConfirmationControl(correctionTargetMessage);
      renderSelected(data.response?.selected_source_paths || []);
      renderEvidence(data.response?.evidence || []);
      renderSummaryChunks(data.response?.summary_chunks || []);
      renderClaimCoverage(
        data.response?.claim_coverage || [],
        data.response?.claim_coverage_progress_summary || data.response?.active_context?.claim_coverage_progress_summary || ""
      );
      renderFactStrengthBar(data.response?.claim_coverage || []);
      renderPreview(data.response?.note_preview || "");
      renderContext(data.response?.active_context || data.session?.active_context || null);
      renderSuggestions(data.response?.follow_up_suggestions || data.session?.active_context?.suggested_prompts || []);
      renderSearchHistory(data.session?.web_search_history || []);
      renderRuntime(data.runtime_status || null);
      if (data.session) {
        const pending = data.session.pending_approvals || [];
        renderApproval(data.response?.approval || pending[pending.length - 1] || null);
        renderContentVerdictControl(correctionTargetMessage);
        renderCorrectionEditor(correctionTargetMessage);
        renderCandidateConfirmationControl(correctionTargetMessage);
      } else {
        renderApproval(data.response?.approval || null);
        renderContentVerdictControl(null);
        renderCorrectionEditor(null);
        renderCandidateConfirmationControl(null);
      }
    }

    function renderError(error) {
      clearNotice();
      const message = error instanceof Error ? error.message : String(error);
      showElement(errorBox, true);
      errorBox.textContent = message;
    }

    function clearError() {
      showElement(errorBox, false);
      errorBox.textContent = "";
    }

    function renderNotice(message) {
      if (!message) {
        clearNotice();
        return;
      }
      showElement(noticeBox, true);
      noticeBox.textContent = message;
    }

    function clearNotice() {
      showElement(noticeBox, false);
      noticeBox.textContent = "";
    }

    async function fetchConfig() {
      const data = await fetchJson("/api/config");
      document.getElementById("provider").value = data.default_provider;
      document.getElementById("model").value = data.default_model || "";
      document.getElementById("base-url").value = data.default_base_url || "";
      state.defaultWebSearchPermission = normalizeWebSearchPermission(data.default_web_search_permission || APP_CONFIG.DEFAULT_WEB_SEARCH_PERMISSION);
      state.webSearchToolConnected = Boolean(data.web_search_tool_connected);
      webSearchPermissionInput.value = state.defaultWebSearchPermission;
      setText("meta-app-name", data.app_name);
      setText("meta-provider", data.default_provider);
      setText("meta-model", data.default_model_label || "선택형 로컬 모델");
      setText("meta-session", data.default_session_id);
      updateWebSearchMeta(state.defaultWebSearchPermission);
      const notesDir = String(data.notes_dir || "").trim();
      if (notesDir) {
        document.getElementById("note-path").placeholder = `비워두면 ${notesDir} 기본 경로를 사용합니다.`;
      }
    }

    async function fetchSessions() {
      const data = await fetchJson("/api/sessions");
      renderSessionList(data.sessions || []);
    }

    async function loadSession(sessionId) {
      const targetSessionId = sessionId || sessionIdInput.value.trim() || state.currentSessionId;
      const data = await fetchJson(`/api/session?session_id=${encodeURIComponent(targetSessionId)}`);
      renderSession(data.session);
      const pending = data.session?.pending_approvals || [];
      renderApproval(pending[pending.length - 1] || null);
      const latestAssistantContext = findLatestAssistantContext(data.session?.messages || []);
      renderCorrectionEditor(
        resolveCorrectionTargetMessage(data.session?.messages || [], latestAssistantContext.assistant)
      );
      await fetchSessions();
    }

    async function approveCurrentApproval() {
      if (!state.currentApproval || state.isBusy) return;
      try {
        startProgress("approve", "system", "승인 워크플로");
        responseText.textContent = "";
        showElement(responseCopyTextButton, false);
        renderResponseOrigin({ provider: "system", badge: "SYSTEM", label: "시스템 응답", kind: C.ResponseOriginKind.APPROVAL });
        const data = await submitStreamPayload({
          session_id: state.currentSessionId,
          approved_approval_id: state.currentApproval.approval_id
        });
        if (data?.cancelled) {
          renderNotice(data.message || "요청을 취소했습니다.");
          await fetchSessions();
          return;
        }
        renderResult(data);
        await fetchSessions();
      } finally {
        stopProgress();
      }
    }

    async function reissueCurrentApproval() {
      if (!state.currentApproval || state.isBusy) return;
      const requestedPath = approvalPathInput.value.trim();
      if (!requestedPath) {
        renderError(new Error("새 저장 경로를 입력해 주세요."));
        return;
      }

      try {
        startProgress("reissue", "system", "승인 워크플로");
        responseText.textContent = "";
        showElement(responseCopyTextButton, false);
        renderResponseOrigin({ provider: "system", badge: "SYSTEM", label: "시스템 응답", kind: C.ResponseOriginKind.APPROVAL });
        const data = await submitStreamPayload({
          session_id: state.currentSessionId,
          reissue_approval_id: state.currentApproval.approval_id,
          note_path: requestedPath,
        });
        if (data?.cancelled) {
          renderNotice(data.message || "요청을 취소했습니다.");
          await fetchSessions();
          return;
        }
        renderResult(data);
        await fetchSessions();
      } finally {
        stopProgress();
      }
    }

    async function rejectCurrentApproval() {
      if (!state.currentApproval || state.isBusy) return;
      try {
        startProgress("reject", "system", "승인 워크플로");
        responseText.textContent = "";
        showElement(responseCopyTextButton, false);
        renderResponseOrigin({ provider: "system", badge: "SYSTEM", label: "시스템 응답", kind: C.ResponseOriginKind.APPROVAL });
        const data = await submitStreamPayload({
          session_id: state.currentSessionId,
          rejected_approval_id: state.currentApproval.approval_id
        });
        if (data?.cancelled) {
          renderNotice(data.message || "요청을 취소했습니다.");
          await fetchSessions();
          return;
        }
        renderResult(data);
        await fetchSessions();
      } finally {
        stopProgress();
      }
    }

    function createSessionId() {
      return `session-${Date.now().toString(36)}`;
    }

      requestForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (state.isBusy) return;
      try {
        startProgress("request", currentProvider(), currentModel());
        responseText.textContent = "";
        showElement(responseCopyTextButton, false);
        renderResponseOrigin(null);
        const data = await submitStreamPayload(await collectPayload());
        if (data?.cancelled) {
          renderNotice(data.message || "요청을 취소했습니다.");
          await fetchSessions();
          return;
        }
        renderResult(data);
        await fetchSessions();
      } catch (error) {
        renderError(error);
      } finally {
        stopProgress();
      }
    });

    document.querySelectorAll('input[name="request_mode"]').forEach((input) => {
      input.addEventListener("change", () => applyMode(activeMode()));
    });

    pickFileButton.addEventListener("click", () => {
      browserFileInput.click();
    });
    pickFolderButton.addEventListener("click", () => {
      browserFolderInput.click();
    });
    clearPickedFileButton.addEventListener("click", () => {
      clearSelectedBrowserFile();
    });
    clearPickedFolderButton.addEventListener("click", () => {
      clearSelectedSearchFolder();
    });
    browserFileInput.addEventListener("change", () => {
      const file = browserFileInput.files && browserFileInput.files[0] ? browserFileInput.files[0] : null;
      if (file) {
        sourcePathInput.value = "";
      }
      renderSelectedBrowserFile(file);
    });
    browserFolderInput.addEventListener("change", () => {
      const files = browserFolderInput.files ? Array.from(browserFolderInput.files) : [];
      if (files.length > 0) {
        searchRootInput.value = "";
      }
      renderSelectedSearchFolder(files);
    });
    sourcePathInput.addEventListener("input", () => {
      if (sourcePathInput.value.trim() && state.selectedBrowserFile) {
        clearSelectedBrowserFile();
      }
    });
    searchRootInput.addEventListener("input", () => {
      if (searchRootInput.value.trim() && state.selectedSearchFolderFiles.length > 0) {
        clearSelectedSearchFolder();
      }
    });

    document.getElementById("load-session").addEventListener("click", () => loadSession().catch(renderError));
    document.getElementById("refresh-session").addEventListener("click", () => loadSession(state.currentSessionId).catch(renderError));
    document.getElementById("new-session").addEventListener("click", async () => {
      state.currentSessionId = createSessionId();
      sessionIdInput.value = state.currentSessionId;
      setText("meta-session", state.currentSessionId);
      webSearchPermissionInput.value = state.defaultWebSearchPermission;
      updateWebSearchMeta(state.defaultWebSearchPermission);
      renderSession({
        session_id: state.currentSessionId,
        title: state.currentSessionId,
        updated_at: new Date().toISOString(),
        messages: [],
        pending_approvals: [],
        web_search_history: [],
        permissions: {
          web_search: state.defaultWebSearchPermission,
          web_search_label: formatWebSearchPermissionLabel(state.defaultWebSearchPermission),
        }
      });
      renderApproval(null);
      await fetchSessions();
    });
    webSearchPermissionInput.addEventListener("change", () => {
      updateWebSearchMeta(webSearchPermissionInput.value);
    });
    approveButton.addEventListener("click", () => approveCurrentApproval().catch(renderError));
    reissueButton.addEventListener("click", () => reissueCurrentApproval().catch(renderError));
    rejectButton.addEventListener("click", () => rejectCurrentApproval().catch(renderError));
    cancelRequestButton.addEventListener("click", () => cancelCurrentRequest().catch(renderError));
    approvalPathInput.addEventListener("input", () => {
      reissueButton.disabled = state.isBusy || !state.currentApproval || !approvalPathInput.value.trim();
    });
    approvalCopyPathButton.addEventListener("click", () => {
      copyTextValue(approvalPathInput.value || state.currentApproval?.requested_path || "", "승인 경로를 복사했습니다.").catch(renderError);
    });
    responseCopyPathButton.addEventListener("click", () => {
      copyTextValue(responseCopyPathButton.dataset.path || "", "저장 경로를 복사했습니다.").catch(renderError);
    });
    responseCopyTextButton.addEventListener("click", () => {
      copyTextValue(responseText.textContent || "", "본문을 복사했습니다.").catch(renderError);
    });
    responseCopySearchRecordButton.addEventListener("click", () => {
      copyTextValue(responseCopySearchRecordButton.dataset.path || "", "검색 기록 경로를 복사했습니다.").catch(renderError);
    });
    responseFeedbackButtons.forEach((button) => {
      button.addEventListener("click", () => {
        if (!state.latestAssistantMessageId) return;
        submitFeedback(
          state.latestAssistantMessageId,
          button.dataset.feedbackValue || "",
          ["unclear", "incorrect"].includes(button.dataset.feedbackValue || "")
            ? (
              state.latestAssistantFeedbackLabel === (button.dataset.feedbackValue || "")
                ? state.latestAssistantFeedbackReason
                : ""
            )
            : ""
        ).catch(renderError);
      });
    });
    responseFeedbackReasonButtons.forEach((button) => {
      button.addEventListener("click", () => {
        if (!state.latestAssistantMessageId || !state.latestAssistantFeedbackLabel) return;
        submitFeedback(
          state.latestAssistantMessageId,
          state.latestAssistantFeedbackLabel,
          button.dataset.feedbackReason || ""
        ).catch(renderError);
      });
    });
    responseFeedbackRetryButton.addEventListener("click", () => {
      retryLatestAssistantWithFeedback().catch(renderError);
    });
    responseContentRejectButton.addEventListener("click", () => {
      submitContentVerdict().catch(renderError);
    });
    responseContentReasonInput.addEventListener("input", () => {
      updateContentReasonNoteState();
    });
    responseContentReasonSubmitButton.addEventListener("click", () => {
      submitContentReasonNote().catch(renderError);
    });
    responseCorrectionInput.addEventListener("input", () => {
      updateCorrectionFormState();
    });
    responseCorrectionSubmitButton.addEventListener("click", () => {
      submitCorrection().catch(renderError);
    });
    responseCorrectionSaveRequestButton.addEventListener("click", () => {
      submitCorrectedSaveRequest().catch(renderError);
    });
    responseCandidateConfirmationSubmitButton.addEventListener("click", () => {
      submitCandidateConfirmation().catch(renderError);
    });
    evidenceToggleButton.addEventListener("click", () => {
      togglePanelBody(evidenceBody, evidenceToggleButton, `근거 ${evidenceText.textContent ? evidenceText.textContent.split("\n").filter((line) => /^\d+\./.test(line)).length : 0}개 펼치기`, "접기");
    });
    summaryChunksToggleButton.addEventListener("click", () => {
      togglePanelBody(summaryChunksBody, summaryChunksToggleButton, `구간 ${summaryChunksText.textContent ? summaryChunksText.textContent.split("\n").filter((line) => /^\d+\./.test(line)).length : 0}개 펼치기`, "접기");
    });
    claimCoverageToggleButton.addEventListener("click", () => {
      togglePanelBody(claimCoverageBody, claimCoverageToggleButton, `사실 검증 ${claimCoverageText.textContent ? claimCoverageText.textContent.split("\n").filter((line) => /^\d+\./.test(line)).length : 0}개 펼치기`, "접기");
    });

    // ── Sidebar toggle ──
    const sidebarEl = document.getElementById("sidebar");
    const sidebarToggleBtn = document.getElementById("sidebar-toggle");
    if (sidebarToggleBtn && sidebarEl) {
      sidebarToggleBtn.addEventListener("click", () => {
        const isMobile = window.innerWidth <= 768;
        if (isMobile) {
          sidebarEl.classList.toggle("open");
        } else {
          sidebarEl.classList.toggle("collapsed");
          document.body.classList.toggle("sidebar-collapsed");
        }
      });
    }

    // ── Attach dropdown toggle ──
    const attachToggle = document.getElementById("attach-toggle");
    const attachDropdown = document.getElementById("attach-dropdown");
    if (attachToggle && attachDropdown) {
      attachToggle.addEventListener("click", (e) => {
        e.preventDefault();
        attachDropdown.classList.toggle("hidden");
      });
      document.addEventListener("click", (e) => {
        if (!attachToggle.contains(e.target) && !attachDropdown.contains(e.target)) {
          attachDropdown.classList.add("hidden");
        }
      });
    }

    // Close attach dropdown after picking file/folder
    pickFileButton.addEventListener("click", () => {
      if (attachDropdown) attachDropdown.classList.add("hidden");
    });
    pickFolderButton.addEventListener("click", () => {
      if (attachDropdown) attachDropdown.classList.add("hidden");
    });

    // ── Auto-resize textarea ──
    const userTextEl = document.getElementById("user-text");
    if (userTextEl) {
      userTextEl.addEventListener("input", () => {
        userTextEl.style.height = "auto";
        userTextEl.style.height = Math.min(userTextEl.scrollHeight, 150) + "px";
      });
      // ── Enter to submit, Shift+Enter for newline ──
      userTextEl.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey && !e.ctrlKey && !e.metaKey) {
          e.preventDefault();
          if (!state.isBusy) {
            requestForm.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
          }
        }
      });
    }

    // ── Scroll chat to bottom helper ──
    const chatMessagesEl = document.getElementById("chat-messages");
    function scrollChatToBottom() {
      if (chatMessagesEl) {
        requestAnimationFrame(() => {
          chatMessagesEl.scrollTop = chatMessagesEl.scrollHeight;
        });
      }
    }

    // Patch renderTranscript to scroll after render
    const _originalRenderTranscript = renderTranscript;
    renderTranscript = function(messages) {
      _originalRenderTranscript(messages);
      scrollChatToBottom();
    };

    // Patch stopProgress to scroll after response
    const _originalStopProgress = stopProgress;
    stopProgress = function() {
      _originalStopProgress();
      scrollChatToBottom();
    };

    Promise.resolve()
      .then(fetchConfig)
      .then(fetchSessions)
      .then(() => loadSession(APP_CONFIG.DEFAULT_SESSION_ID))
      .then(() => applyMode("file"))
      .catch(renderError);
