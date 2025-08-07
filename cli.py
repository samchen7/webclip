#!/usr/bin/env python3
"""
WebClip CLI - 命令行接口
保留原有的命令行使用方式
"""

import argparse
import sys
import logging
from pathlib import Path

# 直接导入本地模块
from config import AppConfig
from logging_setup import setup_logging
from device import pick_device
from ocr import OCRProcessor
from text import fetch_html, extract_main_text
from classifier import ContentClassifier, ContentType
from browser import capture_full_page_screenshot
from files import FileManager

def main():
    parser = argparse.ArgumentParser(description="WebClip - 智能网页截图工具")
    parser.add_argument("output_dir", help="输出目录")
    parser.add_argument("url", help="要处理的URL")
    parser.add_argument("--gpu-mode", choices=["auto", "cuda", "mps", "cpu"], 
                       default="auto", help="GPU模式")
    parser.add_argument("--config", help="配置文件路径")
    parser.add_argument("--debug", action="store_true", help="调试模式")
    
    args = parser.parse_args()
    
    # 设置日志
    log_level = "DEBUG" if args.debug else "INFO"
    log = setup_logging(log_level)
    
    # 加载配置
    cfg = AppConfig()
    if args.config:
        # TODO: 从文件加载配置
        pass
    
    # 初始化组件
    fm = FileManager(args.output_dir)
    classifier = ContentClassifier(cfg.text_thresh)
    device = pick_device(args.gpu_mode)
    ocr = OCRProcessor(device=device, timeout_s=cfg.ocr.timeout_s)
    
    log.info(f"Processing URL: {args.url}")
    log.info(f"Device: {device}")
    log.info(f"Output directory: {args.output_dir}")
    
    # 处理URL
    try:
        ct = classifier.classify(args.url)
        artifacts = []
        strategy = ""

        if ct == ContentType.TEXT:
            html = fetch_html(args.url)
            title, text = extract_main_text(html)
            p = fm.save_text(args.url, title, text)
            artifacts.append(p)
            strategy = "TEXT->readability"
            log.info(f"Saved text to: {p}")
        elif ct == ContentType.IMAGES_ONLY:
            imgs = capture_full_page_screenshot(args.url, cfg.browser.mode.value, cfg.browser.page_timeout_s)
            if not imgs:
                log.warning("No images captured, browser mode may be disabled")
            artifacts.extend(fm.save_images(args.url, imgs))
            strategy = f"IMAGES_ONLY->{cfg.browser.mode.value or 'none'}"
        else:
            # PARTIAL: 取能拿到的结构化内容
            note = ""
            try:
                html = fetch_html(args.url)
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html, "lxml")
                title = soup.title.string if soup.title else (args.url or "Untitled")
                h1 = [h.get_text(strip=True) for h in soup.find_all("h1")]
                h2 = [h.get_text(strip=True) for h in soup.find_all("h2")]
                paras = [p.get_text(strip=True) for p in soup.find_all("p")]
            except Exception as e:
                title, h1, h2, paras = (args.url, [], [], [])
                note = f"Fetch error: {e}"
            p = fm.save_partial_docx(args.url, title, h1, h2, paras, note=note)
            artifacts.append(p)
            strategy = "PARTIAL->docx"
            log.info(f"Saved partial content to: {p}")

        log.info(f"Classification: {ct.name}")
        log.info(f"Strategy: {strategy}")
        log.info(f"Device: {device}")
        log.info(f"Artifacts: {artifacts}")
        
    except Exception as e:
        log.error(f"Processing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 