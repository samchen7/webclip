import logging
import time
from typing import List
import easyocr

log = logging.getLogger(__name__)

class OCRProcessor:
    def __init__(self, device: str, timeout_s: int = 20, langs=None):
        self.device = device  # "cuda" | "mps" | "cpu"
        self.timeout_s = timeout_s
        self.langs = langs or ["en","ch_sim"]
        use_gpu = (self.device == "cuda")  # EasyOCR 仅支持 CUDA
        self.reader = easyocr.Reader(self.langs, gpu=use_gpu)

    def read_batch(self, image_paths: List[str]) -> List[str]:
        out = []
        start = time.time()
        for p in image_paths:
            # 简单超时保护（粗粒度）
            if time.time() - start > self.timeout_s:
                log.warning("OCR timeout, stopping batch")
                break
            try:
                res = self.reader.readtext(p, detail=0, paragraph=True)
                out.append("\n".join(res))
            except Exception as e:
                log.warning(f"OCR failed for {p}: {e}")
        return out 