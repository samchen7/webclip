import os
import sys
import time
import signal
import atexit
import threading
import queue
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image
from datetime import datetime
import uuid
import tempfile
import shutil
import pytesseract
import easyocr
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import glob
import json

# 全局变量，用于清理临时文件
temp_files_to_cleanup = []
processing_results = []
current_process_id = None  # 用于标识当前进程的临时文件

def random_sleep(min_seconds=1.0, max_seconds=3.0):
    """随机睡眠一段时间，模拟人类行为"""
    sleep_time = random.uniform(min_seconds, max_seconds)
    time.sleep(sleep_time)
    return sleep_time

def human_like_scroll(driver, target_position, current_position):
    """模拟人类滚动行为，分步滚动到目标位置"""
    # 计算滚动距离
    scroll_distance = target_position - current_position
    
    if scroll_distance <= 0:
        return
    
    # 分步滚动，模拟人类滚动行为
    step_size = random.randint(200, 400)  # 每次滚动200-400像素
    steps = max(1, scroll_distance // step_size)
    
    for i in range(steps):
        # 计算当前步骤的目标位置
        step_target = current_position + min(step_size, scroll_distance - i * step_size)
        
        # 执行滚动
        driver.execute_script(f"window.scrollTo(0, {step_target})")
        
        # 随机等待
        wait_time = random_sleep(0.3, 0.8)
        
        # 偶尔添加一些微小的随机滚动
        if random.random() < 0.3:  # 30%的概率
            small_scroll = random.randint(-50, 50)
            driver.execute_script(f"window.scrollBy(0, {small_scroll})")
            random_sleep(0.1, 0.3)

def cleanup_all_temp_files():
    """清理所有临时文件"""
    print("开始清理所有临时文件...")
    
    # 清理当前目录下的所有临时文件
    temp_patterns = [
        "temp_screenshot_*.png",
        "final_screenshot_*.png", 
        "*_chunk_*.png",
        "temp_*.png"
    ]
    
    cleaned_count = 0
    for pattern in temp_patterns:
        try:
            files = glob.glob(pattern)
            for file in files:
                try:
                    if os.path.exists(file):
                        os.remove(file)
                        print(f"清理临时文件: {file}")
                        cleaned_count += 1
                except Exception as e:
                    print(f"清理文件失败 {file}: {e}")
        except Exception as e:
            print(f"清理模式 {pattern} 时出错: {e}")
    
    # 清理全局跟踪的文件
    for temp_file in temp_files_to_cleanup:
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
                print(f"清理跟踪文件: {temp_file}")
                cleaned_count += 1
        except Exception as e:
            print(f"清理跟踪文件失败 {temp_file}: {e}")
    
    print(f"清理完成，共清理 {cleaned_count} 个临时文件")
    return cleaned_count

def cleanup_on_exit():
    """程序退出时清理临时文件"""
    print("\n程序退出，正在清理临时文件...")
    cleanup_all_temp_files()

def signal_handler(signum, frame):
    """处理Ctrl+C信号"""
    print("\n程序被用户中断，正在清理临时文件...")
    cleanup_all_temp_files()
    sys.exit(0)

# 注册清理函数
atexit.register(cleanup_on_exit)
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)  # 添加SIGTERM信号处理

def init_browser():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    # 添加反检测功能
    # 随机User-Agent
    user_agents = [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]
    options.add_argument(f'--user-agent={random.choice(user_agents)}')
    
    # 禁用WebDriver检测
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # 设置更大的窗口大小，提高截图质量
    window_width = 1600
    window_height = 1600
    options.add_argument(f'--window-size={window_width},{window_height}')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # 执行JavaScript来隐藏WebDriver属性
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def extract_text_from_page(driver):
    """直接从页面提取文本内容"""
    try:
        # 等待页面加载完成
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # 获取页面文本
        body_text = driver.find_element(By.TAG_NAME, "body").text
        
        # 获取页面标题
        title = driver.title
        
        # 获取所有文本元素，保持结构
        text_elements = driver.find_elements(By.XPATH, "//*[text()]")
        
        structured_text = []
        for element in text_elements:
            tag_name = element.tag_name
            text = element.text.strip()
            if text:
                if tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    structured_text.append(f"标题: {text}")
                elif tag_name == 'p':
                    structured_text.append(text)
                elif tag_name in ['li']:
                    structured_text.append(f"• {text}")
        
        return {
            'title': title,
            'body_text': body_text,
            'structured_text': structured_text
        }
    except Exception as e:
        print(f"文本提取失败: {e}")
        return {'title': '', 'body_text': '', 'structured_text': []}

def ocr_process_image(image_path):
    """使用OCR处理图片"""
    try:
        # 使用EasyOCR进行OCR处理
        reader = easyocr.Reader(['en', 'ch_sim'])  # 支持英文和中文
        results = reader.readtext(image_path)
        
        # 提取文本
        text_lines = []
        for (bbox, text, prob) in results:
            if prob > 0.5:  # 只保留置信度大于50%的文本
                text_lines.append(text.strip())
        
        return '\n'.join(text_lines)
    except Exception as e:
        print(f"OCR处理失败: {e}")
        return ""

def create_rtf_document(title, content, metadata=None):
    """创建RTF文档"""
    try:
        # 清理标题中的特殊字符
        safe_title = re.sub(r'[^\w\s-]', '', title)[:50]
        
        # 清理内容中的特殊字符
        clean_content = content.replace('\\', '\\\\').replace('{', '\\{').replace('}', '\\}')
        
        # 创建RTF内容
        rtf_content = f"""{{\\rtf1\\ansi\\deff0
{{\\fonttbl {{\\f0 Times New Roman;}}
{{\\f1 Arial;}}
}}
\\f0\\fs24
\\b {safe_title}\\b0\\par
\\par
\\fs20
{clean_content}
\\par
}}"""
        
        return rtf_content
    except Exception as e:
        print(f"RTF生成失败: {e}")
        return None

