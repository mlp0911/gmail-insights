from typing import Dict, List


def compute_thread_depth(references: List[str], in_reply_to: str | None) -> int:
    if references:
        return len(references)
    if in_reply_to:
        return 1
    return 0


def build_thread_index(records: List[Dict]) -> Dict[str, List[Dict]]:
    index: Dict[str, List[Dict]] = {}

    for r in records:
        thread_id = r.get("thread_id")
        gmail_id = r.get("gmail_id")

        if isinstance(thread_id, str) and thread_id:
            key = thread_id
        elif isinstance(gmail_id, str) and gmail_id:
            key = gmail_id
        else:
            key = "unknown"

        index.setdefault(key, []).append(r)

    return index


def add_thread_features(records: List[Dict]) -> List[Dict]:
    for r in records:
        references = r.get("references", [])
        in_reply_to = r.get("in_reply_to")
        depth = compute_thread_depth(references, in_reply_to)
        r["thread_depth"] = depth
    return records
