import requests
import time
from config import OCEAN_API_KEY

RETRY_SLEEP_SECONDS = 10
MAX_429_RETRIES = 1


def _post_request(url: str, payload: dict, headers: dict, timeout: int = 15) -> requests.Response:
    for attempt in range(MAX_429_RETRIES + 1):
        response = requests.post(url, json=payload, headers=headers, timeout=timeout)
        if response.status_code == 429:
            if attempt < MAX_429_RETRIES:
                print(f"  [Ocean.io] 429 rate limit received, sleeping {RETRY_SLEEP_SECONDS}s before retry...")
                time.sleep(RETRY_SLEEP_SECONDS)
                continue
        return response
    return response


def get_lookalikes(seed_domain: str, max_results: int = 20) -> list[str]:
    """
    Takes a seed domain like 'stripe.com'
    Returns a list of similar company domains like ['razorpay.com', 'paddle.com', ...]
    """
    print(f"  [Ocean.io] Finding companies similar to {seed_domain}...")

    url = "https://api.ocean.io/v3/search/companies"
    headers = {
        "X-Api-Token": OCEAN_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "companiesFilters": {
            "lookalikeDomains": [seed_domain]
        },
        "size": max_results
    }

    try:
        response = _post_request(url, payload, headers, timeout=15)
        response.raise_for_status()
        data = response.json()

        # Extract domains from response objects
        companies = data.get("companies", [])
        domains = []
        for c in companies:
            company = c.get("company") or {}
            domain = company.get("domain")
            if domain:
                domains.append(domain)

        print(f"  [Ocean.io] Found {len(domains)} lookalike companies.")
        return domains

    except requests.exceptions.HTTPError as e:
        print(f"  [Ocean.io] HTTP error: {e.response.status_code} — {e.response.text}")
        return []
    except requests.exceptions.Timeout:
        print(f"  [Ocean.io] Request timed out.")
        return []
    except Exception as e:
        print(f"  [Ocean.io] Unexpected error: {e}")
        return []