import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

HUBSPOT_TOKEN = os.getenv("HUBSPOT_ACCESS_TOKEN")
BASE_URL = "https://api.hubapi.com"

if not HUBSPOT_TOKEN:
    raise ValueError("HUBSPOT_ACCESS_TOKEN not found in .env")

HEADERS_JSON = {
    "Authorization": f"Bearer {HUBSPOT_TOKEN}",
    "Content-Type": "application/json",
}

HEADERS_FILE = {
    "Authorization": f"Bearer {HUBSPOT_TOKEN}",
}

LEAD_STATUS_MAP = {
    "neu": "Neu",
    "in beratung": "In Beratung",
    "beratung": "In Beratung",
    "in bearbeitung": "In Bearbeitung",
    "termin vorgeschlagen": "Termin vorgeschlagen",
    "termin vereinbart": "Termin vereinbart",
    "kunde gewonnen": "Kunde gewonnen",
    "bestandskunde": "Bestandskunde",
    "kein interesse": "Kein Interesse",
    "falsche nummer": "Falsche Nummer ergänzen",
    "falsche nummer ergänzen": "Falsche Nummer ergänzen",
    "wiedervorlage": "Wiedervorlage",
    "bewerber": "Bewerber",
    "kooperationspartner": "Kooperationspartner",
    "beim setter": "Beim Setter",
    "altkontakt": "Altkontakt",
}

NATIONALITY_MAP = {
    "indisch": "Indien",
    "india": "Indien",
    "indian": "Indien",
    "german": "Deutschland",
    "deutsch": "Deutschland",
    "deutschland": "Deutschland",
    "south africa": "Südafrika",
    "southafrica": "Südafrika",
    "südafrika": "Südafrika",
}


def normalize_expat(value: str):
    if value is None:
        return "false"
    v = str(value).strip().lower()
    return "true" if v in ["true", "yes", "ja", "1"] else "false"


def normalize_lead_status(value: str):
    if not value:
        return None
    key = str(value).strip().lower()
    return LEAD_STATUS_MAP.get(key)


def normalize_nationality(value: str):
    if not value:
        return None
    key = str(value).strip().lower()
    return NATIONALITY_MAP.get(key, value)


def get_contact_id_by_email(email: str):
    url = f"{BASE_URL}/crm/v3/objects/contacts/search"
    payload = {
        "filterGroups": [{
            "filters": [{
                "propertyName": "email",
                "operator": "EQ",
                "value": email.strip().lower()
            }]
        }]
    }
    r = requests.post(url, headers=HEADERS_JSON, json=payload, timeout=30)
    r.raise_for_status()
    results = r.json().get("results", [])
    return results[0]["id"] if results else None


def update_contact(contact_id: str, properties: dict):
    if not properties:
        return
    url = f"{BASE_URL}/crm/v3/objects/contacts/{contact_id}"
    r = requests.patch(url, headers=HEADERS_JSON, json={"properties": properties}, timeout=30)
    if not r.ok:
        print("HubSpot update failed:", r.status_code, r.text)
        print("Payload:", json.dumps({"properties": properties}, indent=2, ensure_ascii=False))
        r.raise_for_status()


def upload_file_to_hubspot(audio_path: str):
    """
    Uploads file to HubSpot Files and returns (file_id, file_url).
    """
    url = f"{BASE_URL}/files/v3/files"

    filename = os.path.basename(audio_path)
    name_no_ext = os.path.splitext(filename)[0]

    # Put in a folder in Files
    data = {
        "folderPath": "/email-audio",
        "options": json.dumps({"access": "PRIVATE"}),  # file can still be attached to engagements
    }

    with open(audio_path, "rb") as f:
        files = {
            "file": (filename, f),
        }
        print(" Uploading audio/video file to HubSpot File Manager...")
        r = requests.post(url, headers=HEADERS_FILE, files=files, data=data, timeout=60)

    if not r.ok:
        print(" File upload failed:", r.status_code, r.text)
        r.raise_for_status()

    j = r.json()
    file_id = j.get("id")
    file_url = j.get("url")
    print(f" File uploaded. id={file_id} name={name_no_ext}")
    return file_id, file_url


def create_note_with_attachment(contact_id: str, file_id: str, transcript: str = ""):
    """
    This is the part that makes the file appear in the CONTACT -> Attachments section.
    It works by creating a NOTE engagement and setting hs_attachment_ids.
    """
    url = f"{BASE_URL}/crm/v3/objects/notes"

    # HubSpot expects attachment ids as a STRING (can be comma-separated)
    payload = {
        "properties": {
            "hs_note_body": f"Audio uploaded from email.\n\nTranscript:\n{transcript}" if transcript else "Audio uploaded from email.",
            "hs_timestamp": datetime.utcnow().isoformat() + "Z",
            "hs_attachment_ids": str(file_id),
        },
        "associations": [{
            "to": {"id": str(contact_id)},
            "types": [{
                "associationCategory": "HUBSPOT_DEFINED",
                "associationTypeId": 202  # Note -> Contact
            }]
        }]
    }

    print(" Attaching file to contact (Attachments section) via Note...")
    r = requests.post(url, headers=HEADERS_JSON, json=payload, timeout=30)

    if not r.ok:
        print(" Note creation failed:", r.status_code, r.text)
        print("Payload:", json.dumps(payload, indent=2, ensure_ascii=False))
        r.raise_for_status()

    return r.json()


def save_transcript_to_hubspot(email: str, transcript: str, audio_path: str, data: dict):
    print(f"Looking up HubSpot contact for: {email}")
    contact_id = get_contact_id_by_email(email)

    if not contact_id:
        print(" Contact not found in HubSpot for:", email)
        return

    # ---- Build contact property updates (use YOUR internal names) ----
    props = {}

    # job title (HubSpot internal is jobtitle)
    jobtitle = (data.get("jobtitle") or "").strip()
    if jobtitle:
        props["jobtitle"] = jobtitle

    # nationality internal: nationalitat
    nationality = normalize_nationality(data.get("nationality"))
    if nationality:
        props["nationalitat"] = nationality

    # expat internal: expat (string true/false)
    props["expat"] = normalize_expat(data.get("expat"))

    # interested products internal: interesse
    interested = (data.get("interested_products") or "").strip()
    if interested:
        props["interesse"] = interested

    # pot units internal: pot__einheiten
    pot_val = (data.get("pot_einheiten") or "").strip()
    if pot_val:
        props["pot__einheiten"] = pot_val

    # lead status internal: hs_lead_status (must match allowed options)
    lead_status = normalize_lead_status(data.get("lead_status"))
    if lead_status:
        props["hs_lead_status"] = lead_status
    else:
        if data.get("lead_status"):
            print(" Lead status not mapped, skipping")

    # Update contact
    update_contact(contact_id, props)

    # Print what was updated
    for k, v in props.items():
        print(f" {k} updated → {v}")

    # ---- Upload file and attach to contact ----
    file_id, file_url = upload_file_to_hubspot(audio_path)

    # If you want it in Attachments section, you MUST attach via engagement (note)
    create_note_with_attachment(contact_id, file_id, transcript="")

    print(" HubSpot update complete\n")














