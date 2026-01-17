import re
import time
import requests
from bs4 import BeautifulSoup
from ddgs import DDGS

MAX_RESULTS = 5
SLEEP_PAGE = 1

HEADERS = {"User-Agent": "Mozilla/5.0"}

EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
)

BAD_EMAILS = [
    "noreply", "donotreply", "example@", "test@", ".png", ".jpg"
]

def is_valid_email(email):
    email = email.lower()
    return not any(bad in email for bad in BAD_EMAILS)

def extract_page(url):
    data = {
        "emails": set(),
        "linkedin": None,
        "facebook": None
    }

    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        if r.status_code != 200:
            return data

        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text(" ", strip=True)

        for e in EMAIL_REGEX.findall(text):
            if is_valid_email(e):
                data["emails"].add(e.lower())

        if "linkedin.com" in r.text:
            data["linkedin"] = "https://linkedin.com"
        if "facebook.com" in r.text:
            data["facebook"] = "https://facebook.com"

    except:
        pass

    return data

def search_and_extract_emails(keyword):
    results = {}
    query = f"{keyword} contact email"

    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=MAX_RESULTS):
            url = r.get("href") or r.get("url")
            if not url:
                continue

            data = extract_page(url)

            if not data["emails"]:
                data = extract_page(url.rstrip("/") + "/contact")

            for email in data["emails"]:
                results[email] = {
                    "email": email,
                    "website": f"https://{email.split('@')[1]}",
                    "source_url": url,
                    "linkedin": data["linkedin"],
                    "facebook": data["facebook"]
                }

            time.sleep(SLEEP_PAGE)

    return list(results.values())