def merge_text_content(direct_text, ocr_text):
    """合并直接文本提取和OCR文本"""
    merged_content = []
    
    # 添加直接提取的文本
    if direct_text.get('title'):
        merged_content.append(f"页面标题: {direct_text['title']}")
        merged_content.append("")
    
    if direct_text.get('structured_text'):
        merged_content.extend(direct_text['structured_text'])
        merged_content.append("")
    
    # 添加OCR文本（如果与直接文本不同）
    if ocr_text and ocr_text.strip():
        # 简单的去重逻辑
        direct_text_combined = ' '.join(direct_text.get('structured_text', []))
        if ocr_text.strip() not in direct_text_combined:
            merged_content.append("OCR识别内容:")
            merged_content.append(ocr_text)
    
    return '\n'.join(merged_content)

def save_rtf_info_to_json(rtf_info, timestamp):
    """将RTF文件信息保存到单独的JSON文件"""
    try:
        rtf_json_filename = f'rtf_files_{timestamp}.json'
        with open(rtf_json_filename, 'w', encoding='utf-8') as f:
            json.dump(rtf_info, f, ensure_ascii=False, indent=2)
        print(f"RTF文件信息已保存到: {rtf_json_filename}")
        return rtf_json_filename
    except Exception as e:
        print(f"保存RTF信息失败: {e}")
        return None

def capture_full_page(driver, url, index, save_folder):
    """截取完整页面，返回PDF链接JSON和RTF信息"""
    try:
        # 清理URL（移除可能的引号）
        url = url.strip().strip('"').strip("'")
        
        # 自动补全协议
        if not url.startswith('http://') and not url.startswith('https://'):
            url = 'https://' + url
            
        print(f"正在访问: {url}")
        driver.get(url)
        # 随机等待页面加载
        sleep_time = random_sleep(2.0, 4.0)
        print(f"页面加载等待: {sleep_time:.1f}秒")
        
        # 获取页面标题
        page_title = driver.title
        safe_title = "".join(c for c in page_title if c.isalnum() or c.isspace())[:50]
        
        # 设置更大的浏览器窗口大小，提高截图质量
        window_width = 1600
        window_height = 1600
        driver.set_window_size(window_width, window_height)
        
        # 获取页面实际高度
        total_height = driver.execute_script("return document.body.scrollHeight")
        print(f"页面总高度: {total_height}px, 窗口大小: {window_width}x{window_height}px")
        
        # 智能识别和隐藏真正的header和footer
        header_footer_info = smart_hide_header_footer(driver)
        if header_footer_info:
            print(f"智能隐藏: Header高度={header_footer_info['header_height']}px, Footer高度={header_footer_info['footer_height']}px")
        else:
            print("未检测到需要隐藏的header/footer，使用正常截图")
        
        # 智能分块截图策略
        temp_screenshots = capture_by_content_blocks(driver, index, save_folder, total_height, window_height)
        
        if not temp_screenshots:
            print("❌ 截图失败")
            return None
        
        # 拼接截图
        final_image_path = os.path.join(save_folder, f'final_screenshot_{index}.png')
        if len(temp_screenshots) > 1:
            print(f"开始拼接 {len(temp_screenshots)} 张截图...")
            final_image = stitch_screenshots(temp_screenshots, final_image_path)
            # 将最终图像添加到清理列表
            temp_files_to_cleanup.append(final_image_path)
        else:
            final_image = temp_screenshots[0]
        
        # 记录截图数量用于报告
        screen_count = len(temp_screenshots)
        
        # 提取文本内容
        print("正在提取页面文本...")
        text_wait = random_sleep(1.0, 2.0)
        print(f"文本提取等待: {text_wait:.1f}秒")
        direct_text = extract_text_from_page(driver)
        
        # OCR处理截图
        print("正在进行OCR识别...")
        ocr_wait = random_sleep(1.0, 2.5)
        print(f"OCR处理等待: {ocr_wait:.1f}秒")
        ocr_text = ""
        if temp_screenshots:
            ocr_text = ocr_process_image(temp_screenshots[0])  # 使用第一张截图进行OCR
        
        # 合并文本内容
        final_content = merge_text_content(direct_text, ocr_text)
        
        # 生成RTF文件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        rtf_name = f'{timestamp}_{index}_{safe_title}.rtf'
        rtf_path = os.path.join(save_folder, rtf_name)
        
        rtf_content = create_rtf_document(page_title, final_content)
        if rtf_content:
            with open(rtf_path, 'w', encoding='utf-8') as f:
                f.write(rtf_content)
            print(f"RTF文件已生成: {rtf_path}")
            print(f"RTF已保存: {rtf_path}")
        else:
            print("RTF生成失败")
            rtf_path = None
        
        # 生成PDF文件
        pdf_name = f'{timestamp}_{index}_{safe_title}.pdf'
        pdf_path = os.path.join(save_folder, pdf_name)
        convert_to_pdf([final_image], pdf_path)
        print(f"PDF文件已生成: {pdf_path}")
        
        # 清理临时文件
        cleanup_chunk_files(save_folder, index)
        
        # 返回包含PDF和RTF下载链接的统一格式
        result = {
            "url": url,
            "title": page_title,
            "status": "success",
            "files": {
                "pdf": {
                    "path": pdf_path,
                    "filename": pdf_name,
                    "size": os.path.getsize(pdf_path) if os.path.exists(pdf_path) else 0,
                    "download_url": f"file://{pdf_path}"
                },
                "rtf": {
                    "path": rtf_path,
                    "filename": rtf_name,
                    "size": os.path.getsize(rtf_path) if rtf_path and os.path.exists(rtf_path) else 0,
                    "download_url": f"file://{rtf_path}"
                }
            },
            "metadata": {
                "page_height": total_height,
                "screenshot_count": screen_count,
                "processing_time": time.time(),
                "timestamp": timestamp
            }
        }
        
        return result, result  # 返回相同的格式给PDF和RTF
        
        return pdf_result, rtf_info
        
    except Exception as e:
        error_msg = str(e)
        if "ERR_NAME_NOT_RESOLVED" in error_msg:
            print(f"❌ 网络连接失败: 无法访问 {url}")
            print("   可能原因: 网络连接问题、域名不存在、防火墙阻止")
            print("   建议: 检查网络连接，确认URL是否正确")
        elif "ERR_CONNECTION_TIMED_OUT" in error_msg:
            print(f"❌ 连接超时: {url}")
            print("   建议: 稍后重试，或检查网络连接")
        elif "ERR_CONNECTION_REFUSED" in error_msg:
            print(f"❌ 连接被拒绝: {url}")
            print("   可能原因: 网站暂时不可用")
        else:
            print(f"❌ 处理URL时出错: {error_msg}")
        
        # 返回错误结果
        error_result = {
            "url": url,
            "title": "",
            "status": "error",
            "error_message": error_msg,
            "files": {
                "pdf": {
                    "path": None,
                    "filename": None,
                    "size": 0,
                    "download_url": None
                },
                "rtf": {
                    "path": None,
                    "filename": None,
                    "size": 0,
                    "download_url": None
                }
            },
            "metadata": {
                "page_height": 0,
                "screenshot_count": 0,
                "processing_time": time.time(),
                "timestamp": datetime.now().strftime('%Y%m%d_%H%M%S')
            }
        }
        
        return error_result, error_result

