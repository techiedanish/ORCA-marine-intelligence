"use client";

import { useEffect, useRef, useState } from "react";
import { Send, Waves, Languages } from "lucide-react";
import clsx from "clsx";
import VoiceInput from "./VoiceInput";
import ThoughtAccordion from "./ThoughtAccordion";
import { SafetyVerdictBanner, CitationChips } from "./ResponseCards";
import { askOrca } from "@/lib/api";
import { t, SUPPORTED_LANGUAGES, type LangCode } from "@/lib/i18n";
import { useLocation } from "@/components/providers/LocationProvider";
import type { ChatMessage, ChatResponse } from "@/lib/types";

const SUGGESTIONS = [
  "Nearest Tuna PFZ from my location",
  "Is it safe to go out to sea tomorrow?",
  "Am I close to the International Maritime Boundary Line?",
  "Why has fish productivity aggregated at the current thermal front?",
];

const COORD_SOURCE_LABEL: Record<string, string> = {
  explicit_coordinates: "coordinates you typed",
  known_location: "place name you mentioned",
  user_grounded_location: "your real location",
  default: "default (Kochi) — no location available",
};

interface Props {
  onNewResponse: (response: ChatResponse) => void;
}

export default function ChatInterface({ onNewResponse }: Props) {
  const { location } = useLocation();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [lang, setLang] = useState<LangCode>("en");
  const [langMenuOpen, setLangMenuOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const submit = async (text: string) => {
    const query = text.trim();
    if (!query || busy) return;

    const userMsg: ChatMessage = { id: crypto.randomUUID(), role: "user", text: query };
    const pendingId = crypto.randomUUID();
    setMessages((prev) => [...prev, userMsg, { id: pendingId, role: "assistant", text: "", pending: true }]);
    setInput("");
    setBusy(true);

    try {
      const response = await askOrca(query, "web3-default", location.lat, location.lon);
      setMessages((prev) =>
        prev.map((m) => (m.id === pendingId ? { ...m, pending: false, text: response.answer_text, response } : m))
      );
      if (response.detected_language) setLang(response.detected_language as LangCode);
      onNewResponse(response);
    } catch (e) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === pendingId
            ? { ...m, pending: false, text: "ORCA could not reach the backend. Please check the API server." }
            : m
        )
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="shrink-0 flex items-center justify-between px-4 py-3 border-b border-abyss-700">
        <div className="flex items-center gap-2">
          <Waves size={16} className="text-depth-teal" />
          <span className="font-display text-sm text-mist-300">{t(lang, "copilot")}</span>
        </div>
        <div className="relative">
          <button
            onClick={() => setLangMenuOpen((v) => !v)}
            className="flex items-center gap-1 text-xs text-mist-400 hover:text-white px-2 py-1 rounded border border-abyss-700"
          >
            <Languages size={13} />
            {SUPPORTED_LANGUAGES.find((l) => l.code === lang)?.label}
          </button>
          {langMenuOpen && (
            <div className="absolute right-0 mt-1 bg-abyss-900 border border-abyss-700 rounded-md shadow-panel z-10 w-32 py-1">
              {SUPPORTED_LANGUAGES.map((l) => (
                <button
                  key={l.code}
                  onClick={() => {
                    setLang(l.code);
                    setLangMenuOpen(false);
                  }}
                  className={clsx(
                    "w-full text-left px-3 py-1.5 text-xs hover:bg-abyss-700",
                    lang === l.code ? "text-depth-teal" : "text-mist-300"
                  )}
                >
                  {l.label}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      <div ref={scrollRef} className="flex-1 min-h-0 overflow-y-auto px-4 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="chart-wash rounded-xl border border-abyss-700 p-4 space-y-2.5">
            <p className="text-sm text-mist-300">
              Ask about Potential Fishing Zones, sea safety, thermal fronts, or your vessel's
              position relative to the India–Sri Lanka boundary.
            </p>
            <div className="flex flex-col gap-1.5">
              {SUGGESTIONS.map((s, i) => (
                <button
                  key={i}
                  onClick={() => submit(s)}
                  className="text-left text-xs text-depth-teal border border-depth-teal/30 rounded-md px-2.5 py-2 hover:bg-depth-teal/10 transition-colors"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m) => (
          <div key={m.id} className={clsx("flex", m.role === "user" ? "justify-end" : "justify-start")}>
            <div
              className={clsx(
                "max-w-[92%] rounded-xl px-3.5 py-2.5",
                m.role === "user"
                  ? "bg-abyss-700 text-white"
                  : "bg-abyss-900 border border-abyss-700 text-[#EAF2F5] w-full"
              )}
            >
              {m.pending ? (
                <div className="flex items-center gap-2 text-xs text-mist-400 py-1">
                  <span className="flex gap-0.5">
                    <span className="h-1.5 w-1.5 rounded-full bg-depth-teal animate-bounce [animation-delay:-0.3s]" />
                    <span className="h-1.5 w-1.5 rounded-full bg-depth-teal animate-bounce [animation-delay:-0.15s]" />
                    <span className="h-1.5 w-1.5 rounded-full bg-depth-teal animate-bounce" />
                  </span>
                  {t(lang, "thinking")}
                </div>
              ) : (
                <div className="space-y-2.5">
                  {m.role === "assistant" && m.response && (
                    <ThoughtAccordion
                      trace={m.response.trace}
                      engineUsed={m.response.engine_used}
                      label={t(lang, "thought_trace")}
                    />
                  )}
                  <p className="text-sm leading-relaxed whitespace-pre-wrap">{m.text}</p>
                  {m.role === "assistant" && m.response?.coordinate_source && (
                    <p className="text-[10px] font-mono text-mist-400/80">
                      📍 grounded via: {COORD_SOURCE_LABEL[m.response.coordinate_source] || m.response.coordinate_source}
                    </p>
                  )}
                  {m.role === "assistant" && m.response?.safety_verdict && (
                    <SafetyVerdictBanner verdict={m.response.safety_verdict} />
                  )}
                  {m.role === "assistant" && m.response?.citations && (
                    <CitationChips citations={m.response.citations} />
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          submit(input);
        }}
        className="shrink-0 border-t border-abyss-700 p-3 flex items-center gap-2"
      >
        <VoiceInput lang={lang} onResult={(text) => submit(text)} disabled={busy} />
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={t(lang, "placeholder")}
          disabled={busy}
          className="flex-1 bg-abyss-900 border border-abyss-700 rounded-full px-4 py-2 text-sm text-white placeholder:text-mist-400 focus:outline-none focus:border-depth-teal/60"
        />
        <button
          type="submit"
          disabled={busy || !input.trim()}
          className={clsx(
            "shrink-0 flex items-center justify-center h-9 w-9 rounded-full transition-colors",
            busy || !input.trim()
              ? "bg-abyss-700 text-mist-400 cursor-not-allowed"
              : "bg-depth-teal text-abyss-950 hover:brightness-110"
          )}
          aria-label={t(lang, "send")}
        >
          <Send size={15} />
        </button>
      </form>
    </div>
  );
}
