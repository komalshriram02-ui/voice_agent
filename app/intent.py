def detect_intent(text: str) -> str:
    text = text.lower()

    cancel_words = [
        "cancel", "कैंसल", "कैन्सल", "कॅन्सल",
        "रद्द", "रद",
    ]
    reschedule_words = [
        "reschedule", "change", "रीशेड्यूल", "रिशेड्यूल", "बदल",
    ]
    book_words = [
        "book", "appointment", "schedule",
        "बुक", "अपॉइंटमेंट", "अपॉईंटमेंट", "अपोइंटमेंट", "अपॉइन्टमेन्ट",
        "भेटीची वेळ", "वेळ घ्यायची", "वेळ हवी",
        "मुलाकात", "समय",
    ]
    greeting_words = [
        "hello", "hi", "hey",
        "हैलो", "हेलो", "हॅलो", "नमस्ते", "नमस्कार",
    ]

    if any(w in text for w in cancel_words):
        return "cancel_appointment"

    if any(w in text for w in reschedule_words):
        return "reschedule_appointment"

    if any(w in text for w in book_words):
        return "book_appointment"

    if any(w in text for w in greeting_words):
        return "greeting"

    return "unknown"