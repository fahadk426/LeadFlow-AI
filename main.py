import sys
from ocean import get_lookalikes
from prospeo import get_contacts, resolve_emails
from brevo import send_emails

SENDER_EMAIL = "contact@devitech.me"  # your company email
SENDER_NAME = "Admin"

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py company.domain")
        print("Example: python main.py stripe.com")
        sys.exit(1)

    seed_domain = sys.argv[1].strip().lower()

    print(f"\n{'='*50}")
    print(f"  Starting pipeline for: {seed_domain}")
    print(f"{'='*50}\n")

    print("[Stage 1/4] Finding lookalike companies...")
    domains = get_lookalikes(seed_domain)
    if not domains:
        print("No lookalike companies found. Exiting.")
        sys.exit(1)

    print(f"\n[Stage 2/4] Finding decision-makers across {len(domains)} companies...")
    contacts = get_contacts(domains)
    if not contacts:
        print("No contacts found. Exiting.")
        sys.exit(1)

    print(f"\n[Stage 3/4] Resolving emails for {len(contacts)} contacts...")
    verified = resolve_emails(contacts)
    if not verified:
        print("No emails resolved. Exiting.")
        sys.exit(1)

    print(f"\n{'='*50}")
    print(f"  READY TO SEND — REVIEW BEFORE PROCEEDING")
    print(f"{'='*50}")
    print(f"  Seed domain    : {seed_domain}")
    print(f"  Companies found: {len(domains)}")
    print(f"  Contacts found : {len(contacts)}")
    print(f"  Verified emails: {len(verified)}")
    print(f"\n  Preview (first 5 recipients):")
    for c in verified[:5]:
        print(f"    → {c['name']} ({c['title']}) at {c['company']} — {c['email']}")
    if len(verified) > 5:
        print(f"    ... and {len(verified) - 5} more.")
    print()

    confirm = input("  Type YES to send all emails, anything else to abort: ")
    if confirm.strip().upper() != "YES":
        print("\n  Aborted. No emails were sent.")
        sys.exit(0)

    print(f"\n[Stage 4/4] Sending emails...")
    send_emails(verified, SENDER_EMAIL, SENDER_NAME)

    print(f"\n{'='*50}")
    print(f"  Pipeline complete.")
    print(f"{'='*50}\n")

if __name__ == "__main__":
    main()