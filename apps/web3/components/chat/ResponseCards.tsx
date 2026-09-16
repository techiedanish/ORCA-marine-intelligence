"use client";

import { AlertTriangle, ShieldCheck, ShieldAlert, ShieldX } from "lucide-react";
import clsx from "clsx";
import type { SafetyVerdict, Citation, ColorCode } from "@/lib/types";

const VERDICT_STYLE: Record<ColorCode, { bg: string; ring: string; icon: any; label: string }> = {
  GREEN: { bg: "bg-verdict-green/15", ring: "ring-verdict-green/40", icon: ShieldCheck, label: "Safe to Sail" },
  AMBER: { bg: "bg-verdict-amber/15", ring: "ring-verdict-amber/40", icon: ShieldAlert, label: "Caution" },
  RED: { bg: "bg-verdict-red/15", ring: "ring-verdict-red/40", icon: ShieldX, label: "Do Not Sail" },
};

const VERDICT_TEXT_COLOR: Record<ColorCode, string> = {
  GREEN: "text-verdict-green",
  AMBER: "text-verdict-amber",
  RED: "text-verdict-red",
};

export function SafetyVerdictBanner({ verdict }: { verdict: SafetyVerdict }) {
  const style = VERDICT_STYLE[verdict.color_code];
  const Icon = style.icon;

  return (
    <div className={clsx("rounded-lg ring-1 p-3", style.bg, style.ring)}>
      <div className="flex items-center gap-2">
        <Icon size={18} className={VERDICT_TEXT_COLOR[verdict.color_code]} />
        <span className={clsx("font-display text-base", VERDICT_TEXT_COLOR[verdict.color_code])}>
          {verdict.color_code} — {style.label}
        </span>
      </div>

      <RiskGauge score={verdict.risk_score} colorCode={verdict.color_code} />

      {verdict.reasons.length > 0 && (
        <ul className="mt-2 space-y-1">
          {verdict.reasons.map((r, i) => (
            <li key={i} className="text-xs text-mist-300 leading-snug">
              {r}
            </li>
          ))}
        </ul>
      )}

      {verdict.alerts.length > 0 && (
        <div className="mt-2 space-y-1">
          {verdict.alerts.map((a, i) => (
            <div key={i} className="flex items-start gap-1.5 text-xs text-verdict-red font-medium">
              <AlertTriangle size={12} className="shrink-0 mt-0.5" />
              <span>{a}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function RiskGauge({ score, colorCode }: { score: number; colorCode: ColorCode }) {
  const hex = { GREEN: "#3FBF7F", AMBER: "#E8A93B", RED: "#E24C4C" }[colorCode];
  return (
    <div className="mt-2.5">
      <div className="flex items-center justify-between text-[10px] font-mono text-mist-400 mb-1">
        <span>RISK INDEX</span>
        <span>{score}/100</span>
      </div>
      <div className="h-1.5 w-full rounded-full bg-abyss-700 overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${Math.min(100, Math.max(2, score))}%`, backgroundColor: hex }}
        />
      </div>
    </div>
  );
}

export function CitationChips({ citations }: { citations: Citation[] }) {
  if (!citations || citations.length === 0) return null;

  const uniqueSources = Array.from(new Set(citations.map((c) => c.source)));

  return (
    <div className="flex flex-wrap gap-1.5 mt-2">
      {uniqueSources.map((src, i) => {
        const c = citations.find((cc) => cc.source === src);
        return (
          <span
            key={i}
            title={c?.claim}
            className={clsx(
              "text-[10px] font-mono px-2 py-1 rounded-full border",
              c?.is_live_feed
                ? "border-depth-teal/40 text-depth-teal"
                : "border-abyss-700 text-mist-400"
            )}
          >
            {src} {c?.is_live_feed ? "· live" : "· snapshot"}
          </span>
        );
      })}
    </div>
  );
}
