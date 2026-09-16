import type { Metadata } from "next";
import "./globals.css";
import TopNav from "@/components/nav/TopNav";
import { LocationProvider } from "@/components/providers/LocationProvider";

// NOTE: intentionally NOT using next/font/google here. That loader fetches font
// files from fonts.googleapis.com at BUILD time, which silently breaks `npm run
// build` on any offline or firewalled machine (exactly the kind of judge/demo
// environment this single-command launcher needs to be bulletproof on). The
// font stacks below are 100% local, zero-network, and preserve the same
// serif-display / clean-sans-body / mono-data character defined in globals.css.

export const metadata: Metadata = {
  title: "ORCA — Marine EcOsystem Reasoning with Collaborative Agents",
  description:
    "SIH 2026 (PS 26176): A multi-agent marine safety and fisheries copilot fusing IMD, INCOIS, ISRO Oceansat-3, and Open-Meteo intelligence for Indian coastal fishermen.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="font-body bg-abyss-950 text-[#EAF2F5] antialiased h-screen flex flex-col overflow-hidden">
        <LocationProvider>
          <TopNav />
          <main className="flex-1 min-h-0">{children}</main>
        </LocationProvider>
      </body>
    </html>
  );
}
