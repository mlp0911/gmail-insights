from typing import Dict


def extract_attachment_features(record: Dict) -> Dict:
    has_attachment = bool(record.get("has_attachment"))
    attachment_count = int(record.get("attachment_count") or 0)
    attachment_total_size = int(record.get("attachment_total_size") or 0)
    size_estimate = int(record.get("size_estimate") or 0)

    return {
        "has_attachment": has_attachment,
        "attachment_count": attachment_count,
        "attachment_total_size": attachment_total_size,
        "size_estimate": size_estimate,
    }
