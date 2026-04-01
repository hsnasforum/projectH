import { useState, useRef, useCallback, type KeyboardEvent, type FormEvent, type DragEvent } from "react";

interface Props {
  onSend: (text: string, opts?: Record<string, unknown>) => void;
  isStreaming: boolean;
  onCancel: () => void;
}

export default function InputBar({ onSend, isStreaming, onCancel }: Props) {
  const [text, setText] = useState("");
  const [attachedFile, setAttachedFile] = useState<File | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
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
          flex items-end gap-2
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

          {/* Textarea */}
          <textarea
            ref={textareaRef}
            value={text}
            onChange={(e) => { setText(e.target.value); autoResize(); }}
            onKeyDown={handleKeyDown}
            placeholder={attachedFile ? "파일에 대해 질문하세요..." : "메시지를 입력하세요..."}
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
          로컬에서 실행 &middot; Enter로 전송 &middot; Shift+Enter로 줄바꿈 &middot; 파일 드래그 앤 드롭 가능
        </p>
      </form>
    </div>
  );
}