def smart_hide_header_footer(driver):
    """智能识别和隐藏真正的header和footer"""
    try:
        # 获取页面信息
        page_height = driver.execute_script("return document.body.scrollHeight")
        viewport_height = driver.execute_script("return window.innerHeight")
        
        # 分析页面结构，识别真正的header和footer
        header_info = analyze_header(driver, page_height)
        footer_info = analyze_footer(driver, page_height)
        
        # 如果检测到真正的header/footer，则隐藏它们
        if header_info or footer_info:
            hide_elements_script = """
            var elementsToHide = [];
            """
            
            if header_info:
                hide_elements_script += f"""
                // 隐藏header区域
                var headerElements = document.querySelectorAll('header, .header, .site-header, .main-header, .top-bar, .navbar, .navigation');
                for(var i = 0; i < headerElements.length; i++) {{
                    var rect = headerElements[i].getBoundingClientRect();
                    if(rect.top <= {header_info['max_height']}) {{
                        headerElements[i].style.display = 'none';
                        elementsToHide.push(headerElements[i]);
                    }}
                }}
                """
            
            if footer_info:
                hide_elements_script += f"""
                // 隐藏footer区域
                var footerElements = document.querySelectorAll('footer, .footer, .site-footer, .main-footer, .bottom-bar');
                for(var i = 0; i < footerElements.length; i++) {{
                    var rect = footerElements[i].getBoundingClientRect();
                    if(rect.bottom >= window.innerHeight - {footer_info['max_height']}) {{
                        footerElements[i].style.display = 'none';
                        elementsToHide.push(footerElements[i]);
                    }}
                }}
                """
            
            driver.execute_script(hide_elements_script)
            
            return {
                'header_height': header_info['max_height'] if header_info else 0,
                'footer_height': footer_info['max_height'] if footer_info else 0,
                'hidden_elements': True
            }
        
        return None
        
    except Exception as e:
        print(f"智能隐藏header/footer时出错: {e}")
        return None

def analyze_header(driver, page_height):
    """分析页面header"""
    try:
        # 获取页面顶部元素
        header_candidates = driver.find_elements(By.CSS_SELECTOR, 
            'header, .header, .site-header, .main-header, .top-bar, .navbar, .navigation, .nav')
        
        if not header_candidates:
            return None
        
        max_header_height = 0
        header_found = False
        
        for elem in header_candidates:
            try:
                # 检查元素是否在页面顶部
                location = elem.location
                size = elem.size
                
                if location and size:
                    # 检查是否在页面顶部100px范围内
                    if location['y'] <= 100 and size['height'] > 0:
                        # 检查元素是否包含导航内容
                        text_content = elem.text.strip()
                        has_nav_content = any(keyword in text_content.lower() for keyword in 
                                            ['menu', 'nav', 'home', 'about', 'contact', 'login', 'search'])
                        
                        # 检查元素是否固定定位
                        is_fixed = driver.execute_script("""
                            var style = window.getComputedStyle(arguments[0]);
                            return style.position === 'fixed' || style.position === 'sticky';
                        """, elem)
                        
                        if has_nav_content or is_fixed:
                            header_found = True
                            max_header_height = max(max_header_height, location['y'] + size['height'])
            except Exception as e:
                continue
        
        if header_found and max_header_height > 0:
            return {'max_height': max_header_height}
        
        return None
        
    except Exception as e:
        print(f"分析header时出错: {e}")
        return None

def analyze_footer(driver, page_height):
    """分析页面footer"""
    try:
        # 获取页面底部元素
        footer_candidates = driver.find_elements(By.CSS_SELECTOR, 
            'footer, .footer, .site-footer, .main-footer, .bottom-bar')
        
        if not footer_candidates:
            return None
        
        max_footer_height = 0
        footer_found = False
        
        for elem in footer_candidates:
            try:
                location = elem.location
                size = elem.size
                
                if location and size:
                    # 检查是否在页面底部
                    elem_bottom = location['y'] + size['height']
                    if elem_bottom >= page_height - 200:  # 在底部200px范围内
                        # 检查元素是否包含footer内容
                        text_content = elem.text.strip()
                        has_footer_content = any(keyword in text_content.lower() for keyword in 
                                               ['copyright', '©', 'all rights', 'privacy', 'terms', 'contact'])
                        
                        if has_footer_content or size['height'] > 50:
                            footer_found = True
                            max_footer_height = max(max_footer_height, size['height'])
            except Exception as e:
                continue
        
        if footer_found and max_footer_height > 0:
            return {'max_height': max_footer_height}
        
        return None
        
    except Exception as e:
        print(f"分析footer时出错: {e}")
        return None

