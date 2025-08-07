import logging
from typing import List

log = logging.getLogger(__name__)

def capture_full_page_screenshot(url: str, mode: str, timeout_s: int) -> List[str]:
    """
    mode: "playwright" | "selenium" | "disabled" | "light"
    Return list of image paths; if browser unavailable, return [].
    """
    try:
        if mode == "playwright":
            # 可实现：playwright 截图（首版可留 TODO）
            log.info("Playwright path TODO; returning [] for now")
            return []
        if mode == "selenium":
            # 可实现：selenium 截图（首版可留 TODO）
            log.info("Selenium path TODO; returning [] for now")
            return []
    except Exception as e:
        log.warning(f"Browser capture failed: {e}")
    return [] 