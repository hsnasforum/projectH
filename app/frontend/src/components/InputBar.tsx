import { useState, useRef, useCallback, type KeyboardEvent, type FormEvent, type DragEvent } from "react";

interface Props {
  onSend: (text: string, opts?: Record<string, unknown>) => void;
  isStreaming: boolean;
  onCancel: () => void;
}

const SLASH_COMMANDS = [
  { command: "/검색", description: "웹에서 검색합니다", prefix: "웹검색: " },
  { command: "/요약", description: "문서를 요약합니다", prefix: "" },
  { command: "/메모", description: "메모 형식으로 정리합니다", prefix: "" },
];

export default function InputBar({ onSend, isStreaming, onCancel }: Props) {
  const [text, setText] = useState("");
  const [attachedFile, setAttachedFile] = useState<File | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [showSlashMenu, setShowSlashMenu] = useState(false);
  const [slashFilter, setSlashFilter] = useState("");
  const [slashSelectedIndex, setSlashSelectedIndex] = useState(0);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const autoResize = useCallback(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 160) + "px";
  }, []);

  const handleFile = useCallback((file: File) => {
    setAttachedFile(file);
  }, []);

  const handleSubmit = useCallback(
    async (e?: FormEvent) => {
      e?.preventDefault();
      const trimmed = text.trim();
      if (!trimmed && !attachedFile) return;
      if (isStreaming) return;

      const opts: Record<string, unknown> = {};

      if (attachedFile) {
        // Read file content as base64 for upload
        const reader = new FileReader();
        const content = await new Promise<string>((resolve) => {
          reader.onload = () => {
            const result = reader.result as string;
            // Extract base64 part after data:...;base64,
            const base64 = result.split(",")[1] || "";
            resolve(base64);
          };
          reader.readAsDataURL(attachedFile);
        });

        opts.uploaded_file = {
          name: attachedFile.name,
          content_base64: content,
          size_bytes: attachedFile.size,
          mime_type: attachedFile.type || "text/plain",
        };
      }

      onSend(trimmed || "이 파일을 요약해 주세요.", opts);
      setText("");
      setAttachedFile(null);
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    },
    [text, attachedFile, isStreaming, onSend],
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

  // Drag and drop handlers
  const handleDragOver = useCallback((e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFile(files[0]);
    }
  }, [handleFile]);

  const handleFileInputChange = useCallback(() => {
    const file = fileInputRef.current?.files?.[0];
    if (file) {
      handleFile(file);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }, [handleFile]);

  return (
    <div
      className={`
        shrink-0 border-t bg-warm-50 transition-colors
        ${isDragOver ? "border-accent bg-accent/5" : "border-stone-100"}
      `}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {/* Drag overlay */}
      {isDragOver && (
        <div className="text-center py-3 text-[13px] text-accent font-medium">
          여기에 파일을 놓으세요
        </div>
      )}

      <form
        onSubmit={handleSubmit}
        className="max-w-[800px] mx-auto px-4 py-3 md:px-6"
      >
        {/* Attached file indicator */}
        {attachedFile && (
          <div className="flex items-center gap-2 mb-2 px-1 py-1.5 bg-beige-50 rounded-lg">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-accent shrink-0">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <path d="M14 2v6h6" />
            </svg>
            <span className="text-[13px] text-ink truncate flex-1">{attachedFile.name}</span>
            <span className="text-[11px] text-muted/50">{(attachedFile.size / 1024).toFixed(1)}KB</span>
            <button
              type="button"
              onClick={() => setAttachedFile(null)}
              className="text-muted/40 hover:text-red-400 transition-colors p-0.5"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 6L6 18M6 6l12 12" />
              </svg>
            </button>
          </div>
        )}

        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept=".txt,.md,.pdf,.json,.csv,.log,.yaml,.yml,.toml,.ini,.py,.ts,.tsx,.js,.jsx,.html,.xml"
          onChange={handleFileInputChange}
        />

        {/* Main input row */}
        <div className="
          relative flex items-end gap-2
          bg-white rounded-[20px]
          border border-stone-200/80
          shadow-sm
          px-4 py-2
          focus-within:border-stone-300 focus-within:shadow-md
          transition-all duration-150
        ">
          {/* Attach button — opens file explorer */}
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="
              p-1.5 rounded-lg text-muted/50 hover:text-muted
              hover:bg-stone-50 transition-colors shrink-0 mb-0.5
            "
            title="파일 첨부 (클릭) 또는 드래그 앤 드롭"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
            </svg>
          </button>

          {/* Slash command dropdown */}
          {showSlashMenu && (
            <div className="absolute bottom-full left-0 right-0 mb-1 mx-4 md:mx-6 z-50">
              <div className="max-w-[800px] mx-auto">
                <div className="bg-white border border-stone-200 rounded-xl shadow-lg overflow-hidden">
                  {SLASH_COMMANDS
                    .filter((c) => c.command.includes(slashFilter) || !slashFilter)
                    .map((cmd, i) => (
                      <button
                        key={cmd.command}
                        type="button"
                        className={`
                          w-full text-left px-4 py-2.5 flex items-center gap-3 transition-colors
                          ${i === slashSelectedIndex ? "bg-stone-50" : "hover:bg-stone-50"}
                        `}
                        onMouseDown={(e) => {
                          e.preventDefault();
                          const rest = text.replace(/^\/\S*/, "").trim();
                          const newText = cmd.prefix ? `${cmd.prefix}${rest}` : rest;
                          setText(newText);
                          setShowSlashMenu(false);
                          textareaRef.current?.focus();
                        }}
                      >
                        <span className="text-[14px] font-semibold text-accent">{cmd.command}</span>
                        <span className="text-[13px] text-muted">{cmd.description}</span>
                      </button>
                    ))}
                </div>
              </div>
            </div>
          )}

          {/* Textarea */}
          <textarea
            ref={textareaRef}
            value={text}
            onChange={(e) => {
              const val = e.target.value;
              setText(val);
              autoResize();
              // Slash command detection
              if (val.startsWith("/")) {
                const match = val.match(/^\/(\S*)$/);
                if (match) {
                  setSlashFilter("/" + match[1]);
                  setShowSlashMenu(true);
                  setSlashSelectedIndex(0);
                  return;
                }
              }
              setShowSlashMenu(false);
            }}
            onKeyDown={(e) => {
              if (showSlashMenu) {
                const filtered = SLASH_COMMANDS.filter((c) => c.command.includes(slashFilter) || !slashFilter);
                if (e.key === "ArrowDown") {
                  e.preventDefault();
                  setSlashSelectedIndex((i) => Math.min(i + 1, filtered.length - 1));
                  return;
                }
                if (e.key === "ArrowUp") {
                  e.preventDefault();
                  setSlashSelectedIndex((i) => Math.max(i - 1, 0));
                  return;
                }
                if (e.key === "Tab" || (e.key === "Enter" && !e.shiftKey)) {
                  e.preventDefault();
                  const cmd = filtered[slashSelectedIndex];
                  if (cmd) {
                    const rest = text.replace(/^\/\S*/, "").trim();
                    setText(cmd.prefix ? `${cmd.prefix}${rest}` : rest);
                  }
                  setShowSlashMenu(false);
                  return;
                }
                if (e.key === "Escape") {
                  setShowSlashMenu(false);
                  return;
                }
              }
              handleKeyDown(e);
            }}
            onBlur={() => { setTimeout(() => setShowSlashMenu(false), 150); }}
            placeholder={attachedFile ? "파일에 대해 질문하세요..." : "메시지를 입력하세요... ( / 로 명령어)"}
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
              disabled={!text.trim() && !attachedFile}
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
          /검색으로 웹 검색 &middot; Enter로 전송 &middot; Shift+Enter로 줄바꿈 &middot; 파일 드래그 앤 드롭
        </p>
      </form>
    </div>
  );
}
