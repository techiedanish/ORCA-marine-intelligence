"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import ChatInterface from "@/components/chat/ChatInterface";
import type { ChatResponse, MapPayload } from "@/lib/types";

const MarineMap = dynamic(() => import("@/components/map/MarineMap"), {
  ssr: false,
  loading: () => (
    <div className="h-full w-full flex items-center justify-center text-mist-400 text-sm">
      Loading chart…
    </div>
  ),
});

export default function CopilotPage() {
  const [mapData, setMapData] = useState<MapPayload | null>(null);

  const handleNewResponse = (response: ChatResponse) => {
    setMapData(response.map);
  };

  return (
    <div className="h-full flex flex-col md:flex-row">
      <section className="md:w-[42%] lg:w-[38%] h-1/2 md:h-full border-b md:border-b-0 md:border-r border-abyss-700 min-h-0">
        <ChatInterface onNewResponse={handleNewResponse} />
      </section>

      <section className="flex-1 h-1/2 md:h-full min-h-0">
        <MarineMap data={mapData} />
      </section>
    </div>
  );
}
