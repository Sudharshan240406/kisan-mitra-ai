import logging
from enum import Enum
from typing import Any, Optional, Dict, Tuple

logger = logging.getLogger("kisan_mitra_ai.ivr.ivr_flow")


class IVRState(str, Enum):
    GREETING = "GREETING"
    LANGUAGE_SELECTION = "LANGUAGE_SELECTION"
    CALLER_IDENTIFICATION = "CALLER_IDENTIFICATION"
    INTENT_CAPTURE = "INTENT_CAPTURE"
    SCHEME_INQUIRY = "SCHEME_INQUIRY"
    SCHEME_RESULT = "SCHEME_RESULT"
    DOCUMENT_ADVISOR = "DOCUMENT_ADVISOR"
    CLARIFICATION = "CLARIFICATION"
    RECOMMENDATION_PLAYBACK = "RECOMMENDATION_PLAYBACK"
    CONFIRMATION = "CONFIRMATION"
    SUMMARY = "SUMMARY"
    EXIT = "EXIT"
    HUMAN_TRANSFER = "HUMAN_TRANSFER"
    CLOSED = "CLOSED"


DEFAULT_IVR_FLOW_CONFIG: Dict[str, Dict[str, Any]] = {
    "GREETING": {
        "prompts": {
            "hi": "नमस्ते, किसान मित्र एआई में आपका स्वागत है। मैं आपकी सरकारी योजनाओं और खेती की समस्याओं में मदद करूंगा।",
            "en": "Hello, welcome to Kisan Mitra AI. I will help you with government schemes and farming assistance.",
            "kn": "ನಮಸ್ಕಾರ, ಕಿಸಾನ್ ಮಿತ್ರ ಐ ಗೆ ಸುಸ್ವಾಗತ. ನಾನು ನಿಮಗೆ ಸರ್ಕಾರಿ ಯೋಜನೆಗಳು ಮತ್ತು ಕೃಷಿ ಸಹಾಯಕ್ಕೆ ಸಹಾಯ ಮಾಡುತ್ತೇನೆ.",
            "te": "నమస్కారం, కిసాన్ మిత్ర ఐ కి స్వాగతం. ప్రభుత్వ పథకాలు మరియు వ్యవసాయ సహాయంలో నేను మీకు సహాయం చేస్తాను.",
            "ta": "வணக்கம், கிசான் மித்ரா ஐ-க்கு உங்களை வரவேற்கிறோம். அரசு திட்டங்கள் மற்றும் விவசாய உதவிக்கு நான் உங்களுக்கு உதவுவேன்.",
            "pa": "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ, ਕਿਸਾਨ ਮਿੱਤਰ ਏਆਈ ਵਿੱਚ ਤੁਹਾਡਾ ਸੁਆਗਤ ਹੈ। ਮੈਂ ਤੁਹਾਡੀ ਸਰਕਾਰੀ ਯੋਜਨਾਵਾਂ ਅਤੇ ਖੇਤੀਬਾੜੀ ਸਮੱਸਿਆਵਾਂ ਵਿੱਚ ਮਦਦ ਕਰਾਂਗਾ।"
        },
        "next": "LANGUAGE_SELECTION"
    },
    "LANGUAGE_SELECTION": {
        "prompts": {
            "hi": "भाषा चुनने के लिए: हिंदी के लिए 1 दबाएं, For English press 2, ಕನ್ನಡಕ್ಕಾಗಿ 3 ಒತ್ತಿರಿ, తెలుగు కోసం 4 నొక్కండి, தமிழுக்கு 5 அழுத்தவும், ਪੰਜਾਬੀ ਲਈ 6 ਦਬਾਓ।",
            "en": "To select language: Press 1 for Hindi, 2 for English, 3 for Kannada, 4 for Telugu, 5 for Tamil, 6 for Punjabi.",
            "kn": "ಭಾಷೆಯನ್ನು ಆಯ್ಕೆ ಮಾಡಲು: ಹಿಂದಿಗಾಗಿ 1 ಒತ್ತಿರಿ, ಇಂಗ್ಲಿಷ್‌ಗಾಗಿ 2 ಒತ್ತಿರಿ, ಕನ್ನಡಕ್ಕಾಗಿ 3 ಒತ್ತಿರಿ, ತೆಲುಗುಗಾಗಿ 4 ನೊಕ್ಕಿ, ತಮಿಳಿಗಾಗಿ 5 ಒತ್ತಿರಿ.",
            "te": "భాషను ఎంచుకోవడానికి: హిందీ కోసం 1 నొక్కండి, ఇంగ్లీష్ కోసం 2 నొక్కండి, కన్నడ కోసం 3 నొక్కండి, తెలుగు కోసం 4 నొక్కండి, తమిళం కోసం 5 నొక్కండి.",
            "ta": "மொழியைத் தேர்ந்தெடுக்க: இந்திக்கு 1 அழுத்தவும், ஆங்கிலத்திற்கு 2 அழுத்தவும், கன்னடத்திற்கு 3 அழுத்தவும், தெலுங்கிற்கு 4 அழுத்தவும், தமிழிற்கு 5 அழுத்தவும்.",
            "pa": "ਭਾਸ਼ਾ ਚੁਣਨ ਲਈ: ਹਿੰਦੀ ਲਈ 1 ਦਬਾਓ, English ਲਈ 2 ਦਬਾਓ, ਕੰਨੜ ਲਈ 3 ਦਬਾਓ, ਤੇਲਗੂ ਲਈ 4 ਦਬਾਓ, ਤਮਿਲ ਲਈ 5 ਦਬਾਓ, ਪੰਜਾਬੀ ਲਈ 6 ਦਬਾਓ।"
        },
        "dtmf": {
            "1": {"next": "CALLER_IDENTIFICATION", "set_language": "hi"},
            "2": {"next": "CALLER_IDENTIFICATION", "set_language": "en"},
            "3": {"next": "CALLER_IDENTIFICATION", "set_language": "kn"},
            "4": {"next": "CALLER_IDENTIFICATION", "set_language": "te"},
            "5": {"next": "CALLER_IDENTIFICATION", "set_language": "ta"},
            "6": {"next": "CALLER_IDENTIFICATION", "set_language": "pa"}
        },
        "fallback": "LANGUAGE_SELECTION"
    },
    "CALLER_IDENTIFICATION": {
        "prompts": {
            "hi": "यदि आप पंजीकृत किसान हैं तो 1 दबाएं। नए किसान के लिए 2 दबाएं। गेस्ट डेमो के लिए 3 दबाएं।",
            "en": "Press 1 if you are a registered farmer. Press 2 for new registration. Press 3 for guest demo.",
            "kn": "ನೀವು ನೋಂದಾಯಿತ ರೈತರಾಗಿದ್ದರೆ 1 ಒತ್ತಿರಿ. ಹೊಸ ನೋಂದಣಿಗೆ 2 ಒತ್ತಿರಿ. ಅತಿಥಿ ಡೆಮೊಗಾಗಿ 3 ಒತ್ತಿರಿ.",
            "te": "మీరు నమోదిత రైతు అయితే 1 నొక్కండి. కొత్త రిజిస్ట్రేషన్ కోసం 2 నొక్కండి. గెస్ట్ డెమో కోసం 3 నొక్కండి.",
            "ta": "நீங்கள் பதிவுசெய்த விவசாயியாக இருந்தால் 1 அழுத்தவும். புதிய பதிவுக்கு 2 அழுத்தவும். விருந்தினர் டெமோவிற்கு 3 அழுத்தவும்.",
            "pa": "ਜੇ ਤੁਸੀਂ ਰਜਿਸਟਰਡ ਕਿਸਾਨ ਹੋ ਤਾਂ 1 ਦਬਾਓ। ਨਵੇਂ ਕਿਸਾਨ ਲਈ 2 ਦਬਾਓ। ਗੈਸਟ ਡੈਮੋ ਲਈ 3 ਦਬਾਓ।"
        },
        "dtmf": {
            "1": {"next": "INTENT_CAPTURE", "caller_type": "registered"},
            "2": {"next": "INTENT_CAPTURE", "caller_type": "new"},
            "3": {"next": "INTENT_CAPTURE", "caller_type": "guest"}
        },
        "fallback": "CALLER_IDENTIFICATION"
    },
    "INTENT_CAPTURE": {
        "prompts": {
            "hi": "मुख्य मेनू: सरकारी योजनाओं के लिए 1 दबाएं, मौसम के लिए 2, बाजार भाव के लिए 3, फसल रोग के लिए 4, या सहायक से बात करने के लिए 5 दबाएं। मेनू दोबारा सुनने के लिए 9 दबाएं।",
            "en": "Main menu: Press 1 for Government Schemes, 2 for Weather, 3 for Market Prices, 4 for Crop Disease advice, or 5 to speak with an agent. Press 9 to repeat.",
            "kn": "ಮುಖ್ಯ ಮೆನು: ಸರ್ಕಾರಿ ಯೋಜನೆಗಳಿಗಾಗಿ 1 ಒತ್ತಿರಿ, ಹವಾಮಾನಕ್ಕಾಗಿ 2, ಮಾರುಕಟ್ಟೆ ಬೆಲೆಗಾಗಿ 3, ಬೆಳೆ ರೋಗದ ಸಲಹೆಗಾಗಿ 4, ಅಥವಾ ನಮ್ಮ ಸಹಾಯಕರೊಂದಿಗೆ ಮಾತನಾಡಲು 5 ಒತ್ತಿರಿ. ಮೆನು ಪುನರಾವರ್ತಿಸಲು 9 ಒತ್ತಿರಿ.",
            "te": "ముఖ్య మెనూ: ప్రభుత్వ పథకాల కోసం 1 నొక్కండి, వాతావరణం కోసం 2, మార్కెట్ ధరల కోసం 3, పంట తెగుళ్ల సలహా కోసం 4, లేదా మా సహాయకుడితో మాట్లాడటానికి 5 నొక్కండి. మెనూను పునరావృతం చేయడానికి 9 నొక్కండి.",
            "ta": "முதன்மை மெனு: அரசு திட்டங்களுக்கு 1 அழுத்தவும், வானிலைக்கு 2, சந்தை விலைக்கு 3, பயிர் நோய் ஆலோசனைக்கு 4, அல்லது எங்களின் உதவியாளரிடம் பேச 5 அழுத்தவும். மெனுவை மீண்டும் கேட்க 9 அழுத்தவும்.",
            "pa": "ਮੁੱਖ ਮੇਨੂ: ਸਰਕਾਰੀ ਯੋਜਨਾਵਾਂ ਲਈ 1 ਦਬਾਓ, ਮੌਸਮ ਲਈ 2, ਮੰਡੀ ਭਾਅ ਲਈ 3, ਫ਼ਸਲ ਰੋਗ ਲਈ 4, ਜਾਂ ਸਹਾਇਕ ਨਾਲ ਗੱਲ ਲਈ 5 ਦਬਾਓ। ਮੇਨੂ ਦੁਬਾਰਾ ਸੁਣਨ ਲਈ 9 ਦਬਾਓ।"
        },
        "dtmf": {
            "1": {"next": "SCHEME_INQUIRY", "query": "government schemes eligibility"},
            "2": {"next": "RECOMMENDATION_PLAYBACK", "query": "weather forecast"},
            "3": {"next": "RECOMMENDATION_PLAYBACK", "query": "market prices"},
            "4": {"next": "RECOMMENDATION_PLAYBACK", "query": "crop disease advice"},
            "5": {"next": "HUMAN_TRANSFER"},
            "9": {"next": "INTENT_CAPTURE"}
        },
        "fallback": "INTENT_CAPTURE"
    },
    "SCHEME_INQUIRY": {
        "prompts": {
            "hi": "मैं आपके लिए सरकारी योजनाओं की पात्रता जाँच रहा हूँ। कृपया प्रतीक्षा करें...",
            "en": "I am checking your eligibility for government schemes. Please wait...",
            "kn": "ನಾನು ನಿಮಗಾಗಿ ಸರ್ಕಾರಿ ಯೋಜನೆಗಳ ಅರ್ಹತೆಯನ್ನು ಪರಿಶೀಲಿಸುತ್ತಿದ್ದೇನೆ. ದಯವಿಟ್ಟು ಕಾಯಿರಿ...",
            "te": "నేను మీ కోసం ప్రభుత్వ పథకాల అర్హతను తనిఖీ చేస్తున్నాను. దయచేసి వేచి ఉండండి...",
            "ta": "உங்களுக்கான அரசு திட்டங்களின் தகுதியை நான் சரிபார்க்கிறேன். தயவுசெய்து காத்திருக்கவும்...",
            "pa": "ਮੈਂ ਤੁਹਾਡੇ ਲਈ ਸਰਕਾਰੀ ਯੋਜਨਾਵਾਂ ਦੀ ਯੋਗਤਾ ਜਾਂਚ ਰਿਹਾ ਹਾਂ। ਕਿਰਪਾ ਕਰਕੇ ਇੰਤਜ਼ਾਰ ਕਰੋ..."
        },
        "next": "SCHEME_RESULT"
    },
    "SCHEME_RESULT": {
        "prompts": {
            "hi": "यहाँ आपकी योजना की जानकारी है: ",
            "en": "Here is your scheme eligibility information: ",
            "kn": "ನಿಮ್ಮ ಯೋಜನೆಯ ಮಾಹಿತಿ ಇಲ್ಲಿದೆ: ",
            "te": "మీ పథకం సమాచారం ఇక్కడ ఉంది: ",
            "ta": "உங்கள் திட்டம் பற்றிய தகவல் இங்கே: ",
            "pa": "ਇੱਥੇ ਤੁਹਾਡੀ ਯੋਜਨਾ ਦੀ ਜਾਣਕਾਰੀ ਹੈ: "
        },
        "next": "DOCUMENT_ADVISOR"
    },
    "DOCUMENT_ADVISOR": {
        "prompts": {
            "hi": "दस्तावेज़ मार्गदर्शन सुनने के लिए 1 दबाएं। अगली योजना सुनने के लिए 2 दबाएं। मुख्य मेनू के लिए 9 दबाएं।",
            "en": "Press 1 to hear document requirements. Press 2 for next scheme. Press 9 for main menu.",
            "kn": "ದಾಖಲೆ ಅಗತ್ಯತೆಗಳನ್ನು ಕೇಳಲು 1 ಒತ್ತಿರಿ. ಮುಂದಿನ ಯೋಜನೆಗಾಗಿ 2 ಒತ್ತಿರಿ. ಮುಖ್ಯ ಮೆನುಗಾಗಿ 9 ಒತ್ತಿರಿ.",
            "te": "పత్రం అవసరాల గురించి వినడానికి 1 నొక్కండి. తదుపరి పథకం కోసం 2 నొక్కండి. ముఖ్య మెనూ కోసం 9 నొక్కండి.",
            "ta": "ஆவண தேவைகளை கேட்க 1 அழுத்தவும். அடுத்த திட்டத்திற்கு 2 அழுத்தவும். முதன்மை மெனுவிற்கு 9 அழுத்தவும்.",
            "pa": "ਦਸਤਾਵੇਜ਼ ਮਾਰਗਦਰਸ਼ਨ ਸੁਣਨ ਲਈ 1 ਦਬਾਓ। ਅਗਲੀ ਯੋਜਨਾ ਸੁਣਨ ਲਈ 2 ਦਬਾਓ। ਮੁੱਖ ਮੇਨੂ ਲਈ 9 ਦਬਾਓ।"
        },
        "dtmf": {
            "1": {"next": "RECOMMENDATION_PLAYBACK", "query": "document_guidance"},
            "2": {"next": "SCHEME_RESULT", "next_scheme": True},
            "9": {"next": "INTENT_CAPTURE"}
        },
        "fallback": "DOCUMENT_ADVISOR"
    },
    "CLARIFICATION": {
        "prompts": {
            "hi": "कृपया अधिक जानकारी प्रदान करें। अपनी समस्या रिकॉर्ड करने के लिए 1 दबाएं या मुख्य मेनू पर लौटने के लिए 9 दबाएं।",
            "en": "Please provide more details. Press 1 to record your query, or press 9 to return to the main menu.",
            "kn": "ದಯವಿಟ್ಟು ಹೆಚ್ಚಿನ ವಿವರಗಳನ್ನು ನೀಡಿ. ನಿಮ್ಮ ಪ್ರಶ್ನೆಯನ್ನು ರೆಕಾರ್ಡ್ ಮಾಡಲು 1 ಒತ್ತಿರಿ, ಅಥವಾ ಮುಖ್ಯ ಮೆನುಗೆ ಮರಳಲು 9 ಒತ್ತಿರಿ.",
            "te": "దయచేసి మరిన్ని వివరాలను అందించండి. మీ ప్రశ్నను రికార్డ్ చేయడానికి 1 నొక్కండి, లేదా ముఖ్య మెనూకు తిరిగి రావడానికి 9 నొక్కండి.",
            "ta": "கூடுதல் விவரங்களை வழங்கவும். உங்கள் கேள்வியை பதிவு செய்ய 1 அழுத்தவும், அல்லது முதன்மை மெனுவிற்கு திரும்ப 9 அழுத்தவும்.",
            "pa": "ਕਿਰਪਾ ਕਰਕੇ ਹੋਰ ਜਾਣਕਾਰੀ ਦਿਓ। ਆਪਣੀ ਸਮੱਸਿਆ ਰਿਕਾਰਡ ਕਰਨ ਲਈ 1 ਦਬਾਓ ਜਾਂ ਮੁੱਖ ਮੇਨੂ ਤੇ ਜਾਣ ਲਈ 9 ਦਬਾਓ।"
        },
        "dtmf": {
            "1": {"next": "INTENT_CAPTURE", "voice_record": True},
            "9": {"next": "INTENT_CAPTURE"}
        },
        "fallback": "CLARIFICATION"
    },
    "RECOMMENDATION_PLAYBACK": {
        "prompts": {
            "hi": "यहाँ आपकी सलाह है: ",
            "en": "Here is your advisory recommendation: ",
            "kn": "ನಿಮ್ಮ ಕೃಷಿ ಸಲಹೆ ಇಲ್ಲಿದೆ: ",
            "te": "మీ వ్యవసాయ సలహా ఇక్కడ ఉంది: ",
            "ta": "உங்கள் விவசாய ஆலோசனை இதோ: ",
            "pa": "ਇੱਥੇ ਤੁਹਾਡੀ ਸਲਾਹ ਹੈ: "
        },
        "next": "CONFIRMATION"
    },
    "CONFIRMATION": {
        "prompts": {
            "hi": "यदि आप सलाह समझ गए हैं तो 1 दबाएं। सलाह दोबारा सुनने के लिए 2 दबाएं। मुख्य मेनू पर लौटने के लिए 9 दबाएं।",
            "en": "If you understood the advisory, press 1. To repeat the advisory, press 2. To return to the main menu, press 9.",
            "kn": "ನೀವು ಸಲಹೆಯನ್ನು ಅರ್ಥಮಾಡಿಕೊಂಡಿದ್ದರೆ 1 ಒತ್ತಿರಿ. ಸಲಹೆಯನ್ನು ಪುನರಾವರ್ತಿಸಲು 2 ಒತ್ತಿರಿ. ಮುಖ್ಯ ಮೆನುಗೆ ಮರಳಲು 9 ಒತ್ತಿರಿ.",
            "te": "మీకు సలహా అర్థమైతే 1 నొక్కండి. సలహాను పునరావృతం చేయడానికి 2 నొక్కండి. ముఖ్య మెనూకు తిరిగి రావడానికి 9 నొక్కండి.",
            "ta": "ஆலோசனையை நீங்கள் புரிந்து கொண்டால் 1 அழுத்தவும். ஆலோசனையை மீண்டும் கேட்க 2 அழுத்தவும். முதன்மை மெனுவிற்கு திரும்ப 9 அழுத்தவும்.",
            "pa": "ਜੇਕਰ ਤੁਸੀਂ ਸਲਾਹ ਸਮਝ ਗਏ ਹੋ ਤਾਂ 1 ਦਬਾਓ। ਸਲਾਹ ਦੁਬਾਰਾ ਸੁਣਨ ਲਈ 2 ਦਬਾਓ। ਮੁੱਖ ਮੇਨੂ ਤੇ ਜਾਣ ਲਈ 9 ਦਬਾਓ।"
        },
        "dtmf": {
            "1": {"next": "SUMMARY"},
            "2": {"next": "RECOMMENDATION_PLAYBACK", "repeat": True},
            "9": {"next": "INTENT_CAPTURE"}
        },
        "fallback": "CONFIRMATION"
    },
    "SUMMARY": {
        "prompts": {
            "hi": "कॉल सारांश तैयार किया जा रहा है और स्मृति इंजन में सहेजा जा रहा है। धन्यवाद।",
            "en": "Preparing call summary and saving to Memory Engine. Thank you.",
            "kn": "ಕರೆ ಸಾರಾಂಶವನ್ನು ಸಿದ್ಧಪಡಿಸಲಾಗುತ್ತಿದೆ ಮತ್ತು ಮೆಮೊರಿ ಎಂಜಿನ್‌ನಲ್ಲಿ ಉಳಿಸಲಾಗುತ್ತಿದೆ. ಧನ್ಯವಾದಗಳು.",
            "te": "కాల్ సారాంశాన్ని సిద్ధం చేస్తోంది మరియు మెమరీ ఇంజిన్‌లో సేవ్ చేస్తోంది. ధన్యవాదాలు.",
            "ta": "கால் சுருக்கம் தயாரிக்கப்பட்டு மெமரி என்ஜினில் சேமிக்கப்படுகிறது. நன்றி.",
            "pa": "ਕਾਲ ਸਾਰਾਂਸ਼ ਤਿਆਰ ਕੀਤਾ ਜਾ ਰਿਹਾ ਹੈ ਅਤੇ ਮੈਮੋਰੀ ਇੰਜਨ ਵਿੱਚ ਸੁਰੱਖਿਅਤ ਕੀਤਾ ਜਾ ਰਿਹਾ ਹੈ। ਧੰਨਵਾਦ।"
        },
        "next": "EXIT"
    },
    "HUMAN_TRANSFER": {
        "prompts": {
            "hi": "कृपया प्रतीक्षा करें, आपकी कॉल हमारे कृषि विशेषज्ञ को ट्रांसफर की जा रही है।",
            "en": "Please wait while we transfer your call to our agricultural specialist.",
            "kn": "ದಯವಿಟ್ಟು ನಿರೀಕ್ಷಿಸಿ, ನಿಮ್ಮ ಕರೆಯನ್ನು ನಮ್ಮ ಕೃಷಿ ತಜ್ಞರಿಗೆ ವರ್ಗಾಯಿಸಲಾಗುತ್ತಿದೆ.",
            "te": "దయచేసి వేచి ఉండండి, మీ కాల్ మా వ్యవసాయ నిపుణుడికి బదిలీ చేయబడుతోంది.",
            "ta": "தயவுசெய்து காத்திருக்கவும், உங்கள் கால் எங்களது விவசாய நிபுணருக்கு மாற்றப்படுகிறது.",
            "pa": "ਕਿਰਪਾ ਕਰਕੇ ਇੰਤਜ਼ਾਰ ਕਰੋ, ਤੁਹਾਡੀ ਕਾਲ ਸਾਡੇ ਖੇਤੀਬਾੜੀ ਮਾਹਿਰ ਨੂੰ ਟ੍ਰਾਂਸਫਰ ਕੀਤੀ ਜਾ ਰਹੀ ਹੈ।"
        },
        "next": "EXIT"
    },
    "EXIT": {
        "prompts": {
            "hi": "किसान मित्र से संपर्क करने के लिए धन्यवाद। आपकी फसल लहलहाए, आपका दिन शुभ हो!",
            "en": "Thank you for calling Kisan Mitra. Wishing you a great harvest and a wonderful day!",
            "kn": "ಕಿಸಾನ್ ಮಿತ್ರರಿಗೆ ಕರೆ ಮಾಡಿದ್ದಕ್ಕಾಗಿ ಧನ್ಯವಾದಗಳು. ಉತ್ತಮ ಬೆಳೆ ಸಿಗಲಿ, ದಿನ ಶುಭವಾಗಿರಲಿ!",
            "te": "కిసాన్ మిత్రకు కాల్ చేసినందుకు ధన్యవాదాలు. మంచి పంట పండాలని, ఈ రోజు శుభప్రదంగా ఉండాలని కోరుకుంటున్నాము!",
            "ta": "கிசான் மித்ராவுக்கு அழைத்ததற்கு நன்றி. நல்ல அறுவடை பெற வாழ்த்துகிறோம், இனிய நாள் வாழ்த்துக்கள்!",
            "pa": "ਕਿਸਾਨ ਮਿੱਤਰ ਨਾਲ ਸੰਪਰਕ ਕਰਨ ਲਈ ਧੰਨਵਾਦ। ਚੰਗੀ ਫਸਲ ਹੋਵੇ, ਤੁਹਾਡਾ ਦਿਨ ਵਧੀਆ ਰਹੇ!"
        },
        "next": "CLOSED"
    }
}


