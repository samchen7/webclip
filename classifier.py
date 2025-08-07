from enum import Enum, auto
from bs4 import BeautifulSoup
import requests
import logging

log = logging.getLogger(__name__)

class ContentType(Enum):
    TEXT = auto()
    IMAGES_ONLY = auto()
    PARTIAL = auto()

class ContentClassifier:
    def __init__(self, text_thresh: int = 1000, timeout: int = 6):
        self.text_thresh = text_thresh
        self.timeout = timeout

    def classify(self, url: str) -> ContentType:
        try:
            head = requests.head(url, timeout=self.timeout, allow_redirects=True)
            ctype = (head.headers.get("Content-Type") or "").lower()
            if "image/" in ctype:
                return ContentType.IMAGES_ONLY
        except Exception:
            pass
        try:
            resp = requests.get(url, timeout=self.timeout, headers={"User-Agent":"Mozilla/5.0"})
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")
            paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")]
            total_chars = sum(len(t) for t in paragraphs)
            imgs = soup.find_all("img")
            if total_chars >= self.text_thresh:
                return ContentType.TEXT
            if imgs and total_chars < max(50, self.text_thresh // 5):
                return ContentType.IMAGES_ONLY
            return ContentType.PARTIAL
        except Exception as e:
            log.warning(f"classify fallback to PARTIAL due to error: {e}")
            return ContentType.PARTIAL 