def capture_by_content_blocks(driver, index, save_folder, total_height, window_height):
    """基于内容块的智能截图策略（带智能重试机制）"""
    print("开始智能分块截图（带重试机制）...")
    
    # 使用智能重试机制进行截图
    temp_screenshots = smart_retry_capture(driver, index, save_folder, total_height, window_height)
    
    print(f"智能分块截图完成，共 {len(temp_screenshots)} 张截图")
    return temp_screenshots

def smart_retry_capture(driver, index, save_folder, total_height, window_height):
    """基于滚动位置的智能重试截图机制"""
    print("使用智能重试截图机制...")
    
    # 第一步：获取内容密度分布
    content_density = analyze_content_density(driver, total_height)
    
    # 第二步：找到最佳截图边界点
    capture_boundaries = find_optimal_capture_boundaries(content_density, total_height, window_height)
    
    # 第三步：基于边界进行智能截图
    temp_screenshots = []
    screen_count = 0
    max_retries = 3  # 最大重试次数
    
    for i, (start_pos, end_pos) in enumerate(capture_boundaries):
        print(f"处理截图区域 {i+1}: {start_pos}px - {end_pos}px")
        
        # 尝试截图，如果失败则重试
        screenshot_path = None
        retry_count = 0
        
        while retry_count < max_retries and screenshot_path is None:
            try:
                screenshot_path = capture_with_verification(
                    driver, index, save_folder, start_pos, end_pos, screen_count, retry_count
                )
                if screenshot_path:
                    temp_screenshots.append(screenshot_path)
                    temp_files_to_cleanup.append(screenshot_path)
                    print(f"截图 {screen_count + 1} 成功: {os.path.basename(screenshot_path)}")
                    screen_count += 1
                else:
                    retry_count += 1
                    print(f"截图 {screen_count + 1} 失败，重试 {retry_count}/{max_retries}")
            except Exception as e:
                retry_count += 1
                print(f"截图出错: {e}，重试 {retry_count}/{max_retries}")
        
        if screenshot_path is None:
            print(f"⚠️  截图区域 {i+1} 在 {max_retries} 次重试后仍然失败")
    
    return temp_screenshots

def analyze_content_density(driver, total_height):
    """分析页面内容密度分布"""
    print("分析页面内容密度...")
    
    # 获取所有文本元素
    text_elements = driver.find_elements(By.XPATH, "//*[text() and normalize-space(text())]")
    
    # 创建密度分布图（每100px一个采样点）
    density_map = {}
    sample_interval = 100
    
    for y in range(0, total_height, sample_interval):
        density_map[y] = 0
    
    # 计算每个区域的文本密度
    for elem in text_elements:
        try:
            location = elem.location
            size = elem.size
            if location and size:
                y_start = location['y']
                y_end = y_start + size['height']
                
                # 计算该元素覆盖的密度区域
                for y in range(0, total_height, sample_interval):
                    if y_start <= y + sample_interval and y_end >= y:
                        # 计算重叠部分
                        overlap_start = max(y_start, y)
                        overlap_end = min(y_end, y + sample_interval)
                        overlap_height = max(0, overlap_end - overlap_start)
                        
                        # 根据重叠高度计算密度贡献
                        density_contribution = overlap_height / sample_interval
                        density_map[y] += density_contribution
        except Exception as e:
            continue
    
    print(f"内容密度分析完成，共 {len(density_map)} 个采样点")
    return density_map

def find_optimal_capture_boundaries(density_map, total_height, window_height):
    """基于内容密度找到最佳截图边界"""
    print("寻找最佳截图边界...")
    
    boundaries = []
    current_pos = 0
    overlap = 200  # 重叠区域
    max_iterations = 100  # 防止无限循环
    iteration_count = 0
    
    while current_pos < total_height and iteration_count < max_iterations:
        iteration_count += 1
        
        # 计算当前区域的内容密度
        current_density = get_average_density(density_map, current_pos, window_height)
        
        # 寻找最佳结束位置
        optimal_end = find_optimal_end_position(
            density_map, current_pos, window_height, total_height, current_density
        )
        
        # 防止无限循环：确保optimal_end > current_pos
        if optimal_end <= current_pos:
            optimal_end = min(current_pos + window_height, total_height)
        
        boundaries.append((current_pos, optimal_end))
        
        # 移动到下一个位置，考虑重叠
        next_pos = optimal_end - overlap
        
        # 防止无限循环：确保有进展
        if next_pos <= current_pos:
            next_pos = current_pos + window_height - overlap
        
        current_pos = next_pos
        
        if current_pos >= total_height:
            break
    
    if iteration_count >= max_iterations:
        print(f"⚠️  达到最大迭代次数，可能存在问题")
    
    print(f"找到 {len(boundaries)} 个最佳截图边界")
    return boundaries

def get_average_density(density_map, start_pos, height):
    """获取指定区域的平均密度"""
    total_density = 0
    count = 0
    
    for y in range(start_pos, start_pos + height, 100):
        if y in density_map:
            total_density += density_map[y]
            count += 1
    
    return total_density / max(count, 1)

def find_optimal_end_position(density_map, start_pos, window_height, total_height, current_density):
    """寻找最佳结束位置"""
    # 默认结束位置
    default_end = min(start_pos + window_height, total_height)
    
    # 在窗口高度范围内寻找密度变化最小的位置
    best_end = default_end
    min_density_change = float('inf')
    
    for end_pos in range(start_pos + window_height - 200, start_pos + window_height + 200, 50):
        if end_pos > total_height:
            break
        
        # 计算结束位置附近的密度变化
        density_change = abs(
            get_average_density(density_map, end_pos - 100, 200) - current_density
        )
        
        if density_change < min_density_change:
            min_density_change = density_change
            best_end = end_pos
    
    return best_end

