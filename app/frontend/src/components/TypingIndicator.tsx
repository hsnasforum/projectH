interface Props {
  status?: string;
}

export default function TypingIndicator({ status }: Props) {
  return (
    <div className="flex gap-3">
      <div className="w-8 h-8 rounded-full bg-beige-100 flex items-center justify-center shrink-0">
        <span className="text-[13px] font-semibold text-accent">H</span>
      </div>
      <div className="bg-white border border-stone-100 rounded-2xl rounded-bl-md px-4 py-3 shadow-sm">
        {/* Dots */}
        <div className="flex items-center gap-1 mb-1">
          <span className="w-[5px] h-[5px] rounded-full bg-stone-300 animate-bounce [animation-delay:0ms]" />
          <span className="w-[5px] h-[5px] rounded-full bg-stone-300 animate-bounce [animation-delay:150ms]" />
          <span className="w-[5px] h-[5px] rounded-full bg-stone-300 animate-bounce [animation-delay:300ms]" />
        </div>
        {/* Status text */}
        {status && (
          <p className="text-[11px] text-muted/60 leading-snug">
            {status}
          </p>
        )}
      </div>
    </div>
  );
}
