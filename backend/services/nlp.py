import spacy
from dateparser import parse as parse_date
from datetime import datetime, timedelta
import re

nlp = spacy.load("en_core_web_sm")


def normalize_date_phrases(text):
    match = re.search(
        r"next\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
        text,
        re.IGNORECASE,
    )
    if match:
        weekday = match.group(1).lower()
        today = datetime.now()
        days_ahead = (
            [
                "monday",
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
                "saturday",
                "sunday",
            ].index(weekday)
            - today.weekday()
        ) % 7
        days_ahead += 7 if days_ahead == 0 else 7  # Always push to *next* week
        future_date = today + timedelta(days=days_ahead)
        text = text.replace(match.group(0), future_date.strftime("%Y-%m-%d"))
    else:
        text = text.replace("this", "")

    return text


def extract_title_and_description(text):
    connectors = {"about", "for", "to", "at", "from"}
    tokens = text.split()

    for i, token in enumerate(tokens):
        if token.lower() in connectors:
            title = " ".join(tokens[:i]).strip()
            description = " ".join(tokens[i:]).strip()
            return title, description

    return text.strip(), ""


def parse_task_text(text):
    doc = nlp(text)
    entities = {ent.label_: ent.text for ent in doc.ents}

    due_date = None
    if "DATE" in entities or "TIME" in entities:
        date_text = entities.get("DATE", "") + " " + entities.get("TIME", "")
        date_text = normalize_date_phrases(date_text)
        due_date = parse_date(
            date_text,
            settings={
                "PREFER_DATES_FROM": "future",
                "RELATIVE_BASE": datetime.now(),
            },
            languages=["en"],
        )
    title, description = extract_title_and_description(text)

    # Simple tag guessing
    tags = []
    if "meeting" in text.lower():
        tags.append("meeting")
    if "call" in text.lower():
        tags.append("call")

    if due_date and due_date.time() == datetime.min.time():
        due_date = due_date.replace(hour=9, minute=0)

    return {
        "title": title.strip().capitalize(),
        "due_date": due_date.isoformat() if due_date else None,
        "description": description.strip(),
    }
