import requests
from config import BREVO_API_KEY

EMAIL_SUBJECT = "Quick question, {first_name}"

EMAIL_BODY = """Hi {first_name},

I came across {company} while researching high-growth teams in your space — impressive work.

We help companies like yours cut prospecting time by 60% using automated outreach pipelines. Most of our clients see qualified meetings booked within the first week.

Worth a 15-minute call this week to see if it's a fit?

Best,
Fahad Khan
fahadk3384@gmail.com
"""

def send_emails(contacts: list[dict], sender_email: str, sender_name: str) -> None:
    """
    Sends personalized email to each verified contact via Brevo
    """
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "api-key": BREVO_API_KEY,
        "Content-Type": "application/json"
    }

    sent = 0
    failed = 0

    for contact in contacts:
        first_name = contact.get("first_name") or contact.get("name", "").split()[0]
        company = contact.get("company", "your company")
        email = contact.get("email")

        if not email:
            continue

        personalized_subject = EMAIL_SUBJECT.format(first_name=first_name)
        personalized_body = EMAIL_BODY.format(
            first_name=first_name,
            company=company
        )

        payload = {
            "sender": {"name": sender_name, "email": sender_email},
            "to": [{"email": email, "name": contact.get("name", "")}],
            "subject": personalized_subject,
            "textContent": personalized_body
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            response.raise_for_status()
            print(f"  [Brevo] ✓ Sent to {contact['name']} <{email}>")
            sent += 1

        except requests.exceptions.HTTPError as e:
            print(f"  [Brevo] ✗ Failed for {email}: {e.response.status_code} — {e.response.text}")
            failed += 1

    print(f"  [Brevo] Done — {sent} sent, {failed} failed.")