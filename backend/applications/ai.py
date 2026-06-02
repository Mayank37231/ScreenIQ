import json
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Generator

from django.conf import settings


@dataclass
class ScreeningResult:
    score: Decimal
    reasons: list[str]
    raw_text: str


NUMBER_WORDS = {
    "one": Decimal("1"),
    "two": Decimal("2"),
    "three": Decimal("3"),
    "four": Decimal("4"),
    "five": Decimal("5"),
    "six": Decimal("6"),
    "seven": Decimal("7"),
    "eight": Decimal("8"),
    "nine": Decimal("9"),
    "ten": Decimal("10"),
}


def build_screening_messages(job_description: str, resume: str) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are an HR screening assistant. Evaluate only job-relevant skills, "
                "experience, qualifications, and evidence in the resume. Ignore protected "
                "or proxy attributes such as name, age, gender, race, location, school prestige, "
                "and nationality unless the job description explicitly requires a lawful work location."
            ),
        },
        {
            "role": "user",
            "content": (
                "Compare the resume against the job description. Return strict JSON with this schema: "
                '{"score": number from 1 to 10, "reasons": ["reason 1", "reason 2", "reason 3"]}. '
                "The reasons must be concise bullets focused on fit, gaps, and evidence.\n\n"
                f"Job description:\n{job_description}\n\nResume:\n{resume}"
            ),
        },
    ]


def normalize_score(value) -> Decimal:
    if isinstance(value, (int, float, Decimal)):
        score = Decimal(str(value))
    else:
        text = str(value).strip().lower()
        score = NUMBER_WORDS.get(text)
        if score is None:
            match = re.search(r"\b(10|[1-9](?:\.\d+)?)\b", text)
            if not match:
                raise ValueError("AI response did not contain a score from 1 to 10.")
            score = Decimal(match.group(1))

    if score < Decimal("1"):
        score = Decimal("1")
    if score > Decimal("10"):
        score = Decimal("10")
    return score.quantize(Decimal("0.1"))


def parse_screening_text(text: str) -> ScreeningResult:
    try:
        payload = json.loads(text)
        score = normalize_score(payload.get("score"))
        reasons = payload.get("reasons") or []
    except (json.JSONDecodeError, TypeError, InvalidOperation, ValueError):
        score = normalize_score(text)
        reasons = [
            line.strip(" -*\t")
            for line in text.splitlines()
            if line.strip().startswith(("-", "*"))
        ]

    clean_reasons = [str(reason).strip() for reason in reasons if str(reason).strip()][:3]
    while len(clean_reasons) < 3:
        clean_reasons.append("The AI response did not provide this reason clearly.")
    return ScreeningResult(score=score, reasons=clean_reasons, raw_text=text)


def extract_candidate_name(resume: str) -> str:
    for line in resume.splitlines():
        candidate = line.strip()
        if candidate and len(candidate) <= 80 and not any(char.isdigit() for char in candidate):
            return candidate
    return "Unnamed candidate"


def screen_candidate(job_description: str, resume: str) -> ScreeningResult:
    if settings.AI_PROVIDER == "mock":
        text = json.dumps(
            {
                "score": 7.3,
                "reasons": [
                    "Resume shows several relevant skills from the job description.",
                    "Experience appears directionally aligned but lacks some quantified outcomes.",
                    "A human reviewer should confirm depth against the most important requirements.",
                ],
            }
        )
        return parse_screening_text(text)

    from openai import OpenAI

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=build_screening_messages(job_description, resume),
        temperature=0.2,
        response_format={"type": "json_object"},
    )
    return parse_screening_text(response.choices[0].message.content or "")


def stream_screen_candidate(job_description: str, resume: str) -> Generator[str, None, ScreeningResult]:
    if settings.AI_PROVIDER == "mock":
        chunks = [
            '{"score": 7.3, ',
            '"reasons": ["Resume shows relevant skills.", ',
            '"Experience is aligned with the core requirements.", ',
            '"Some gaps need recruiter follow-up."]}',
        ]
        text = ""
        for chunk in chunks:
            text += chunk
            yield chunk
        return parse_screening_text(text)

    from openai import OpenAI

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    stream = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=build_screening_messages(job_description, resume),
        temperature=0.2,
        response_format={"type": "json_object"},
        stream=True,
    )
    text = ""
    for event in stream:
        delta = event.choices[0].delta.content or ""
        if delta:
            text += delta
            yield delta
    return parse_screening_text(text)
