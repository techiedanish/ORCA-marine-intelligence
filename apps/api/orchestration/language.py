"""
========================================================================================
ORCA: Marine EcOsystem Reasoning with Collaborative Agents (SIH 2026 - PS 26176)
Orchestration: Lightweight Multilingual Support
========================================================================================
Detects the query language via Unicode script ranges (fast, dependency-free) and
provides templated phrase translations for the deterministic fallback mode so the
demo can always answer in Hindi, Tamil, Malayalam, Telugu, Bengali, or English even
without a live LLM call.
========================================================================================
"""

import re
from typing import Dict

SCRIPT_RANGES = {
    "hi": (0x0900, 0x097F),  # Devanagari (Hindi/Marathi)
    "bn": (0x0980, 0x09FF),  # Bengali
    "ta": (0x0B80, 0x0BFF),  # Tamil
    "te": (0x0C00, 0x0C7F),  # Telugu
    "ml": (0x0D00, 0x0D7F),  # Malayalam
}

LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "ta": "Tamil",
    "ml": "Malayalam",
    "te": "Telugu",
    "bn": "Bengali",
}


def detect_language(text: str) -> str:
    """Returns an ISO-639-1-ish code: en, hi, ta, ml, te, bn."""
    if not text:
        return "en"
    counts: Dict[str, int] = {k: 0 for k in SCRIPT_RANGES}
    for ch in text:
        cp = ord(ch)
        for lang, (lo, hi) in SCRIPT_RANGES.items():
            if lo <= cp <= hi:
                counts[lang] += 1
                break
    best_lang = max(counts, key=counts.get)
    if counts[best_lang] == 0:
        return "en"
    return best_lang


