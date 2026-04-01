export default function TypingIndicator() {
  return (
    <div className="flex gap-3">
      <div className="w-8 h-8 rounded-full bg-beige-100 flex items-center justify-center shrink-0">
        <span className="text-[13px] font-semibold text-accent">H</span>
      </div>
      <div className="flex items-center gap-1 px-4 py-3">
        <span className="w-[6px] h-[6px] rounded-full bg-stone-300 animate-bounce [animation-delay:0ms]" />
        <span className="w-[6px] h-[6px] rounded-full bg-stone-300 animate-bounce [animation-delay:150ms]" />
        <span className="w-[6px] h-[6px] rounded-full bg-stone-300 animate-bounce [animation-delay:300ms]" />
      </div>
    </div>
  );
}
