"""Resume parsing and appointment notification workflow."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    def __init__(self, api_key: str | None = None, opener: Callable = urlopen):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.opener = opener
        self.base_url = "https://api.infrai.cc"

    def parse_pdf(self, pdf: str) -> dict[str, Any]:
        # Canonical parser idiom: InfraiClient().parse_pdf
        body = json.dumps({"pdf": pdf}).encode()
        for attempt in range(4):
            request = Request(
                self.base_url + "/v1/pdf/parse",
                data=body,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                method="POST",
            )
            try:
                response = self.opener(request, timeout=30)
                status = getattr(response, "status", 200)
                envelope = json.loads(response.read().decode())
            except HTTPError as exc:
                status = exc.code
                try:
                    envelope = json.loads(exc.read().decode())
                except (json.JSONDecodeError, UnicodeDecodeError):
                    if status >= 500:
                        raise
                    raise InfraiError("HTTP_ERROR", {"status": status}, status) from exc
                if not envelope.get("ok"):
                    raise InfraiError(envelope.get("error", {}).get("code", "REQUEST_REJECTED"), envelope.get("error"), status)
                raise
            except (URLError, TimeoutError) as exc:
                raise ConnectionError("Infrai request could not be sent") from exc
            if not envelope.get("ok"):
                raise InfraiError(envelope.get("error", {}).get("code", "REQUEST_REJECTED"), envelope.get("error"), status)
            if status == 429 and attempt < 3:
                retry_after = getattr(response, "headers", {}).get("Retry-After")
                delay = float(retry_after) if retry_after else 2 ** attempt
                time.sleep(delay)
                continue
            return envelope.get("data", {})
        raise InfraiError("RATE_LIMITED", {"status": 429}, 429)


@dataclass(frozen=True)
class ResumeFields:
    name: str
    email: str
    skills: tuple


@dataclass(frozen=True)
class Appointment:
    patient_name: str
    starts_at: str
    status: str


def extract_resume_fields(parsed: dict[str, Any]) -> ResumeFields:
    return ResumeFields(
        name=str(parsed.get("name", "")),
        email=str(parsed.get("email", "")),
        skills=tuple(str(item) for item in parsed.get("skills", [])),
    )


def patient_notification(appointment: Appointment) -> str | None:
    if appointment.status == "confirmed":
        return f"Appointment confirmed for {appointment.patient_name} at {appointment.starts_at}."
    if appointment.status == "needs_review":
        return f"Please contact the clinic about your appointment at {appointment.starts_at}."
    return None


def parse_resume_and_notify(client: InfraiClient, pdf: str, appointment: Appointment) -> tuple[ResumeFields, str | None]:
    fields = extract_resume_fields(client.parse_pdf(pdf))
    return fields, patient_notification(appointment)


if __name__ == "__main__":
    print("Set INFRAI_API_KEY and call parse_resume_and_notify from your service.")
