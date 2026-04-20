    // Shared contracts — generated from core/contracts.py
    const C = Object.freeze({
      ResponseStatus: Object.freeze({ ANSWER: "answer", ERROR: "error", NEEDS_APPROVAL: "needs_approval", SAVED: "saved" }),
      ArtifactKind: Object.freeze({ GROUNDED_BRIEF: "grounded_brief" }),
      SaveContentSource: Object.freeze({ ORIGINAL_DRAFT: "original_draft", CORRECTED_TEXT: "corrected_text" }),
      RecordStage: Object.freeze({
        EMITTED: "emitted_record_only_not_applied",
        APPLIED_PENDING: "applied_pending_result",
        APPLIED_WITH_RESULT: "applied_with_result",
        STOPPED: "stopped",
        REVERSED: "reversed",
        CONFLICT_CHECKED: "conflict_visibility_checked",
      }),
      ResultStage: Object.freeze({
        RESULT_RECORDED_EFFECT_PENDING: "result_recorded_effect_pending",
        EFFECT_ACTIVE: "effect_active",
        EFFECT_STOPPED: "effect_stopped",
        EFFECT_REVERSED: "effect_reversed",
      }),
      AnswerMode: Object.freeze({ GENERAL: "general", ENTITY_CARD: "entity_card", LATEST_UPDATE: "latest_update" }),
      SourceRole: Object.freeze({
        WIKI: "백과 기반", OFFICIAL: "공식 기반", DATABASE: "데이터 기반",
        DESCRIPTIVE: "설명형 출처", NEWS: "보조 기사", AUXILIARY: "보조 출처",
        COMMUNITY: "보조 커뮤니티", PORTAL: "보조 포털", BLOG: "보조 블로그",
      }),
      CoverageStatus: Object.freeze({ STRONG: "strong", CONFLICT: "conflict", WEAK: "weak", MISSING: "missing" }),
      SearchIntentKind: Object.freeze({ NONE: "none", EXPLICIT_WEB: "explicit_web", LIVE_LATEST: "live_latest", EXTERNAL_FACT: "external_fact" }),
      WebSearchPermission: Object.freeze({ DISABLED: "disabled", APPROVAL: "approval", ENABLED: "enabled" }),
      StreamEventType: Object.freeze({
        PHASE: "phase", RUNTIME_STATUS: "runtime_status", RESPONSE_ORIGIN: "response_origin",
        TEXT_DELTA: "text_delta", TEXT_REPLACE: "text_replace", FINAL: "final",
        CANCELLED: "cancelled", ERROR: "error", SEARCH_PREVIEW: "search_preview",
      }),
      ResponseOriginKind: Object.freeze({ APPROVAL: "approval", ASSISTANT: "assistant" }),
      CorrectedOutcome: Object.freeze({ ACCEPTED_AS_IS: "accepted_as_is", CORRECTED: "corrected", REJECTED: "rejected" }),
      ContentVerdict: Object.freeze({ REJECTED: "rejected" }),
      CandidateFamily: Object.freeze({ CORRECTION_REWRITE: "correction_rewrite_preference" }),
    });
