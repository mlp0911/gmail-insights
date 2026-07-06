from typing import Optional, Dict, List


def normalize_message_id(msgid: Optional[str]) -> Optional[str]:
    if msgid is None:
        return None
    return msgid.strip()


def parse_references(references: Optional[str]) -> List[str]:
    if not references:
        return []
    parts = references.split()
    cleaned = [p.strip() for p in parts if p.strip()]
    return cleaned


def extract_id_features(record: Dict) -> Dict:
    rfc822_msgid = normalize_message_id(record.get("rfc822_msgid"))
    in_reply_to = normalize_message_id(record.get("in_reply_to"))
    references_raw = record.get("references")

    if isinstance(references_raw, str):
        references = parse_references(references_raw)
    else:
        references = []

    return {
        "gmail_id": record.get("gmail_id"),
        "thread_id": record.get("thread_id"),
        "rfc822_msgid": rfc822_msgid,
        "in_reply_to": in_reply_to,
        "references": references,
    }
