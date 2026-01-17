import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from ddgs import DDGS

# ============================
# CONFIG
# ============================
MAX_RESULTS = 5
SLEEP_SEARCH = 0.7
SLEEP_PAGE = 1

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

# ============================
# REGEX
# ============================
EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
)

LINKEDIN_REGEX = re.compile(r"https?://(www\.)?linkedin\.com/[^\s\"'>]+", re.I)
FACEBOOK_REGEX = re.compile(r"https?://(www\.)?facebook\.com/[^\s\"'>]+", re.I)

# ============================
# BLOCKED EMAIL CONTEXT
# ============================
BAD_CONTEXT = [
    "noreply",
    "no-reply",
    "donotreply",
    "do-not-reply",
    "example@",
    "test@",
    "sample@",
    "demo@",
    "fake@",
    ".png",
    ".jpg",
    ".jpeg",
    ".svg",
    ".webp"
]

# ============================
# EMAIL VALIDATION
# ============================
def is_valid_email(email: str) -> bool:
    email = email.lower().strip()

    if len(email) > 254:
        return False

    if any(bad in email for bad in BAD_CONTEXT):
        return False

    # remove fake patterns
    if re.search(r"(example|examp1e|esempio|esemp1o)", email):
        return False

    return True

# ============================
# DOMAIN FROM EMAIL
# ============================
def get_website_from_email(email: str) -> str:
    try:
        domain = email.split("@")[1]
        return f"https://{domain}"
    except Exception:
        return ""

# ============================
# EXTRACT SOCIAL LINKS
# ============================
def extract_social_links(html_text: str) -> dict:
    linkedin = None
    facebook = None

    linkedin_match = LINKEDIN_REGEX.search(html_text)
    facebook_match = FACEBOOK_REGEX.search(html_text)

    if linkedin_match:
        linkedin = linkedin_match.group(0)

    if facebook_match:
        facebook = facebook_match.group(0)

    return {
        "linkedin": linkedin,
        "facebook": facebook
    }

# ============================
# SCRAPE PAGE
# ============================
def scrape_page(url: str) -> dict:
    data = {
        "emails": set(),
        "linkedin": None,
        "facebook": None
    }

    try:
        resp = requests.get(
            url,
            headers=HEADERS,
            timeout=15,
            allow_redirects=True
        )

        if resp.status_code != 200:
            return data

        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text(" ", strip=True)

        # Emails
        for email in EMAIL_REGEX.findall(text):
            if is_valid_email(email):
                data["emails"].add(email.lower())

        # Social links
        socials = extract_social_links(resp.text)
        data["linkedin"] = socials["linkedin"]
        data["facebook"] = socials["facebook"]

    except Exception:
        pass

    return data

# ============================
# SEARCH + EXTRACT
# ============================
def search_and_extract_emails(keyword: str) -> list:
    """
    Returns:
    [
        {
            email,
            website,
            source_url,
            linkedin,
            facebook
        }
    ]
    """
    results = {}
    query = f"{keyword} contact email"

    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=MAX_RESULTS):
                url = r.get("href") or r.get("url")
                if not url:
                    continue

                page_data = scrape_page(url)

                # Try contact page
                if not page_data["emails"]:
                    contact_url = url.rstrip("/") + "/contact"
                    page_data = scrape_page(contact_url)

                for email in page_data["emails"]:
                    if email not in results:
                        results[email] = {
                            "email": email,
                            "website": get_website_from_email(email),
                            "source_url": url,
                            "linkedin": page_data["linkedin"],
                            "facebook": page_data["facebook"]
                        }

                time.sleep(SLEEP_PAGE)

    except Exception:
        pass

    time.sleep(SLEEP_SEARCH)
    return list(results.values())
