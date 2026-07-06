import sys
import subprocess

# src/ importierbar machen
sys.path.append("src")

from gmail_api.auth import get_service
from gmail_api.fetch import list_message_ids

from src.features.transform import (
    cache_raw_messages,
    load_cached_messages,
    build_feature_batch_from_cache,
    compute_purge_candidates,
    compute_keep_list,
    compute_keep_scores,
)

# ---------------------------------------------------------
# Deine eigenen Adressen (SELF)
# ---------------------------------------------------------
SELF_EMAILS = {
    "ml.leipold@gmail.com",
    "ml.leipold@outlook.de",
    "michael.leipold@web.de",
    "michael.leipold@siemens.com",
    "ml.leipold@googlemail.com",
    "mlp001@vodafonemail.de",
}

YOUR_EMAIL = "SELF"

# ---------------------------------------------------------
# Pager für lange Ausgaben
# ---------------------------------------------------------
def pager(text):
    p = subprocess.Popen(["less"], stdin=subprocess.PIPE)
    p.communicate(input=text.encode("utf-8"))

# ---------------------------------------------------------
# Hauptprogramm
# ---------------------------------------------------------
def main():
    print("Gmail Insights")
    print("==============")
    print("1) Cache neu einlesen")
    print("2) Analyse aus lokalem Cache")
    print("3) Beenden")
    print("4) PURGE-Kandidaten (deterministisch)")
    print("5) KEEP-Liste (alle Sender minus PURGE)")
    print("6) Datengetriebener Keep-Score (S_node, Spezifikation)")

    choice = input("Auswahl: ").strip()

    if choice == "3":
        return

    cache_path = "cache/raw_messages.ndjson"

    # ---------------------------------------------------------
    # Cache neu einlesen
    # ---------------------------------------------------------
    if choice == "1":
        print("🔐 Authentifiziere…")
        service = get_service()

        print("📬 Hole IDs…")
        ids = list_message_ids(service)
        print(f"Gefundene Nachrichten: {len(ids)}")

        print(f"💾 Erzeuge Cache unter: {cache_path}")
        cache_raw_messages(service, ids, cache_path=cache_path)

    # ---------------------------------------------------------
    # Cache laden
    # ---------------------------------------------------------
    print("📥 Lade Cache…")
    records = load_cached_messages(cache_path)

    print("⚙️ Baue Features…")
    batch = build_feature_batch_from_cache(records)

    # ---------------------------------------------------------
    # 4) PURGE-Kandidaten
    # ---------------------------------------------------------
    if choice == "4":
        print("🗑️ Bestimme PURGE-Kandidaten…")
        purge = compute_purge_candidates(batch, SELF_EMAILS)

        out = []
        out.append("PURGE-KANDIDATEN (deterministisch)")
        out.append("=================================\n")

        for s in sorted(purge):
            out.append(" " + s)

        pager("\n".join(out))
        return

    # ---------------------------------------------------------
    # 5) KEEP-Liste
    # ---------------------------------------------------------
    if choice == "5":
        print("🔎 Bestimme KEEP-Liste…")
        purge = compute_purge_candidates(batch, SELF_EMAILS)
        keep = compute_keep_list(batch, purge)

        out = []
        out.append("KEEP-LISTE (distinct sender minus PURGE)")
        out.append("=======================================\n")

        for s in keep:
            out.append(" " + s)

        pager("\n".join(out))
        return

    # ---------------------------------------------------------
    # 6) Datengetriebener Keep-Score nach Spezifikation
    # ---------------------------------------------------------
    if choice == "6":
        print("🔗 Berechne datengetriebene Keep-Scores (S_node)…")
        scores = compute_keep_scores(batch, SELF_EMAILS, user_node=YOUR_EMAIL)

        keep = {a: s for a, s in scores.items() if s >= 70.0}
        review = {a: s for a, s in scores.items() if 30.0 <= s < 70.0}
        purge = {a: s for a, s in scores.items() if s < 30.0}

        out = []
        out.append("DATENGETRIEBENER KEEP-SCORE (S_node)")
        out.append("===================================\n")

        out.append("KEEP-ZONE (S >= 70):")
        for a, s in sorted(keep.items(), key=lambda x: -x[1])[:50]:
            out.append(f" {a:40}  {s:6.2f}")

        out.append("\nREVIEW-ZONE (30 <= S < 70):")
        for a, s in sorted(review.items(), key=lambda x: -x[1])[:50]:
            out.append(f" {a:40}  {s:6.2f}")

        out.append("\nPURGE-ZONE (S < 30):")
        for a, s in sorted(purge.items(), key=lambda x: -x[1])[:50]:
            out.append(f" {a:40}  {s:6.2f}")

        pager("\n".join(out))
        return

    # ---------------------------------------------------------
    # 2) Standardanalyse
    # ---------------------------------------------------------
    print("\n📬 Liste aller distinct Absender:")
    distinct_senders = sorted(
        {f["sender_email"] for f in batch if f["sender_email"]}
    )
    for s in distinct_senders:
        print(" -", s)


if __name__ == "__main__":
    main()
