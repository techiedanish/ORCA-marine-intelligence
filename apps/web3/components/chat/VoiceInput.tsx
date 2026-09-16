"use client";

import { useEffect, useRef, useState } from "react";
import { Mic, MicOff } from "lucide-react";
import clsx from "clsx";
import type { LangCode } from "@/lib/i18n";
import { SUPPORTED_LANGUAGES } from "@/lib/i18n";

interface Props {
  lang: LangCode;
  onResult: (transcript: string) => void;
  disabled?: boolean;
}

/**
 * Microphone toggle wired directly into the prompt bar. Uses the browser's
 * Web Speech API (webkitSpeechRecognition / SpeechRecognition). Silently
 * disables itself when the browser does not support speech recognition
 * (e.g. Firefox) rather than throwing — voice input is an enhancement, not
 * a requirement, for the ORCA copilot.
 */
export default function VoiceInput({ lang, onResult, disabled }: Props) {
  const [listening, setListening] = useState(false);
  const [supported, setSupported] = useState(true);
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setSupported(false);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onresult = (event: any) => {
      const transcript = event.results?.[0]?.[0]?.transcript;
      if (transcript) onResult(transcript);
    };
    recognition.onend = () => setListening(false);
    recognition.onerror = () => setListening(false);

    recognitionRef.current = recognition;
    return () => {
      recognition.onresult = null;
      recognition.onend = null;
      recognition.onerror = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [onResult]);

  useEffect(() => {
    const speechTag = SUPPORTED_LANGUAGES.find((l) => l.code === lang)?.speechTag || "en-IN";
    if (recognitionRef.current) recognitionRef.current.lang = speechTag;
  }, [lang]);

  if (!supported) return null;

  const toggle = () => {
    if (!recognitionRef.current || disabled) return;
    if (listening) {
      recognitionRef.current.stop();
      setListening(false);
    } else {
      try {
        recognitionRef.current.start();
        setListening(true);
      } catch {
        setListening(false);
      }
    }
  };

  return (
    <button
      type="button"
      onClick={toggle}
      disabled={disabled}
      aria-pressed={listening}
      aria-label={listening ? "Stop voice input" : "Start voice input"}
      className={clsx(
        "shrink-0 flex items-center justify-center h-9 w-9 rounded-full transition-colors",
        listening
          ? "bg-verdict-red/20 text-verdict-red animate-pulse"
          : "bg-abyss-700 text-mist-300 hover:text-white hover:bg-abyss-600",
        disabled && "opacity-40 cursor-not-allowed"
      )}
    >
      {listening ? <MicOff size={16} /> : <Mic size={16} />}
    </button>
  );
}
