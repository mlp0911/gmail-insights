from googleapiclient.discovery import build
from .auth import get_credentials


# Wir definieren die Header, die wir wirklich brauchen.
# Alles andere (Body, HTML, MIME, Attachments) wird NICHT geladen.
METADATA_HEADERS = [
    "From",
    "To",
    "Subject",
    "Date",
    "Message-ID",
    "List-Unsubscribe"
]


def get_service():
    creds = get_credentials()
    return build("gmail", "v1", credentials=creds)


def list_message_ids(service, user_id="me"):
    ids = []
    response = service.users().messages().list(userId=user_id).execute()

    if "messages" in response:
        ids.extend([m["id"] for m in response["messages"]])

    while "nextPageToken" in response:
        response = service.users().messages().list(
            userId=user_id,
            pageToken=response["nextPageToken"]
        ).execute()

        if "messages" in response:
            ids.extend([m["id"] for m in response["messages"]])

    return ids


def fetch_message_metadata(service, msg_id, user_id="me"):
    """
    Holt nur die Header-Metadaten einer Nachricht.
    Kein Body, kein HTML, keine Attachments.
    Extrem schnell und quota-schonend.
    """
    return service.users().messages().get(
        userId=user_id,
        id=msg_id,
        format="metadata",
        metadataHeaders=METADATA_HEADERS
    ).execute()
