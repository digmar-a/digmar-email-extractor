import re
import time
import requests
from bs4 import BeautifulSoup
from ddgs import DDGS

MAX_RESULTS = 5
HEADERS = {"User-Agent": "Mozilla/5.0"}

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
LINKEDIN_REGEX = re.compile(r"https?://(www\.)?linkedin\.com/[^\s\"'>]+", re.I)
FACEBOOK_REGEX = re.compile(r"https?://(www\.)?facebook\.com/[^\s\"'>]+", re.I)

BAD_CONTEXT = [
    "noreply", "no-reply", "donotreply", "example@", "test@", "sample@",
    ".png", ".jpg", ".jpeg", ".svg"
]


def is_valid_email(email):
    email = email.lower()
    if any(bad in email for bad in BAD_CONTEXT):
        return False
    return True


def get_website_from_email(email):
    try:
        return f"https://{email.split('@')[1]}"
    except:
        return ""


def scrape_page(url):
    data = {"emails": set(), "linkedin": None, "facebook": None}

    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return data

        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text(" ", strip=True)

        for email in EMAIL_REGEX.findall(text):
            if is_valid_email(email):
                data["emails"].add(email)

        li = LINKEDIN_REGEX.search(r.text)
        fb = FACEBOOK_REGEX.search(r.text)

        if li:
            data["linkedin"] = li.group(0)
        if fb:
            data["facebook"] = fb.group(0)

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

            page = scrape_page(url)

            for email in page["emails"]:
                if email not in results:
                    results[email] = {
                        "email": email,
                        "website": get_website_from_email(email),
                        "source_url": url,
                        "linkedin": page["linkedin"],
                        "facebook": page["facebook"]
                    }

            time.sleep(1)

    return list(results.values())
