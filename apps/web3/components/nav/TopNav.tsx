"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Waves, Compass, Thermometer, CloudLightning, ShieldAlert } from "lucide-react";
import clsx from "clsx";
import LocationBadge from "./LocationBadge";

const TABS = [
  { href: "/", label: "Copilot", icon: Waves },
  { href: "/agents/discovery", label: "Marine Discovery", icon: Compass },
  { href: "/agents/analytics", label: "Ocean Analytics", icon: Thermometer },
  { href: "/agents/weather", label: "Weather Intelligence", icon: CloudLightning },
  { href: "/agents/risk", label: "Risk & Geofencing", icon: ShieldAlert },
];

export default function TopNav() {
  const pathname = usePathname();

  return (
    <header className="shrink-0 border-b border-abyss-700 bg-abyss-900/80 backdrop-blur px-4 sm:px-6">
      <div className="flex items-center h-14 gap-6">
        <div className="flex items-center gap-2 shrink-0">
          <span className="font-display text-lg tracking-tight text-depth-teal">ORCA</span>
          <span className="hidden md:inline text-[11px] font-mono text-mist-400 border border-abyss-700 rounded px-1.5 py-0.5">
            PS 26176
          </span>
        </div>

        <nav className="flex items-center gap-1 overflow-x-auto">
          {TABS.map(({ href, label, icon: Icon }) => {
            const active = pathname === href;
            return (
              <Link
                key={href}
                href={href}
                className={clsx(
                  "flex items-center gap-1.5 px-3 py-2 rounded-md text-sm whitespace-nowrap transition-colors",
                  active
                    ? "bg-abyss-700 text-white"
                    : "text-mist-400 hover:text-white hover:bg-abyss-800"
                )}
              >
                <Icon size={15} strokeWidth={2} />
                {label}
              </Link>
            );
          })}
        </nav>

        <div className="ml-auto shrink-0">
          <LocationBadge />
        </div>
      </div>
    </header>
  );
}
