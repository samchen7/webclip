from fastapi import FastAPI
from pydantic import BaseModel
import logging
from bs4 import BeautifulSoup

from config import AppConfig
from logging_setup import setup_logging
from device import pick_device
from ocr import OCRProcessor
from text import fetch_html, extract_main_text
from classifier import ContentClassifier, ContentType
from browser import capture_full_page_screenshot
from files import FileManager

log = setup_logging()
cfg = AppConfig()
fm = FileManager(cfg.storage_dir)
classifier = ContentClassifier(cfg.text_thresh)
device = pick_device(cfg.ocr.backend.value if hasattr(cfg.ocr, "backend") else str(cfg.ocr.backend))
ocr = OCRProcessor(device=device, timeout_s=cfg.ocr.timeout_s)

app = FastAPI(title="WebClip Cloud")

class ProcessRequest(BaseModel):
    url: str
    options: dict | None = None

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.post("/v1/process")
def process(req: ProcessRequest):
    url = req.url
    ct = classifier.classify(url)
    artifacts = []
    strategy = ""

    if ct == ContentType.TEXT:
        html = fetch_html(url)
        title, text = extract_main_text(html)
        p = fm.save_text(url, title, text)
        artifacts.append(p)
        strategy = "TEXT->readability"
    elif ct == ContentType.IMAGES_ONLY:
        imgs = capture_full_page_screenshot(url, cfg.browser.mode.value, cfg.browser.page_timeout_s)
        if not imgs:
            # 兜底：下载页面主图也可（此处简化为空）
            pass
        artifacts.extend(fm.save_images(url, imgs))
        strategy = f"IMAGES_ONLY->{cfg.browser.mode.value or 'none'}"
    else:
        # PARTIAL: 取能拿到的结构化内容
        note = ""
        try:
            html = fetch_html(url)
            soup = BeautifulSoup(html, "lxml")
            title = soup.title.string if soup.title else (url or "Untitled")
            h1 = [h.get_text(strip=True) for h in soup.find_all("h1")]
            h2 = [h.get_text(strip=True) for h in soup.find_all("h2")]
            paras = [p.get_text(strip=True) for p in soup.find_all("p")]
        except Exception as e:
            title, h1, h2, paras = (url, [], [], [])
            note = f"Fetch error: {e}"
        p = fm.save_partial_docx(url, title, h1, h2, paras, note=note)
        artifacts.append(p)
        strategy = "PARTIAL->docx"

    return {
        "classification": ct.name,
        "strategy": strategy,
        "device": device,
        "artifacts": artifacts
    } 