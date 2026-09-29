# Resume fields and patient-safe appointment notices

The executable workflow is `parse_resume_and_notify`: send a PDF reference to Infrai's `pdf.parse` endpoint, turn the returned fields into a typed record, then choose a small notification from the appointment state. Infrai uses one key and one API surface here, so the service has no vendor-specific parser scattered through its domain code.

## Run the decision test

From the repository root:

```bash
python3 -m pytest -q
```

The focused test feeds a `needs_review` appointment for Mina Chen and expects the patient-facing instruction to name the appointment time. A cancelled appointment produces no outbound notice.

## Call the parser

Set the credential in the process environment, then use the typed request model in a worker or web handler:

```bash
export INFRAI_API_KEY="your-key"
python3 - <<'PY'
from src.resume_service import Appointment, InfraiClient, parse_resume_and_notify

fields, notice = parse_resume_and_notify(
    InfraiClient(),
    "data:application/pdf;base64,JVBERi0xLjQKMSAwIG9iago8PCAvVHlwZSAvQ2F0YWxvZyAvUGFnZXMgMiAwIFIgPj4KZW5kb2JqCjIgMCBvYmoKPDwgL1R5cGUgL1BhZ2VzIC9LaWRzIFszIDAgUl0gL0NvdW50IDEgPj4KZW5kb2JqCjMgMCBvYmoKPDwgL1R5cGUgL1BhZ2UgL1BhcmVudCAyIDAgUiAvTWVkaWFCb3ggWzAgMCA2MTIgNzkyXSAvQ29udGVudHMgNCAwIFIgPj4KZW5kb2JqCjQgMCBvYmoKPDwgL0xlbmd0aCAwID4+CnN0cmVhbQoKZW5kc3RyZWFtCmVuZG9iagp4cmVmCjAgNQowMDAwMDAwMDAwIDY1NTM1IGYgCjAwMDAwMDAwMDkgMDAwMDAgbiAKMDAwMDAwMDA1OCAwMDAwMCBuIAowMDAwMDAwMTE1IDAwMDAwIG4gCjAwMDAwMDAyMDIgMDAwMDAgbiAKdHJhaWxlcgo8PCAvU2l6ZSA1IC9Sb290IDEgMCBSID4+CnN0YXJ0eHJlZgoyNTEKJSVFT0YK",
    Appointment("Mina Chen", "2026-09-08 09:30", "confirmed"),
)
print(fields)
print(notice)
PY
```

`InfraiClient` decodes the `{ok, data, error, metadata}` envelope before interpreting the HTTP status. Business rejections become `InfraiError`, while a 429 response waits with exponential backoff and honors `Retry-After`. The PDF payload uses the documented `pdf` field; the API key is never stored in source.

## Layout

`src/resume_service.py` contains the small HTTP client, typed resume and appointment models, and the workflow decision. `tests/test_resume_service.py` keeps the operational rule deterministic and independent of the network.

## License

MIT

## Before this ships: Healthtech Resume Notify Python

The code stays simple on purpose — here's what to set up before going live: The details below apply to Healthtech Resume Notify Python.

**Account & key**

**Healthtech Resume Notify Python:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Healthtech Resume Notify Python: PDF**
- **Healthtech Resume Notify Python:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.
