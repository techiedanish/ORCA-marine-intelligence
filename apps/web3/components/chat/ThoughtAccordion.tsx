"use client";

import { useState } from "react";
import { ChevronDown, CheckCircle2, CircleSlash } from "lucide-react";
import clsx from "clsx";
import type { TraceStep } from "@/lib/types";

const AGENT_ICON_HINT: Record<string, string> = {
  "Marine Data Discovery Agent": "INCOIS PFZ sectors, species filters",
  "Ocean Analytics Agent": "SST thermal gradients, Chlorophyll-a upwelling",
  "Weather Intelligence Agent": "IMD bulletins, OpenWeather wind/squall telemetry",
  "Risk Assessment Agent": "0–100 risk score, safety verdict",
  "Geospatial Reasoning Agent": "IMBL treaty line & MPA containment audit",
};

export default function ThoughtAccordion({
  trace,
  engineUsed,
  label,
}: {
  trace: TraceStep[];
  engineUsed?: string;
  label: string;
}) {
  const [open, setOpen] = useState(false);
  const completed = trace.filter((t) => t.status === "COMPLETED").length;

  return (
    <div className="rounded-lg border border-abyss-700 bg-abyss-900/60 overflow-hidden">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between px-3 py-2 text-left"
      >
        <div className="flex items-center gap-2 text-xs text-mist-300">
          <span className="flex h-1.5 w-1.5 rounded-full bg-depth-teal" />
          <span className="font-medium text-mist-300">{label}</span>
          <span className="text-mist-400">
            · {completed}/{trace.length} agents
          </span>
          {engineUsed && (
            <span className="hidden sm:inline text-[10px] font-mono text-mist-400 border border-abyss-700 rounded px-1 py-0.5">
              {engineUsed === "gemini_flash" ? "Gemini Flash" : "deterministic fallback"}
            </span>
          )}
        </div>
        <ChevronDown
          size={14}
          className={clsx("text-mist-400 transition-transform", open && "rotate-180")}
        />
      </button>

      {open && (
        <ul className="border-t border-abyss-700 divide-y divide-abyss-700/70">
          {trace.map((step, i) => (
            <li key={i} className="px-3 py-2.5 flex gap-2.5">
              {step.status === "COMPLETED" ? (
                <CheckCircle2 size={15} className="text-depth-teal shrink-0 mt-0.5" />
              ) : (
                <CircleSlash size={15} className="text-mist-400 shrink-0 mt-0.5" />
              )}
              <div className="min-w-0">
                <p className="text-sm text-[#EAF2F5] leading-snug">{step.agent}</p>
                <p className="text-xs text-mist-400 leading-snug mt-0.5">{step.summary}</p>
                <p className="text-[10px] text-mist-400/70 font-mono mt-1">
                  {AGENT_ICON_HINT[step.agent]} · {step.duration_ms}ms
                </p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
