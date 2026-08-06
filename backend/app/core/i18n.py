import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class I18nLocalizationService:
    """
    Internationalization Architecture service supporting English (en), Tamil (ta), and Hindi (hi).
    """
    SUPPORTED_LANGUAGES = ["en", "ta", "hi"]

    TRANSLATIONS = {
        "en": {
            "welcome": "Welcome to AI Classroom Assistant",
            "attendance_marked": "Attendance marked successfully.",
            "quiz_generated": "Quiz generated with AI."
        },
        "ta": {
            "welcome": "AI வகுப்பறை உதவிமையத்திற்கு வரவேற்கிறோம்",
            "attendance_marked": "வருகை வெற்றிகரமாகப் பதிவு செய்யப்பட்டது.",
            "quiz_generated": "AI மூலம் வினாடி வினா உருவாக்கப்பட்டது."
        },
        "hi": {
            "welcome": "एआई क्लासरूम असिस्टेंट में आपका स्वागत है",
            "attendance_marked": "उपस्थिति सफलतापूर्वक दर्ज की गई।",
            "quiz_generated": "एआई द्वारा क्विज़ तैयार किया गया।"
        }
    }

    @classmethod
    def get_text(cls, key: str, lang: str = "en") -> str:
        """Retrieves localized text string."""
        lang_code = lang.lower() if lang.lower() in cls.SUPPORTED_LANGUAGES else "en"
        return cls.TRANSLATIONS.get(lang_code, {}).get(key, cls.TRANSLATIONS["en"].get(key, key))
