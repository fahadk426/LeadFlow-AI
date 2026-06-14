import requests
import time
from config import PROSPEO_API_KEY

HEADERS = {
    "Content-Type": "application/json",
    "X-KEY": PROSPEO_API_KEY
}

DECISION_MAKER_KEYWORDS = [
    "ceo", "cto", "coo", "cfo", "founder", "president", "chief",
    "vp", "vice president", "head of", "head", "director", "partner",
    "owner", "principal", "general manager", "executive"
]

RETRY_SLEEP_SECONDS = 10
MAX_429_RETRIES = 1


def _is_decision_maker(title: str) -> bool:
    if not title:
        return False
    title = title.lower()
    return any(keyword in title for keyword in DECISION_MAKER_KEYWORDS)


def _post_request(url: str, payload: dict, timeout: int = 20) -> requests.Response:
    for attempt in range(MAX_429_RETRIES + 1):
        response = requests.post(url, json=payload, headers=HEADERS, timeout=timeout)
        if response.status_code == 429:
            if attempt < MAX_429_RETRIES:
                print(f"  [Prospeo] 429 rate limit received, sleeping {RETRY_SLEEP_SECONDS}s before retry...")
                time.sleep(RETRY_SLEEP_SECONDS)
                continue
        return response
    return response


def get_contacts(domains: list[str]) -> list[dict]:
    """
    Takes a list of domains
    Returns a list of contacts: [{name, first_name, linkedin_url, title, company, person_id}, ...]
    """
    all_contacts = []

    for i, domain in enumerate(domains):
        print(f"  [Prospeo] {i+1}/{len(domains)} — searching {domain}...")

        url = "https://api.prospeo.io/search-person"
        payload = {
            "page": 1,
            "filters": {
                "company": {
                    "websites": {"include": [domain]}
                }
            }
        }

        try:
            response = _post_request(url, payload, timeout=20)
            response.raise_for_status()
            data = response.json()

            results = data.get("results", [])
            for result in results:
                person = result.get("person", {})
                company = result.get("company", {})
                if not person:
                    continue

                title = person.get("current_job_title") or person.get("headline", "")
                if not _is_decision_maker(title):
                    continue

                name = person.get("full_name") or " ".join(filter(None, [person.get("first_name"), person.get("last_name")]))
                first_name = person.get("first_name") or (name.split()[0] if name else "")
                linkedin_url = person.get("linkedin_url")
                company_name = company.get("name") or domain
                company_domain = company.get("domain") or company.get("website") or domain

                all_contacts.append({
                    "name": name,
                    "first_name": first_name,
                    "title": title,
                    "linkedin_url": linkedin_url,
                    "company": company_name,
                    "company_domain": company_domain,
                    "person_id": person.get("person_id")
                })

        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else "?"
            text = e.response.text if e.response is not None else str(e)
            print(f"  [Prospeo] Error for {domain}: {status} — {text}")
        except Exception as e:
            print(f"  [Prospeo] Error for {domain}: {e}")

        time.sleep(0.5)

    seen = set()
    unique_contacts = []
    for c in all_contacts:
        key = c.get("person_id") or c.get("linkedin_url") or c.get("name")
        if key and key not in seen:
            seen.add(key)
            unique_contacts.append(c)

    print(f"  [Prospeo] Total unique decision-makers found: {len(unique_contacts)}")
    return unique_contacts


def resolve_emails(contacts: list[dict]) -> list[dict]:
    """
    Takes contacts with person_id or linkedin_url
    Uses Enrich Person to resolve a verified email
    Returns only contacts where an email was found
    """
    verified = []

    for i, contact in enumerate(contacts):
        person_id = contact.get("person_id")
        linkedin_url = contact.get("linkedin_url")
        if not person_id and not linkedin_url:
            print(f"  [Resolve] Skipping {contact.get('name')} — no identifier")
            continue

        print(f"  [Resolve] {i+1}/{len(contacts)} — resolving {contact['name']}...")

        enrich_url = "https://api.prospeo.io/enrich-person"
        enrich_payload = {"data": {}}
        if person_id:
            enrich_payload["data"]["person_id"] = person_id
        else:
            enrich_payload["data"]["linkedin_url"] = linkedin_url

        try:
            response = _post_request(enrich_url, enrich_payload, timeout=20)
            response.raise_for_status()
            enrich_data = response.json()
            person_data = enrich_data.get("person", {})
            email_info = person_data.get("email", {})
            email = email_info.get("email") if email_info else None

            if email and email_info.get("revealed"):
                contact["email"] = email
                verified.append(contact)
                print(f"  [Resolve] ✓ {contact['name']} → {email}")
            else:
                print(f"  [Resolve] ✗ No verified email found for {contact['name']}")

        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else "?"
            text = e.response.text if e.response is not None else str(e)
            print(f"  [Resolve] Enrich Person error for {contact['name']}: {status} — {text}")
        except Exception as e:
            print(f"  [Resolve] Enrich Person error for {contact['name']}: {e}")

        time.sleep(1)

    print(f"  [Resolve] Resolved {len(verified)}/{len(contacts)} contacts.")
    return verified