class IVRFlow:
    """Manages IVR states, transitions, prompts retrieval and configuration mapping."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or DEFAULT_IVR_FLOW_CONFIG

    def get_prompt(self, state: str, language: str) -> str:
        state_cfg = self.config.get(state)
        if not state_cfg:
            return ""
        prompts = state_cfg.get("prompts", {})
        return prompts.get(language, prompts.get("en", ""))

    def get_next_state(self, current_state: str, trigger: str) -> str:
        state_cfg = self.config.get(current_state)
        if not state_cfg:
            return IVRState.EXIT.value
        return state_cfg.get("next", IVRState.EXIT.value)

    async def transition(
        self,
        session: Any,
        trigger: str,
        input_val: Optional[str] = None
    ) -> Tuple[IVRState, str]:
        curr_state = session.current_ivr_state
        state_cfg = self.config.get(curr_state)
        if not state_cfg:
            session.current_ivr_state = IVRState.EXIT.value
            return IVRState.EXIT, self.get_prompt(IVRState.EXIT.value, session.language)
        
        next_state_str = state_cfg.get("next", IVRState.EXIT.value)
        session.current_ivr_state = next_state_str
        prompt = self.get_prompt(next_state_str, session.language)
        return IVRState(next_state_str), prompt

    async def handle_dtmf(self, session: Any, digits: str) -> Tuple[IVRState, str]:
        curr_state = session.current_ivr_state
        state_cfg = self.config.get(curr_state)
        if not state_cfg or "dtmf" not in state_cfg:
            prompt = self.get_prompt(curr_state, session.language)
            return IVRState(curr_state), prompt
        
        dtmf_map = state_cfg["dtmf"]
        action = dtmf_map.get(digits)
        if not action:
            fallback = state_cfg.get("fallback", curr_state)
            session.current_ivr_state = fallback
            prompt = "Invalid input. " + self.get_prompt(fallback, session.language)
            return IVRState(fallback), prompt
        
        next_state = action["next"]
        if "set_language" in action:
            session.language = action["set_language"]
        if "caller_type" in action:
            session.metadata["caller_type"] = action["caller_type"]
        if "query" in action:
            session.metadata["intent_query"] = action["query"]
            
        session.current_ivr_state = next_state
        prompt = self.get_prompt(next_state, session.language)
        return IVRState(next_state), prompt


class IVRStateMachine(IVRFlow):
    """Subclass of IVRFlow for direct compatibility with IVRStateMachine registry configurations."""
    pass

