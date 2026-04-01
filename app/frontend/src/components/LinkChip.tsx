import { useState } from "react";

interface Props {
  url: string;
}

function extractSiteName(url: string): string {
  try {
    const host = new URL(url).hostname.replace(/^www\./, "");
    const map: Record<string, string> = {
      "namu.wiki": "나무위키",
      "ko.wikipedia.org": "위키백과",
      "en.wikipedia.org": "Wikipedia",
      "ja.wikipedia.org": "Wikipedia JP",
      "thewiki.kr": "더위키",
      "naver.com": "네이버",
      "search.naver.com": "네이버",
      "blog.naver.com": "네이버 블로그",
      "news.naver.com": "네이버 뉴스",
      "daum.net": "다음",
      "tistory.com": "티스토리",
      "github.com": "GitHub",
      "youtube.com": "YouTube",
      "reddit.com": "Reddit",
      "stackoverflow.com": "Stack Overflow",
    };
    for (const [domain, name] of Object.entries(map)) {
      if (host === domain || host.endsWith(`.${domain}`)) return name;
    }
    // Use second-level domain as fallback
    const parts = host.split(".");
    return parts.length >= 2 ? parts[parts.length - 2] : host;
  } catch {
    return url.slice(0, 20);
  }
}

function faviconUrl(url: string): string {
  try {
    const origin = new URL(url).origin;
    return `${origin}/favicon.ico`;
  } catch {
    return "";
  }
}

function extractTitle(url: string): string {
  try {
    const u = new URL(url);
    const path = decodeURIComponent(u.pathname).replace(/\//g, " / ").trim();
    return path.length > 2 ? path : u.hostname;
  } catch {
    return url;
  }
}

export default function LinkChip({ url }: Props) {
  const [hovered, setHovered] = useState(false);
  const [faviconError, setFaviconError] = useState(false);
  const siteName = extractSiteName(url);
  const title = extractTitle(url);
  const favicon = faviconUrl(url);

  return (
    <span
      className="relative inline-flex"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        className="
          inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg
          bg-stone-50 border border-stone-200/60
          text-[13px] text-stone-600 font-medium
          hover:bg-stone-100 hover:border-stone-300
          transition-colors no-underline
          max-w-[280px]
        "
      >
        {favicon && !faviconError ? (
          <img
            src={favicon}
            alt=""
            width={14}
            height={14}
            className="rounded-sm shrink-0"
            onError={() => setFaviconError(true)}
          />
        ) : (
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="shrink-0 opacity-50">
            <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
            <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
          </svg>
        )}
        <span className="truncate">{siteName}</span>
      </a>

      {/* Hover preview card */}
      {hovered && (
        <div className="
          absolute bottom-full left-0 mb-2 z-50
          w-[320px] bg-white rounded-xl shadow-lg border border-stone-200
          p-3 pointer-events-none
          animate-in fade-in duration-150
        ">
          <div className="flex items-center gap-2 mb-1.5">
            {favicon && !faviconError ? (
              <img src={favicon} alt="" width={16} height={16} className="rounded-sm" onError={() => setFaviconError(true)} />
            ) : (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="opacity-40">
                <circle cx="12" cy="12" r="10" />
                <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
              </svg>
            )}
            <span className="text-[12px] text-stone-400">{siteName}</span>
          </div>
          <p className="text-[13px] font-medium text-ink leading-snug line-clamp-2">{title}</p>
          <p className="text-[11px] text-stone-400 mt-1 truncate">{url}</p>
        </div>
      )}
    </span>
  );
}
