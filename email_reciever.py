import os
import base64
import re
import pickle
from email import message_from_bytes

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from transcriber import transcribe_file
from structurer import extract_structured_data
from hubspot_writer import save_transcript_to_hubspot

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

DOWNLOAD_DIR = "downloads_from_gmail"
TRANSCRIPT_DIR = "transcripts_from_gmail"


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def get_gmail_service():
    creds = None
    if os.path.exists("token_gmail.pickle"):
        with open("token_gmail.pickle", "rb") as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open("token_gmail.pickle", "wb") as f:
            pickle.dump(creds, f)

    return build("gmail", "v1", credentials=creds)


def list_recent_emails(service, max_results=20):
    res = service.users().messages().list(
        userId="me", q="has:attachment", maxResults=max_results
    ).execute()
    return res.get("messages", [])


def process_emails():
    target_email = input(
        "Enter the email address you want to process: "
    ).strip().lower()

    service = get_gmail_service()
    ensure_dir(DOWNLOAD_DIR)
    ensure_dir(TRANSCRIPT_DIR)

    messages = list_recent_emails(service)

    found_any = False

    for msg in messages:
        msg_data = service.users().messages().get(
            userId="me", id=msg["id"], format="raw"
        ).execute()

        raw = base64.urlsafe_b64decode(msg_data["raw"])
        email_msg = message_from_bytes(raw)

        subject = email_msg.get("Subject", "").lower()

        # ✅ SUBJECT decides which contact to update
        if target_email not in subject:
            continue

        found_any = True
        print(f"\nEmail subject matched: {subject}")

        if not email_msg.is_multipart():
            continue

        for part in email_msg.walk():
            filename = part.get_filename()
            if not filename:
                continue

            if not filename.lower().endswith(
                (".mp3", ".wav", ".m4a", ".mp4")
            ):
                continue

            payload = part.get_payload(decode=True)
            if not payload:
                continue

            audio_path = os.path.join(DOWNLOAD_DIR, filename)
            with open(audio_path, "wb") as f:
                f.write(payload)

            print(f"Saved attachment → {audio_path}")

            transcript = transcribe_file(audio_path, model_size="base")

            txt_path = os.path.join(
                TRANSCRIPT_DIR,
                target_email.replace("@", "_").replace(".", "_") + ".txt",
            )
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(transcript)

            structured_data = extract_structured_data(transcript)

            save_transcript_to_hubspot(
                target_email, transcript, audio_path, structured_data
            )

    if not found_any:
        print(
            f"No emails with audio attachments found for {target_email}."
        )


if __name__ == "__main__":
    process_emails()




