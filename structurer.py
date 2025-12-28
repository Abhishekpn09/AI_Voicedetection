# structurer.py
import os
import json
import re
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY is missing. Put it in your .env like:\n"
        "OPENAI_API_KEY=sk-xxxx"
    )

client = OpenAI(api_key=OPENAI_API_KEY)


def extract_structured_data(transcript: str) -> dict:
    """
    Extract fields from transcript using GPT.
    Returns dict with keys:
    jobtitle, nationality, expat, interested_products, lead_status
    """

    schema = {
        "jobtitle": "",
        "nationality": "",
        "expat": "",  # must be "true" or "false"
        "interested_products": "",  # comma-separated string
        "lead_status": ""
    }

    # IMPORTANT: no .format(), no f-string containing JSON braces.
    prompt = (
        "Extract CRM fields from the transcript.\n"
        "Return ONLY valid JSON. No extra text.\n\n"
        "Rules:\n"
        "- Transcript may be German or English.\n"
        '- expat must be "true" or "false" (strings).\n'
        "- nationality must be a COUNTRY name (e.g. Indien, Deutschland).\n"
        "- interested_products must be a comma-separated string.\n\n"
        "Return JSON exactly in this schema:\n"
        + json.dumps(schema, ensure_ascii=False, indent=2)
        + "\n\nTranscript:\n\"\"\"\n"
        + (transcript or "")
        + "\n\"\"\"\n"
    )

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {"role": "system", "content": "You extract CRM-ready structured data. Output ONLY valid JSON."},
            {"role": "user", "content": prompt},
        ],
    )

    raw = (resp.choices[0].message.content or "").strip()

    # Strict parse, fallback to extracting JSON block
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            return {}
        data = json.loads(match.group(0))

    # Ensure all keys exist
    for k in schema.keys():
        data.setdefault(k, "")

    # Normalize expat strictly to "true"/"false" if model returns variants
    exp = str(data.get("expat", "")).strip().lower()
    if exp in ["true", "yes", "ja", "1"]:
        data["expat"] = "true"
    elif exp in ["false", "no", "nein", "0"]:
        data["expat"] = "false"
    else:
        data["expat"] = ""

    # Ensure interested_products is a string (not list)
    if isinstance(data.get("interested_products"), list):
        data["interested_products"] = ", ".join([str(x) for x in data["interested_products"]])

    return data

