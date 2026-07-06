import re
import json
from datetime import datetime


# ---------------------------------------------------------------------------
# JSON-Konfiguration laden
# ---------------------------------------------------------------------------

def load_classification_config():
    with open("config/classification.json", "r", encoding="utf-8") as f:
        return json.load(f)


CFG = load_classification_config()


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def match_any(text, keywords):
    """Prüft, ob eines der Keywords im Text vorkommt."""
    if not text:
        return False
    text = text.lower()
    return any(k.lower() in text for k in keywords)


def classify_domain(domain):
    """Domain-Kategorie anhand JSON-Konfiguration bestimmen."""
    if domain is None:
        return "unknown"

    domain_lower = domain.lower()

    for cat, patterns in CFG["domains"].items():
        if any(p.lower() in domain_lower for p in patterns):
            return cat

    return "other"


def classify_subject(subject):
    """Subject-Kategorie anhand JSON-Konfiguration bestimmen."""
    subject_lower = (subject or "").lower()

    for cat, keywords in CFG["subject_keywords"].items():
        if match_any(subject_lower, keywords):
            return cat

    return "general"


def classify_labels(labels):
    """Label-Features anhand JSON-Konfiguration bestimmen."""
    return {
        "is_important": CFG["labels"]["important"] in labels,
        "is_unread": CFG["labels"]["unread"] in labels,
        "is_updates": CFG["labels"]["updates"] in labels,
        "is_promotions": CFG["labels"]["promotions"] in labels,
        "is_spam": CFG["labels"]["spam"] in labels,
        "is_personal": CFG["labels"]["personal"] in labels,
    }


# ---------------------------------------------------------------------------
# Hauptfunktion: classify_sender_header()
# ---------------------------------------------------------------------------

def classify_sender_header(parsed):
    """
    Extrahiert Absender-bezogene Features aus dem parse_message()-Ergebnis.
    Nutzt ausschließlich Header-Daten:
      - from
      - subject
      - date
      - labels
    JSON-Konfiguration steuert Domain-, Subject- und Label-Klassifizierung.
    """

    # -----------------------------
    # Basisfelder
    # -----------------------------
    from_addr = parsed.get("from") or ""
    subject = parsed.get("subject") or ""
    date_raw = parsed.get("date")
    labels = parsed.get("labels", [])

    # -----------------------------
    # Name extrahieren
    # -----------------------------
    name_match = re.match(r'(.*)<', from_addr)
    name = name_match.group(1).strip() if name_match else None

    # -----------------------------
    # Email extrahieren
    # -----------------------------
    email_match = re.search(r'<(.+?)>', from_addr)
    email = email_match.group(1).strip().lower() if email_match else None

    # -----------------------------
    # Domain & Organisation
    # -----------------------------
    domain = email.split("@")[1] if email else None
    org = domain.split(".")[0] if domain else None

    # -----------------------------
    # Datum normalisieren
    # -----------------------------
    date_obj = None
    if date_raw:
        try:
            cleaned = date_raw.split("(")[0].strip()
            date_obj = datetime.strptime(cleaned, "%a, %d %b %Y %H:%M:%S %z")
        except Exception:
            date_obj = None

    # -----------------------------
    # Kategorie aus Domain (JSON)
    # -----------------------------
    category = classify_domain(domain)

    # -----------------------------
    # Subject-Typ aus JSON
    # -----------------------------
    subject_type = classify_subject(subject)

    # -----------------------------
    # Labels aus JSON
    # -----------------------------
    label_features = classify_labels(labels)

    # -----------------------------
    # Ergebnis zurückgeben
    # -----------------------------
    return {
        "name": name,
        "email": email,
        "domain": domain,
        "org": org,
        "category": category,

        "subject": subject,
        "subject_type": subject_type,

        "date": date_obj,
        "labels": labels,

        "is_important": label_features["is_important"],
        "is_unread": label_features["is_unread"],
        "is_updates": label_features["is_updates"],
        "is_promotions": label_features["is_promotions"],
        "is_spam": label_features["is_spam"],
        "is_personal": label_features["is_personal"],
    }