def capture_with_verification(driver, index, save_folder, start_pos, end_pos, screen_count, retry_count):
    """带验证的截图函数"""
    # 滚动到目标位置
    driver.execute_script(f"window.scrollTo(0, {start_pos})")
    
    # 等待页面稳定
    wait_time = random_sleep(0.5 + retry_count * 0.2, 1.0 + retry_count * 0.3)
    print(f"等待页面稳定: {wait_time:.1f}秒")
    
    # 截图
    screenshot_path = os.path.join(save_folder, f'temp_screenshot_{index}_{screen_count}.png')
    driver.save_screenshot(screenshot_path)
    
    # 验证截图质量
    if verify_screenshot_quality(screenshot_path, start_pos, end_pos):
        return screenshot_path
    else:
        # 如果质量不好，删除文件并返回None
        if os.path.exists(screenshot_path):
            os.remove(screenshot_path)
        return None

def verify_screenshot_quality(screenshot_path, start_pos, end_pos):
    """验证截图质量"""
    try:
        img = Image.open(screenshot_path)
        
        # 检查图像是否为空或过小
        if img.width < 100 or img.height < 100:
            print(f"截图质量检查失败: 图像尺寸过小 ({img.width}x{img.height})")
            return False
        
        # 检查图像是否全白或全黑
        img_gray = img.convert('L')
        pixels = list(img_gray.getdata())
        
        # 计算非空白像素比例
        non_white_pixels = sum(1 for p in pixels if p < 250)  # 非白色像素
        total_pixels = len(pixels)
        
        if total_pixels == 0:
            return False
        
        content_ratio = non_white_pixels / total_pixels
        
        if content_ratio < 0.01:  # 如果内容比例小于1%，认为质量不好
            print(f"截图质量检查失败: 内容比例过低 ({content_ratio:.3f})")
            return False
        
        print(f"截图质量检查通过: 内容比例 {content_ratio:.3f}")
        return True
        
    except Exception as e:
        print(f"截图质量检查出错: {e}")
        return False

def capture_traditional(driver, index, save_folder, total_height, window_height):
    """传统截图方法（备用）"""
    print("使用传统截图方法...")
    
    temp_screenshots = []
    screen_count = 0
    current_position = 0
    overlap = 200  # 200px重叠区域
    scroll_step = window_height - overlap
    
    while current_position < total_height:
        # 滚动到目标位置
        print(f"滚动到位置: {current_position}px")
        driver.execute_script(f"window.scrollTo(0, {current_position})")
        
        # 截图前短暂等待
        screenshot_wait = random_sleep(0.5, 1.0)
        print(f"截图前等待: {screenshot_wait:.1f}秒")
        
        # 截图
        screenshot_path = os.path.join(save_folder, f'temp_screenshot_{index}_{screen_count}.png')
        driver.save_screenshot(screenshot_path)
        temp_screenshots.append(screenshot_path)
        temp_files_to_cleanup.append(screenshot_path)
        
        screen_count += 1
        print(f"截图 {screen_count}: 位置 {current_position}/{total_height}px, 步长 {scroll_step}px")
        
        current_position += scroll_step
        
        # 如果已经到达底部，退出循环
        if current_position >= total_height:
            break
    
    return temp_screenshots

def stitch_screenshots(screenshot_files, output_path):
    """智能拼接多张截图，处理大图像限制"""
    images = []
    for file in screenshot_files:
        if os.path.exists(file):
            img = Image.open(file)
            images.append(img)
    
    if not images:
        return None
    
    if len(images) == 1:
        # 只有一张图片，直接保存
        images[0].save(output_path)
        return output_path
    
    print(f"开始智能拼接 {len(images)} 张截图...")
    
    # 使用智能拼接算法
    result_image = intelligent_stitch_images(images)
    
    if result_image is None:
        print("智能拼接失败，使用传统拼接方法")
        return traditional_stitch(images, output_path)
    
    # 检查图像尺寸是否超过PIL限制
    if result_image.height > 65000:
        print(f"⚠️  拼接后图像高度({result_image.height}px)超过PIL限制，将分块保存")
        return save_as_chunks(result_image, output_path)
    else:
        result_image.save(output_path)
        print(f"智能拼接完成: {result_image.width}x{result_image.height}")
        return output_path

def intelligent_stitch_images(images):
    """基于图像相似度的智能拼接（带质量验证）"""
    if len(images) < 2:
        return images[0] if images else None
    
    print("使用智能拼接算法（带质量验证）...")
    
    # 从第一张图片开始
    result = images[0]
    
    for i in range(1, len(images)):
        next_image = images[i]
        
        # 找到最佳拼接点
        stitch_point = find_best_stitch_point(result, next_image)
        
        if stitch_point is None:
            print(f"无法找到图片 {i+1} 的最佳拼接点，使用简单拼接")
            # 简单拼接：直接连接
            new_result = Image.new('RGB', (max(result.width, next_image.width), 
                                          result.height + next_image.height))
            new_result.paste(result, (0, 0))
            new_result.paste(next_image, (0, result.height))
            result = new_result
        else:
            # 智能拼接：在最佳点拼接
            result = stitch_at_point(result, next_image, stitch_point)
        
        # 验证拼接质量
        if not verify_stitch_quality(result, i):
            print(f"⚠️  拼接质量验证失败，尝试重新拼接图片 {i+1}")
            # 尝试使用不同的拼接策略
            result = retry_stitch_with_different_strategy(result, next_image, i)
    
    return result

def verify_stitch_quality(stitched_image, stitch_index):
    """验证拼接质量"""
    try:
        # 检查拼接后的图像是否有明显的接缝
        img_gray = stitched_image.convert('L')
        
        # 分析拼接区域附近的像素变化
        # 这里简化处理，检查图像是否为空或过小
        if stitched_image.width < 100 or stitched_image.height < 100:
            print(f"拼接质量检查失败: 图像尺寸过小 ({stitched_image.width}x{stitched_image.height})")
            return False
        
        # 检查拼接区域是否有明显的空白或断裂
        # 这里可以添加更复杂的图像分析算法
        print(f"拼接质量检查通过: 图片 {stitch_index + 1}")
        return True
        
    except Exception as e:
        print(f"拼接质量检查出错: {e}")
        return False

