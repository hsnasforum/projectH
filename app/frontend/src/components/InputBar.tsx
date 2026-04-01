import { useState, useRef, useCallback, type KeyboardEvent, type FormEvent } from "react";

interface Props {
  onSend: (text: string, opts?: Record<string, unknown>) => void;
  isStreaming: boolean;
  onCancel: () => void;
}

export default function InputBar({ onSend, isStreaming, onCancel }: Props) {
  const [text, setText] = useState("");
  const [filePath, setFilePath] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const autoResize = useCallback(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 160) + "px";
  }, []);

  const handleSubmit = useCallback(
    (e?: FormEvent) => {
      e?.preventDefault();
      const trimmed = text.trim();
      if (!trimmed && !filePath.trim()) return;
      if (isStreaming) return;

      const opts: Record<string, unknown> = {};
      if (filePath.trim()) {
        opts.sourcePath = filePath.trim();
      }
      onSend(trimmed || "이 파일을 요약해 주세요.", opts);
      setText("");
      setFilePath("");
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    },
    [text, filePath, isStreaming, onSend],
  );

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSubmit();
      }
    },
    [handleSubmit],
  );

  return (
    <div className="shrink-0 border-t border-stone-100 bg-warm-50">
      <form
        onSubmit={handleSubmit}
        className="max-w-[800px] mx-auto px-4 py-3 md:px-6"
      >
        {/* File path input (subtle) */}
        {filePath && (
          <div className="flex items-center gap-2 mb-2 px-1">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-muted/50">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <path d="M14 2v6h6" />
            </svg>
            <span className="text-[13px] text-muted truncate">{filePath}</span>
            <button
              type="button"
              onClick={() => setFilePath("")}
              className="text-muted/40 hover:text-muted transition-colors"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 6L6 18M6 6l12 12" />
              </svg>
            </button>
          </div>
        )}

        {/* Main input row */}
        <div className="
          flex items-end gap-2
          bg-white rounded-[20px]
          border border-stone-200/80
          shadow-sm
          px-4 py-2
          focus-within:border-stone-300 focus-within:shadow-md
          transition-all duration-150
        ">
          {/* Attach button */}
          <button
            type="button"
            onClick={() => {
              const path = prompt("파일 경로를 입력하세요:");
              if (path) setFilePath(path);
            }}
            className="
              p-1.5 rounded-lg text-muted/50 hover:text-muted
              hover:bg-stone-50 transition-colors shrink-0 mb-0.5
            "
            title="파일 첨부"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
            </svg>
          </button>

          {/* Textarea */}
          <textarea
            ref={textareaRef}
            value={text}
            onChange={(e) => { setText(e.target.value); autoResize(); }}
            onKeyDown={handleKeyDown}
            placeholder="메시지를 입력하세요..."
            rows={1}
            className="
              flex-1 resize-none outline-none
              text-[15px] text-ink leading-relaxed
              placeholder:text-stone-300
              max-h-[160px] py-1
              bg-transparent
            "
          />

          {/* Send / Cancel button */}
          {isStreaming ? (
            <button
              type="button"
              onClick={onCancel}
              className="
                w-9 h-9 rounded-full shrink-0
                bg-stone-800 text-white
                flex items-center justify-center
                hover:bg-stone-700 transition-colors mb-0.5
              "
              title="중지"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                <rect x="6" y="6" width="12" height="12" rx="2" />
              </svg>
            </button>
          ) : (
            <button
              type="submit"
              disabled={!text.trim() && !filePath.trim()}
              className="
                w-9 h-9 rounded-full shrink-0
                flex items-center justify-center
                transition-all duration-150 mb-0.5
                disabled:bg-stone-100 disabled:text-stone-300
                bg-stone-800 text-white hover:bg-stone-700
              "
              title="전송"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
              </svg>
            </button>
          )}
        </div>

        {/* Subtle hint */}
        <p className="text-center text-[11px] text-muted/30 mt-2">
          로컬에서 실행 &middot; Enter로 전송 &middot; Shift+Enter로 줄바꿈
        </p>
      </form>
    </div>
  );
}
