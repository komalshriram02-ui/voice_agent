def detect_intent(text: str) -> str:
    text = text.lower()

    if "cancel" in text:
        return "cancel_appointment"

    if "reschedule" in text or "change" in text:
        return "reschedule_appointment"

    if "book" in text or "appointment" in text or "schedule" in text:
        return "book_appointment"

    if "hello" in text or "hi" in text or "hey" in text:
        return "greeting"

    return "unknown"