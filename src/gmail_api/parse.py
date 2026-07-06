def parse_message(msg):
    """
    Parser für Gmail-Metadaten (format=metadata).
    Keine Bodies, keine Attachments, keine MIME-Struktur.
    Nur Header + Labels + IDs.
    """

    payload = msg.get("payload", {})
    headers = payload.get("headers", [])

    # Header-Felder extrahieren
    header_map = {h["name"].lower(): h["value"] for h in headers}

    gmail_id = msg.get("id")
    thread_id = msg.get("threadId")
    size_estimate = msg.get("sizeEstimate")

    rfc822_msgid = header_map.get("message-id")
    in_reply_to = header_map.get("in-reply-to")
    references = header_map.get("references")

    from_addr = header_map.get("from")
    to_addr = header_map.get("to")
    subject = header_map.get("subject")
    date = header_map.get("date")

    labels = msg.get("labelIds", [])

    # Da wir metadata nutzen, gibt es KEINE Attachments und KEINE Bodies.
    # Wir setzen die Werte deterministisch auf None/0.
    has_attachment = False
    attachment_count = 0
    attachment_total_size = 0

    return {
        "gmail_id": gmail_id,
        "thread_id": thread_id,
        "size_estimate": size_estimate,

        "rfc822_msgid": rfc822_msgid,
        "in_reply_to": in_reply_to,
        "references": references,

        "from": from_addr,
        "to": to_addr,
        "subject": subject,
        "date": date,
        "labels": labels,

        "has_attachment": has_attachment,
        "attachment_count": attachment_count,
        "attachment_total_size": attachment_total_size,

        # Bodies existieren im metadata-Modus nicht.
        "text_plain": None,
        "text_html": None,
    }
