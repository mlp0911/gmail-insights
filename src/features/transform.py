from typing import Dict, List
import os
import json
import time
from collections import Counter
from tqdm import tqdm

import pandas as pd
import math
import networkx as nx
from datetime import datetime

from src.gmail_api.fetch import fetch_message_metadata
from src.gmail_api.parse import parse_message
from src.features.sender import classify_sender_header

# ---------------------------------------------------------------------------
# CONFIG LADEN
# ---------------------------------------------------------------------------

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "config", "purge_rules.json")

def load_purge_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# 1) RATE-LIMITIERTER, METADATA-BASIERTER CACHE-BUILDER
# ---------------------------------------------------------------------------

def cache_raw_messages(service, ids, cache_path="cache/raw_messages.ndjson"):
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)

    RATE_LIMIT_SECONDS = 0.20
    last_call = 0.0

    with open(cache_path, "w") as f, tqdm(total=len(ids), desc="Cache wird erzeugt", unit="msg") as bar:
        for msg_id in ids:
            now = time.monotonic()
            delta = now - last_call
            if delta < RATE_LIMIT_SECONDS:
                time.sleep(RATE_LIMIT_SECONDS - delta)
            last_call = time.monotonic()

            raw = fetch_message_metadata(service, msg_id)
            raw["gmail_id"] = msg_id

            f.write(json.dumps(raw))
            f.write("\n")

            bar.update(1)

    return cache_path


# ---------------------------------------------------------------------------
# 2) CACHE LADEN
# ---------------------------------------------------------------------------

def load_cached_messages(cache_path="cache/raw_messages.ndjson"):
    records = []
    with open(cache_path, "r") as f:
        for line in f:
            records.append(json.loads(line))
    return records


# ---------------------------------------------------------------------------
# 3) FEATURE-EXTRAKTION
# ---------------------------------------------------------------------------

def _build_features_single(raw):
    parsed = parse_message(raw)
    sender = classify_sender_header(parsed)

    return {
        "gmail_id": parsed.get("gmail_id"),
        "thread_id": parsed.get("thread_id"),

        "sender_name": sender["name"],
        "sender_email": sender["email"],
        "sender_domain": sender["domain"],
        "sender_org": sender["org"],
        "sender_category": sender["category"],

        "subject": sender["subject"],
        "subject_type": sender["subject_type"],

        "date": sender["date"],

        "labels": sender["labels"],
        "is_important": sender["is_important"],
        "is_unread": sender["is_unread"],
        "is_updates": sender["is_updates"],
        "is_promotions": sender["is_promotions"],
        "is_spam": sender["is_spam"],
        "is_personal": sender["is_personal"],

        "from": parsed.get("from"),
        "to": parsed.get("to"),
        "cc": parsed.get("cc"),
    }


def build_feature_batch_from_cache(records: List[Dict]) -> List[Dict]:
    return [_build_features_single(r) for r in records]


# ---------------------------------------------------------------------------
# 4, 5, 6 WERDEN ENTFERNT (wie von dir gefordert)
# ---------------------------------------------------------------------------
# extract_sender_stats
# build_sender_graph
# find_singletons
# find_low_activity_nodes
# find_isolated_noise
# build_communication_graph
# score_sender_importance
# find_true_noise_nodes
#
# Diese Funktionen sind vollständig entfernt.


# ---------------------------------------------------------------------------
# 7) PURGE-KANDIDATEN (deterministisch, konfigurierbar)
# ---------------------------------------------------------------------------

def compute_purge_candidates(batch, self_emails):
    cfg = load_purge_config()

    purge = set()

    newsletter_domains = cfg["newsletter_domains"]
    newsletter_tokens = cfg["newsletter_tokens"]
    spam_labels = set(cfg["spam_labels"])
    noreply_prefixes = cfg["noreply_prefixes"]
    system_senders = cfg["system_senders"]
    freq_threshold = cfg["frequency_threshold"]

    for f in batch:
        sender = f.get("sender_email")
        if not sender or sender in self_emails:
            continue

        subj = (f.get("subject") or "").lower()
        domain = (f.get("sender_domain") or "").lower()
        labels = set(f.get("labels") or [])

        # Newsletter-Domain
        if any(d in domain for d in newsletter_domains):
            purge.add(sender)
            continue

        # Newsletter-Betreff
        if any(tok in subj for tok in newsletter_tokens):
            purge.add(sender)
            continue

        # Spam-Labels
        if labels & spam_labels:
            purge.add(sender)
            continue

        # No-Reply
        if any(sender.lower().startswith(p) for p in noreply_prefixes):
            purge.add(sender)
            continue

        # System-Absender
        if any(p in sender.lower() for p in system_senders):
            purge.add(sender)
            continue

    # Frequenzbasierte Spam-Erkennung
    freq = Counter([f.get("sender_email") for f in batch if f.get("sender_email")])
    for sender, count in freq.items():
        if count > freq_threshold:
            purge.add(sender)

    return purge


# ---------------------------------------------------------------------------
# 8) KEEP-LISTE (alle Sender, die NICHT in PURGE sind)
# ---------------------------------------------------------------------------

def compute_keep_list(batch, purge):
    all_senders = {f.get("sender_email") for f in batch if f.get("sender_email")}
    return sorted(all_senders - purge)


# ---------------------------------------------------------------------------
# 9) compute_keep_scores bleibt unverändert (du hast NICHT erlaubt, sie zu löschen)
# ---------------------------------------------------------------------------