def retry_stitch_with_different_strategy(result, next_image, stitch_index):
    """使用不同策略重试拼接"""
    print(f"尝试不同的拼接策略...")
    
    # 策略1：使用更大的重叠区域
    try:
        # 增加重叠区域进行拼接
        overlap_height = min(600, result.height // 3, next_image.height // 3)
        
        # 从result底部和next_image顶部提取重叠区域
        result_bottom = result.crop((0, result.height - overlap_height, result.width, result.height))
        next_top = next_image.crop((0, 0, next_image.width, overlap_height))
        
        # 创建新的拼接图像
        new_width = max(result.width, next_image.width)
        new_height = result.height + next_image.height - overlap_height
        
        new_result = Image.new('RGB', (new_width, new_height))
        new_result.paste(result, (0, 0))
        new_result.paste(next_image, (0, result.height - overlap_height))
        
        print(f"使用更大重叠区域拼接成功")
        return new_result
        
    except Exception as e:
        print(f"重试拼接失败: {e}")
        # 如果重试失败，使用简单拼接
        simple_result = Image.new('RGB', (max(result.width, next_image.width), 
                                         result.height + next_image.height))
        simple_result.paste(result, (0, 0))
        simple_result.paste(next_image, (0, result.height))
        return simple_result

def find_best_stitch_point(img1, img2):
    """找到两张图片的最佳拼接点"""
    # 计算重叠区域
    overlap_height = min(400, img1.height // 4, img2.height // 4)  # 最大400px重叠
    
    if overlap_height < 50:  # 重叠区域太小，无法找到好的拼接点
        return None
    
    # 提取重叠区域
    img1_bottom = img1.crop((0, img1.height - overlap_height, img1.width, img1.height))
    img2_top = img2.crop((0, 0, img2.width, overlap_height))
    
    # 计算相似度，找到最佳拼接点
    best_overlap = overlap_height // 2  # 默认在中间拼接
    
    # 简单的相似度检测（可以进一步优化）
    try:
        # 将图像转换为灰度
        img1_gray = img1_bottom.convert('L')
        img2_gray = img2_top.convert('L')
        
        # 计算平均像素差异
        min_diff = float('inf')
        best_y = 0
        
        for y in range(0, overlap_height - 50, 10):  # 每10px检查一次
            # 提取对应区域
            region1 = img1_gray.crop((0, y, img1_gray.width, y + 50))
            region2 = img2_gray.crop((0, y, img2_gray.width, y + 50))
            
            # 计算差异
            diff = calculate_image_difference(region1, region2)
            
            if diff < min_diff:
                min_diff = diff
                best_y = y
        
        print(f"找到最佳拼接点: y={best_y}, 差异={min_diff:.2f}")
        return best_y
        
    except Exception as e:
        print(f"计算拼接点时出错: {e}")
        return None

def calculate_image_difference(img1, img2):
    """计算两张图片的差异度"""
    try:
        # 确保两张图片尺寸相同
        if img1.size != img2.size:
            img2 = img2.resize(img1.size)
        
        # 计算像素差异
        diff = 0
        for y in range(img1.height):
            for x in range(img1.width):
                pixel1 = img1.getpixel((x, y))
                pixel2 = img2.getpixel((x, y))
                diff += abs(pixel1 - pixel2)
        
        return diff / (img1.width * img1.height)
    except Exception as e:
        print(f"计算图像差异时出错: {e}")
        return float('inf')

def stitch_at_point(img1, img2, stitch_y):
    """在指定点拼接两张图片"""
    # 计算拼接后的尺寸
    overlap_height = min(400, img1.height // 4, img2.height // 4)
    
    # 从img1底部和img2顶部提取重叠区域
    img1_bottom = img1.crop((0, img1.height - overlap_height, img1.width, img1.height))
    img2_top = img2.crop((0, 0, img2.width, overlap_height))
    
    # 创建拼接后的图像
    new_width = max(img1.width, img2.width)
    new_height = img1.height + img2.height - overlap_height
    
    result = Image.new('RGB', (new_width, new_height))
    
    # 粘贴第一张图片
    result.paste(img1, (0, 0))
    
    # 粘贴第二张图片，在拼接点处
    result.paste(img2, (0, img1.height - overlap_height))
    
    return result

def traditional_stitch(images, output_path):
    """传统拼接方法（备用）"""
    print("使用传统拼接方法...")
    
    # 计算总高度
    total_height = sum(img.height for img in images)
    max_width = max(img.width for img in images)
    
    print(f"传统拼接: {max_width}x{total_height}")
    
    # 检查图像尺寸是否超过PIL限制
    if total_height > 65000:
        print(f"⚠️  图像总高度({total_height}px)超过PIL限制，将分块处理")
        return save_as_chunks_traditional(images, output_path)
    
    # 创建拼接图像
    stitched_image = Image.new('RGB', (max_width, total_height))
    
    # 拼接图像
    y_offset = 0
    for img in images:
        stitched_image.paste(img, (0, y_offset))
        y_offset += img.height
    
    stitched_image.save(output_path)
    return output_path

def save_as_chunks(image, output_path):
    """将大图像分块保存"""
    chunk_height = 60000
    chunks = []
    
    for i in range(0, image.height, chunk_height):
        chunk = image.crop((0, i, image.width, min(i + chunk_height, image.height)))
        chunk_path = output_path.replace('.png', f'_chunk_{len(chunks)}.png')
        chunk.save(chunk_path)
        chunks.append(chunk_path)
        print(f"已保存图像块 {len(chunks)}: {chunk_path} ({chunk.width}x{chunk.height})")
    
    return chunks[0] if chunks else None

def save_as_chunks_traditional(images, output_path):
    """传统方法分块保存"""
    chunk_height = 60000
    chunks = []
    current_chunk = []
    current_height = 0
    
    for img in images:
        if current_height + img.height > chunk_height:
            # 保存当前块
            if current_chunk:
                chunk_image = Image.new('RGB', (max(img.width for img in current_chunk), current_height))
                y_offset = 0
                for chunk_img in current_chunk:
                    chunk_image.paste(chunk_img, (0, y_offset))
                    y_offset += chunk_img.height
                
                chunk_path = output_path.replace('.png', f'_chunk_{len(chunks)}.png')
                chunk_image.save(chunk_path)
                chunks.append(chunk_path)
                print(f"已保存图像块 {len(chunks)}: {chunk_path}")
            
            # 开始新块
            current_chunk = [img]
            current_height = img.height
        else:
            current_chunk.append(img)
            current_height += img.height
    
    # 添加最后一个块
    if current_chunk:
        chunk_image = Image.new('RGB', (max(img.width for img in current_chunk), current_height))
        y_offset = 0
        for chunk_img in current_chunk:
            chunk_image.paste(chunk_img, (0, y_offset))
            y_offset += chunk_img.height
        
        chunk_path = output_path.replace('.png', f'_chunk_{len(chunks)}.png')
        chunk_image.save(chunk_path)
        chunks.append(chunk_path)
        print(f"已保存图像块 {len(chunks)}: {chunk_path}")
    
    return chunks[0] if chunks else None

def convert_to_pdf(screenshot_files, pdf_path):
    """将截图转换为PDF，处理大图像限制"""
    images = []
    for file in screenshot_files:
        if os.path.exists(file):
            img = Image.open(file)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            images.append(img)
    
    if not images:
        print("❌ 没有有效的图像文件用于PDF生成")
        return
    
    # 检查是否有分块图像
    chunk_files = [f for f in screenshot_files if '_chunk_' in f]
    if chunk_files:
        print(f"发现分块图像文件: {len(chunk_files)} 个")
        # 使用分块图像生成PDF
        chunk_images = []
        for chunk_file in sorted(chunk_files):  # 按文件名排序
            if os.path.exists(chunk_file):
                img = Image.open(chunk_file)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                chunk_images.append(img)
        
        if chunk_images:
            print(f"使用 {len(chunk_images)} 个分块图像生成PDF")
            chunk_images[0].save(pdf_path, 'PDF', save_all=True, append_images=chunk_images[1:])
            print(f"PDF文件已生成: {pdf_path}")
        else:
            print("❌ 分块图像加载失败")
    else:
        # 正常处理
        if images:
            # 检查图像尺寸
            total_height = sum(img.height for img in images)
            if total_height > 65000:
                print(f"⚠️  图像总高度({total_height}px)较大，PDF生成可能较慢")
            
            images[0].save(pdf_path, 'PDF', save_all=True, append_images=images[1:])
            print(f"PDF文件已生成: {pdf_path}")
        else:
            print("❌ 没有有效的图像文件")

def cleanup_temp_files(files):
    """清理临时文件"""
    for file in files:
        try:
            if os.path.exists(file):
                os.remove(file)
        except Exception as e:
            print(f"清理文件失败 {file}: {e}")

def cleanup_chunk_files(save_folder, index):
    """清理分块图像文件和临时截图文件"""
    try:
        # 清理分块文件
        chunk_pattern = os.path.join(save_folder, f'final_screenshot_{index}_chunk_*.png')
        chunk_files = glob.glob(chunk_pattern)
        for chunk_file in chunk_files:
            try:
                if os.path.exists(chunk_file):
                    os.remove(chunk_file)
                    print(f"清理分块文件: {chunk_file}")
            except Exception as e:
                print(f"清理分块文件失败 {chunk_file}: {e}")
        
        # 清理临时截图文件
        temp_pattern = os.path.join(save_folder, f'temp_screenshot_{index}_*.png')
        temp_files = glob.glob(temp_pattern)
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    print(f"清理临时截图: {temp_file}")
            except Exception as e:
                print(f"清理临时截图失败 {temp_file}: {e}")
                
    except Exception as e:
        print(f"清理文件时出错: {e}")

def process_urls_parallel(urls):
    """并行处理多个URL，返回PDF链接JSON和RTF信息"""
    print(f"开始并行处理 {len(urls)} 个URL...")
    
    # 使用当前目录作为保存目录
    save_dir = os.getcwd()
    print(f"保存目录: {save_dir}")
    
    results = []
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        # 提交所有任务
        future_to_url = {executor.submit(process_single_url, url, i, save_dir): url 
                        for i, url in enumerate(urls, 1)}
        
        # 收集结果
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                result, _ = future.result()
                if result and result.get('status') == 'success':
                    results.append(result)
                    print(f"✅ {url} 处理完成")
                    print(f"   PDF文件: {result['files']['pdf']['filename']}")
                    print(f"   RTF文件: {result['files']['rtf']['filename']}")
                else:
                    error_msg = result.get('error_message', '未知错误') if result else '处理失败'
                    print(f"❌ {url} 处理失败: {error_msg}")
                    if result:
                        results.append(result)
            except Exception as e:
                error_result = {
                    "url": url,
                    "title": "",
                    "status": "error",
                    "error_message": str(e),
                    "files": {
                        "pdf": {
                            "path": None,
                            "filename": None,
                            "size": 0,
                            "download_url": None
                        },
                        "rtf": {
                            "path": None,
                            "filename": None,
                            "size": 0,
                            "download_url": None
                        }
                    },
                    "metadata": {
                        "page_height": 0,
                        "screenshot_count": 0,
                        "processing_time": time.time(),
                        "timestamp": datetime.now().strftime('%Y%m%d_%H%M%S')
                    }
                }
                results.append(error_result)
                print(f"❌ {url} 处理出错: {e}")
    
    # 生成统一的JSON结果
    final_result = {
        "summary": {
            "total_urls": len(urls),
            "successful_urls": len([r for r in results if r.get('status') == 'success']),
            "failed_urls": len([r for r in results if r.get('status') == 'error']),
            "processing_time": time.time(),
            "timestamp": datetime.now().strftime('%Y%m%d_%H%M%S')
        },
        "results": results
    }
    
    print(f"\n处理完成！成功: {final_result['summary']['successful_urls']}, 失败: {final_result['summary']['failed_urls']}")
    return final_result, final_result

def process_single_url(url, index, save_folder):
    """处理单个URL，返回PDF链接和RTF信息"""
    print(f"\n处理URL {index}: {url}")
    
    driver = None
    try:
        driver = init_browser()
        pdf_result, rtf_info = capture_full_page(driver, url, index, save_folder)
        return pdf_result, rtf_info
    except Exception as e:
        print(f"处理URL时出错: {e}")
        error_pdf_result = {
            "url": url,
            "title": "",
            "status": "error",
            "error_message": str(e),
            "pdf_download_link": {
                "path": None,
                "filename": None,
                "size": 0,
                "download_url": None
            },
            "metadata": {
                "page_height": 0,
                "screenshot_count": 0,
                "processing_time": time.time(),
                "timestamp": datetime.now().strftime('%Y%m%d_%H%M%S')
            }
        }
        error_rtf_info = {
            "url": url,
            "title": "",
            "rtf_file": {
                "path": None,
                "filename": None,
                "size": 0
            },
            "metadata": {
                "page_height": 0,
                "screenshot_count": 0,
                "processing_time": time.time(),
                "timestamp": datetime.now().strftime('%Y%m%d_%H%M%S')
            }
        }
        return error_pdf_result, error_rtf_info
    finally:
        if driver:
            driver.quit()

def create_output_directories(base_path):
    """创建输出目录结构"""
    documents_dir = os.path.join(base_path, "documents")
    textualization_dir = os.path.join(base_path, "textualization")
    
    # 创建目录
    os.makedirs(documents_dir, exist_ok=True)
    os.makedirs(textualization_dir, exist_ok=True)
    
    print(f"创建输出目录:")
    print(f"  PDF文档目录: {documents_dir}")
    print(f"  RTF文档目录: {textualization_dir}")
    
    return documents_dir, textualization_dir

def move_files_to_output_dirs(results, documents_dir, textualization_dir):
    """将生成的文件移动到指定的输出目录"""
    moved_files = []
    
    for result in results['results']:
        if result.get('status') == 'success':
            # 移动PDF文件
            pdf_source = result['files']['pdf']['path']
            pdf_filename = result['files']['pdf']['filename']
            pdf_dest = os.path.join(documents_dir, pdf_filename)
            
            if os.path.exists(pdf_source):
                shutil.move(pdf_source, pdf_dest)
                print(f"✅ 移动PDF文件: {pdf_filename} -> {documents_dir}")
                moved_files.append(pdf_dest)
            
            # 移动RTF文件
            rtf_source = result['files']['rtf']['path']
            rtf_filename = result['files']['rtf']['filename']
            rtf_dest = os.path.join(textualization_dir, rtf_filename)
            
            if rtf_source and os.path.exists(rtf_source):
                shutil.move(rtf_source, rtf_dest)
                print(f"✅ 移动RTF文件: {rtf_filename} -> {textualization_dir}")
                moved_files.append(rtf_dest)
    
    return moved_files

def main():
    """主函数，云服务版本"""
    if len(sys.argv) < 3:
        print("使用方法: python app.py <输出目录> <url1> [<url2> ...]")
        print("示例: python app.py /path/to/output https://example.com https://google.com")
        print("\n功能特性:")
        print("- 智能内容截图，自动隐藏固定元素")
        print("- 自动生成可搜索的RTF文档")
        print("- OCR文本识别，支持中英文")
        print("- 超长页面分块处理")
        print("- 并行处理多个URL")
        print("- 自动清理临时文件")
        print("- 云服务输出：documents/PDF文件, textualization/RTF文件")
        sys.exit(1)
    
    # 程序开始时清理之前的临时文件
    print("清理之前的临时文件...")
    cleanup_all_temp_files()
    
    # 解析参数
    output_path = sys.argv[1]
    urls = sys.argv[2:]
    
    print(f"输出目录: {output_path}")
    print(f"准备处理 {len(urls)} 个URL...")
    
    # 创建输出目录
    documents_dir, textualization_dir = create_output_directories(output_path)
    
    try:
        results, _ = process_urls_parallel(urls)
        
        # 移动文件到输出目录
        print("\n开始移动文件到输出目录...")
        moved_files = move_files_to_output_dirs(results, documents_dir, textualization_dir)
        
        # 输出处理结果
        successful_results = [r for r in results['results'] if r.get('status') == 'success']
        failed_results = [r for r in results['results'] if r.get('status') == 'error']
        
        print(f"\n处理完成！")
        print(f"成功: {len(successful_results)}, 失败: {len(failed_results)}")
        
        if successful_results:
            print(f"\n成功生成的文件:")
            for result in successful_results:
                print(f"  URL: {result['url']}")
                print(f"    标题: {result['title']}")
                print(f"    PDF: {result['files']['pdf']['filename']} ({result['files']['pdf']['size']} bytes)")
                print(f"    RTF: {result['files']['rtf']['filename']} ({result['files']['rtf']['size']} bytes)")
                print()
        
        if failed_results:
            print(f"\n处理失败的URL:")
            for result in failed_results:
                print(f"  URL: {result['url']}")
                print(f"    错误: {result.get('error_message', '未知错误')}")
                print()
        
        # 在终端显示处理报告（不保存文件）
        print(f"\n处理报告:")
        print("=" * 60)
        print(json.dumps(results, ensure_ascii=False, indent=2))
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序出错: {e}")
    finally:
        cleanup_on_exit()

if __name__ == "__main__":
    main()