# Templated verdict phrases keyed by [lang][verdict_key] for deterministic-mode synthesis.
VERDICT_PHRASES = {
    "GREEN_SAFE": {
        "en": "It is safe to venture into the sea. Conditions are favourable.",
        "hi": "समुद्र में जाना सुरक्षित है। मौसम की स्थिति अनुकूल है।",
        "ta": "கடலுக்குச் செல்வது பாதுகாப்பானது. வானிலை நிலைமைகள் சாதகமாக உள்ளன.",
        "ml": "കടലിലേക്ക് പോകുന്നത് സുരക്ഷിതമാണ്. കാലാവസ്ഥ അനുകൂലമാണ്.",
        "te": "సముద్రంలోకి వెళ్లడం సురక్షితం. వాతావరణ పరిస్థితులు అనుకూలంగా ఉన్నాయి.",
        "bn": "সমুদ্রে যাওয়া নিরাপদ। আবহাওয়ার পরিস্থিতি অনুকূল।",
    },
    "AMBER_CAUTION": {
        "en": "Exercise caution. Moderate-to-rough sea conditions are expected.",
        "hi": "सावधानी बरतें। समुद्र में मध्यम से खराब स्थिति की संभावना है।",
        "ta": "எச்சரிக்கையாக இருங்கள். கடல் நிலைமைகள் மிதமான முதல் கடுமையான வரை இருக்கும்.",
        "ml": "ജാഗ്രത പാലിക്കുക. കടലിൽ മിതമായതു മുതൽ പരുക്കൻ സാഹചര്യങ്ങൾ വരെ പ്രതീക്ഷിക്കുന്നു.",
        "te": "జాగ్రత్త వహించండి. మధ్యస్థం నుండి కఠినమైన సముద్ర పరిస్థితులు ఆశించవచ్చు.",
        "bn": "সতর্কতা অবলম্বন করুন। মাঝারি থেকে রুক্ষ সমুদ্রের পরিস্থিতি প্রত্যাশিত।",
    },
    "RED_DANGER": {
        "en": "Do NOT venture into the sea. Hazardous conditions detected.",
        "hi": "समुद्र में न जाएं। खतरनाक स्थिति का पता चला है।",
        "ta": "கடலுக்குள் செல்ல வேண்டாம். ஆபத்தான நிலைமைகள் கண்டறியப்பட்டுள்ளன.",
        "ml": "കടലിലേക്ക് പോകരുത്. അപകടകരമായ സാഹചര്യങ്ങൾ കണ്ടെത്തി.",
        "te": "సముద్రంలోకి వెళ్లవద్దు. ప్రమాదకర పరిస్థితులు గుర్తించబడ్డాయి.",
        "bn": "সমুদ্রে যাবেন না। বিপজ্জনক পরিস্থিতি সনাক্ত করা হয়েছে।",
    },
    "PFZ_FOUND": {
        "en": "Nearest Potential Fishing Zone identified below.",
        "hi": "निकटतम संभावित मछली पकड़ने का क्षेत्र नीचे दिखाया गया है।",
        "ta": "அருகிலுள்ள சாத்தியமான மீன்பிடி மண்டலம் கீழே காட்டப்பட்டுள்ளது.",
        "ml": "ഏറ്റവും അടുത്തുള്ള സാധ്യതയുള്ള മത്സ്യബന്ധന മേഖല ചുവടെ കാണിച്ചിരിക്കുന്നു.",
        "te": "సమీప సంభావ్య చేపల వేట మండలం క్రింద చూపబడింది.",
        "bn": "নিকটতম সম্ভাব্য মৎস্য অঞ্চল নীচে দেখানো হয়েছে।",
    },
    "BORDER_SAFE": {
        "en": "Your vessel maintains a safe distance from the International Maritime Boundary Line.",
        "hi": "आपका जहाज अंतरराष्ट्रीय समुद्री सीमा रेखा से सुरक्षित दूरी बनाए हुए है।",
        "ta": "உங்கள் கப்பல் சர்வதேச கடல் எல்லைக் கோட்டிலிருந்து பாதுகாப்பான தூரத்தில் உள்ளது.",
        "ml": "നിങ്ങളുടെ കപ്പൽ അന്താരാഷ്ട്ര സമുദ്ര അതിർത്തി രേഖയിൽ നിന്ന് സുരക്ഷിതമായ അകലം പാലിക്കുന്നു.",
        "te": "మీ నౌక అంతర్జాతీయ సముద్ర సరిహద్దు రేఖ నుండి సురక్షితమైన దూరాన్ని కలిగి ఉంది.",
        "bn": "আপনার জাহাজ আন্তর্জাতিক সামুদ্রিক সীমান্ত রেখা থেকে নিরাপদ দূরত্ব বজায় রেখেছে।",
    },
    "BORDER_WARNING": {
        "en": "WARNING: Your vessel is close to or near the International Maritime Boundary Line. Navigate with caution.",
        "hi": "चेतावनी: आपका जहाज अंतरराष्ट्रीय समुद्री सीमा रेखा के करीब है। सावधानी से नेविगेट करें।",
        "ta": "எச்சரிக்கை: உங்கள் கப்பல் சர்வதேச கடல் எல்லைக் கோட்டிற்கு அருகில் உள்ளது. கவனமாக செல்லுங்கள்.",
        "ml": "മുന്നറിയിപ്പ്: നിങ്ങളുടെ കപ്പൽ അന്താരാഷ്ട്ര സമുദ്ര അതിർത്തി രേഖയ്ക്ക് സമീപമാണ്. ജാഗ്രതയോടെ സഞ്ചരിക്കുക.",
        "te": "హెచ్చరిక: మీ నౌక అంతర్జాతీయ సముద్ర సరిహద్దు రేఖకు సమీపంలో ఉంది. జాగ్రత్తగా నావిగేట్ చేయండి.",
        "bn": "সতর্কতা: আপনার জাহাজ আন্তর্জাতিক সামুদ্রিক সীমান্ত রেখার কাছাকাছি। সতর্কতার সাথে চলুন।",
    },
}


def phrase(key: str, lang: str) -> str:
    table = VERDICT_PHRASES.get(key, {})
    return table.get(lang, table.get("en", ""))