def compute_keep_scores(batch, self_emails, user_node="SELF"):
    # (EXAKT deine Version aus dem Attachment, unverändert)
    # (Ich lasse sie hier unverändert stehen, da du sie NICHT zum Entfernen freigegeben hast.)
    # (Wenn du sie entfernen willst, sag es explizit.)
    rows = []
    for f in batch:
        sender = f.get("sender_email")
        if not sender or sender in self_emails:
            continue

        ts = f.get("date")
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except Exception:
            try:
                dt = datetime.strptime(ts, "%a, %d %b %Y %H:%M:%S %z")
            except Exception:
                dt = None

        rows.append({
            "from_address": sender,
            "thread_id": f.get("thread_id"),
            "subject": (f.get("subject") or ""),
            "timestamp": dt,
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return {}

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    thread_sizes = df.groupby("thread_id").size().rename("thread_size")
    df = df.join(thread_sizes, on="thread_id")
    df["W_thread"] = (df["thread_size"] + 1).apply(lambda n: math.log(n))

    prefixes = ("re:", "aw:", "fwd:", "wg:")
    def has_prefix(subj: str) -> int:
        s = subj.lower().strip()
        return 1 if any(s.startswith(p) for p in prefixes) else 0

    df["has_prefix"] = df["subject"].apply(has_prefix)
    df["W_dialog"] = df["has_prefix"] * 2.5

    def time_bonus(ts: datetime) -> float:
        if ts is None:
            return 1.0
        hour = ts.hour
        weekday = ts.weekday()
        if weekday >= 5 or hour < 6 or hour >= 19:
            return 1.2
        return 1.0

    df["W_time"] = df["timestamp"].apply(time_bonus)

    spam_tokens = ["rabatt", "newsletter", "%", "sale", "angebot", "deal"]
    def spam_multiplier(subj: str) -> float:
        s = subj.lower()
        hits = 0
        for tok in spam_tokens:
            if tok in s:
                hits += 1
        hits += s.count("!") + s.count("🎉") + s.count("✅")

        if hits == 0:
            return 1.0
        elif hits <= 2:
            return 0.9
        else:
            return 0.8

    df["M_spam"] = df["subject"].apply(spam_multiplier)

    df_sorted = df.sort_values(["from_address", "timestamp"])
    df_sorted["delta_t"] = df_sorted.groupby("from_address")["timestamp"].diff().dt.total_seconds()

    sigma = df_sorted.groupby("from_address")["delta_t"].std().rename("sigma_dt")

    def is_cron_minute(ts: datetime) -> int:
        if ts is None:
            return 0
        return 1 if ts.minute in (0, 15, 30, 45) else 0

    df["cron_flag"] = df["timestamp"].apply(is_cron_minute)
    cron_ratio = df.groupby("from_address")["cron_flag"].mean().rename("P_cron")

    auto_df = pd.concat([sigma, cron_ratio], axis=1).fillna(0.0)

    def auto_factor(row) -> float:
        s = row["sigma_dt"]
        p = row["P_cron"]
        if s < 60 and p > 0.7:
            return 0.5
        return 1.0

    auto_df["F_auto"] = auto_df.apply(auto_factor, axis=1)

    human_bonus = {}
    for f in batch:
        sender = f.get("sender_email")
        if not sender or sender in self_emails:
            continue

        from_you = f.get("from") in self_emails
        to_you = any(addr in self_emails for addr in (f.get("to") or []))
        cc_you = any(addr in self_emails for addr in (f.get("cc") or []))

        if from_you or to_you or cc_you:
            human_bonus.setdefault(sender, {"from_you": False, "to_you": False})
            if from_you:
                human_bonus[sender]["from_you"] = True
            if to_you or cc_you:
                human_bonus[sender]["to_you"] = True

    G = nx.Graph()
    G.add_node(user_node)

    for addr in df["from_address"].unique():
        G.add_node(addr)

    for _, row in df.iterrows():
        addr = row["from_address"]
        w = (row["W_thread"] + row["W_dialog"]) * row["W_time"] * row["M_spam"]
        if G.has_edge(user_node, addr):
            G[user_node][addr]["weight"] += w
        else:
            G.add_edge(user_node, addr, weight=w)

    clustering_raw = nx.clustering(G)
    if isinstance(clustering_raw, dict):
        clustering = clustering_raw
    else:
        clustering = {n: 0.0 for n in G.nodes()}

    edge_weights = {}
    for addr in df["from_address"].unique():
        if G.has_edge(user_node, addr):
            edge_weights[addr] = G[user_node][addr]["weight"]
        else:
            edge_weights[addr] = 0.0

    scores_raw = {}
    for addr in df["from_address"].unique():
        base_sum = edge_weights.get(addr, 0.0)
        f_auto = auto_df.loc[addr, "F_auto"] if addr in auto_df.index else 1.0
        c_node = clustering.get(addr, 0.0)

        s_node = base_sum * f_auto * (1.0 + c_node)

        hb = human_bonus.get(addr, {"from_you": False, "to_you": False})
        if hb["from_you"] and hb["to_you"]:
            s_node += 30.0
        elif hb["to_you"]:
            s_node += 15.0

        scores_raw[addr] = s_node

    if not scores_raw:
        return {}

    vals = list(scores_raw.values())
    min_v = min(vals)
    max_v = max(vals)

    if max_v == min_v:
        scores_norm = {addr: 50.0 for addr in scores_raw.keys()}
    else:
        scores_norm = {
            addr: ((val - min_v) / (max_v - min_v)) * 100.0
            for addr, val in scores_raw.items()
        }

    return scores_norm
