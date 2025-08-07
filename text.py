import requests
import logging
from bs4 import BeautifulSoup
from readability import Document

log = logging.getLogger(__name__)

def fetch_html(url: str, timeout: int = 10) -> str:
    r = requests.get(url, timeout=timeout, headers={"User-Agent":"Mozilla/5.0"})
    r.raise_for_status()
    return r.text

def extract_main_text(html: str) -> tuple[str, str]:
    doc = Document(html)
    title = doc.short_title() or ""
    summary_html = doc.summary()
    soup = BeautifulSoup(summary_html, "lxml")
    text = soup.get_text("\n", strip=True)
    return title, text 