import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

def scrape_website(url: str, timeout: int = 15) -> dict:
    result = {
        "url": url,
        "scraped_at": datetime.now().isoformat(),
        "status": "ok",
        "title": "",
        "description": "",
        "headlines": [],
        "body_text": "",
        "internal_links": [],
        "error": None,
    }
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        result["title"] = soup.title.string.strip() if soup.title else ""
        meta_desc = soup.find("meta", attrs={"name": "description"})
        result["description"] = meta_desc.get("content", "") if meta_desc else ""

        for tag in soup.find_all(["h1", "h2", "h3"]):
            text = tag.get_text(strip=True)
            if text:
                result["headlines"].append(text)

        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        body = soup.get_text(separator=" ", strip=True)
        result["body_text"] = " ".join(body.split())[:3000]

        from urllib.parse import urljoin, urlparse
        base = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        seen = set()
        for a in soup.find_all("a", href=True):
            href = urljoin(base, a["href"])
            if href.startswith(base) and href not in seen:
                seen.add(href)
                result["internal_links"].append(href)
        result["internal_links"] = result["internal_links"][:20]

    except requests.exceptions.Timeout:
        result["status"] = "error"
        result["error"] = "Timeout al conectar con el sitio"
    except requests.exceptions.HTTPError as e:
        result["status"] = "error"
        result["error"] = f"HTTP {e.response.status_code}"
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result


def scrape_multiple(urls: list) -> list:
    results = []
    for url in urls:
        results.append(scrape_website(url))
        time.sleep(1)
    return results
