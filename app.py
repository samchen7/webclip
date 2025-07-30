import os
import sys
import time
import signal
import atexit
import threading
import queue
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

# 全局变量，用于清理临时文件
temp_files_to_cleanup = []

def cleanup_on_exit():
    """程序退出时清理临时文件"""
    for temp_file in temp_files_to_cleanup:
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
                print(f"清理临时文件: {temp_file}")
        except Exception as e:
            print(f"清理文件失败 {temp_file}: {e}")

def signal_handler(signum, frame):
    """处理Ctrl+C信号"""
    print("\n程序被中断，正在清理临时文件...")
    cleanup_on_exit()
    sys.exit(0)

# 注册清理函数
atexit.register(cleanup_on_exit)
signal.signal(signal.SIGINT, signal_handler)

def init_browser():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

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

def capture_full_page(driver, url, index, save_folder):
    try:
        # 清理URL（移除可能的引号）
        url = url.strip().strip('"').strip("'")
        
        # 自动补全协议
        if not url.startswith('http://') and not url.startswith('https://'):
            url = 'http://' + url
            
        print(f"正在访问: {url}")
        driver.get(url)
        time.sleep(3)
        
        # 获取页面标题
        page_title = driver.title
        safe_title = "".join(c for c in page_title if c.isalnum() or c.isspace())[:50]
        
        # 设置固定的浏览器窗口大小
        window_width = 1200
        window_height = 1200
        driver.set_window_size(window_width, window_height)
        
        # 获取页面实际高度，不再限制最大值
        total_height = driver.execute_script("return document.body.scrollHeight")
        print(f"页面总高度: {total_height}px, 窗口大小: {window_width}x{window_height}px")
        
        # 隐藏固定header和footer，只截取内容
        driver.execute_script("""
            // 隐藏固定定位的元素（通常是header和footer）
            var fixedElements = document.querySelectorAll('header, nav, .header, .nav, .fixed, .sticky, [style*="position: fixed"], [style*="position: sticky"], footer, .footer');
            for(var i = 0; i < fixedElements.length; i++) {
                fixedElements[i].style.display = 'none';
            }
        """)
        
        # 计算截图数量和预估时间
        scroll_step = 1000  # 使用1000px步长
        estimated_screenshots = (total_height + scroll_step - 1) // scroll_step  # 向上取整
        estimated_time_per_screenshot = 3  # 每张截图预估3秒（包括滚动和截图时间）
        total_estimated_time = estimated_screenshots * estimated_time_per_screenshot
        
        print(f"预估截图数量: {estimated_screenshots}张")
        print(f"预估总时间: {total_estimated_time}秒 ({total_estimated_time/60:.1f}分钟)")
        print(f"开始截取完整页面内容: (0-{total_height}px)")
        
        temp_screenshots = []
        screen_count = 0
        current_position = 0
        
        while current_position < total_height:
            driver.execute_script(f"window.scrollTo(0, {current_position})")
            time.sleep(2)
            
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
        
        # 拼接截图
        if len(temp_screenshots) > 1:
            print(f"开始拼接 {len(temp_screenshots)} 张截图...")
            final_image = stitch_screenshots(temp_screenshots, os.path.join(save_folder, f'final_screenshot_{index}.png'))
        else:
            final_image = temp_screenshots[0]
        
        # 提取文本内容
        print("正在提取页面文本...")
        direct_text = extract_text_from_page(driver)
        
        # OCR处理截图
        print("正在进行OCR识别...")
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
        
        # 可选：同时生成PDF（保持向后兼容）
        pdf_name = f'{timestamp}_{index}_{safe_title}.pdf'
        pdf_path = os.path.join(save_folder, pdf_name)
        convert_to_pdf([final_image], pdf_path)
        print(f"PDF文件已生成: {pdf_path}")
        
        # 清理分块文件
        cleanup_chunk_files(save_folder, index)
        
        return rtf_path, page_title
        
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
        return None, None

def stitch_screenshots(screenshot_files, output_path):
    """拼接多张截图，处理大图像限制"""
    images = []
    for file in screenshot_files:
        if os.path.exists(file):
            img = Image.open(file)
            images.append(img)
    
    if not images:
        return None
    
    # 计算总高度
    total_height = sum(img.height for img in images)
    max_width = max(img.width for img in images)
    
    print(f"图像拼接信息: 总高度={total_height}px, 最大宽度={max_width}px")
    
    # 检查图像尺寸是否超过PIL限制（65500像素）
    if total_height > 65000:  # 留一些安全边距
        print(f"⚠️  图像总高度({total_height}px)超过PIL限制，将分块处理")
        
        # 分块处理：每块最多60000像素高度
        chunk_height = 60000
        chunks = []
        current_chunk = []
        current_height = 0
        
        for img in images:
            if current_height + img.height > chunk_height:
                # 保存当前块
                if current_chunk:
                    chunks.append(current_chunk)
                # 开始新块
                current_chunk = [img]
                current_height = img.height
            else:
                current_chunk.append(img)
                current_height += img.height
        
        # 添加最后一个块
        if current_chunk:
            chunks.append(current_chunk)
        
        # 处理每个块
        chunk_files = []
        for i, chunk in enumerate(chunks):
            chunk_height = sum(img.height for img in chunk)
            chunk_width = max(img.width for img in chunk)
            
            # 创建块图像
            chunk_image = Image.new('RGB', (chunk_width, chunk_height))
            y_offset = 0
            for img in chunk:
                chunk_image.paste(img, (0, y_offset))
                y_offset += img.height
            
            # 保存块文件
            chunk_path = output_path.replace('.png', f'_chunk_{i}.png')
            chunk_image.save(chunk_path)
            chunk_files.append(chunk_path)
            print(f"已保存图像块 {i+1}: {chunk_path} ({chunk_width}x{chunk_height})")
        
        # 返回第一个块作为主要输出（用于PDF生成）
        return chunk_files[0] if chunk_files else None
    
    else:
        # 正常拼接
        print(f"正常拼接图像: {max_width}x{total_height}")
        stitched_image = Image.new('RGB', (max_width, total_height))
        
        # 拼接图像
        y_offset = 0
        for img in images:
            stitched_image.paste(img, (0, y_offset))
            y_offset += img.height
        
        stitched_image.save(output_path)
        return output_path

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
    """清理分块图像文件"""
    try:
        chunk_pattern = os.path.join(save_folder, f'final_screenshot_{index}_chunk_*.png')
        chunk_files = glob.glob(chunk_pattern)
        for chunk_file in chunk_files:
            try:
                if os.path.exists(chunk_file):
                    os.remove(chunk_file)
                    print(f"清理分块文件: {chunk_file}")
            except Exception as e:
                print(f"清理分块文件失败 {chunk_file}: {e}")
    except Exception as e:
        print(f"清理分块文件时出错: {e}")

def process_urls_parallel(urls):
    """并行处理多个URL"""
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
                result = future.result()
                if result:
                    results.append(result)
                    print(f"✅ {url} 处理完成")
                else:
                    print(f"❌ {url} 处理失败")
            except Exception as e:
                print(f"❌ {url} 处理出错: {e}")
    
    print(f"\n所有网页已保存为RTF: {len(results)} 个文件")
    return results

def process_single_url(url, index, save_folder):
    """处理单个URL"""
    print(f"\n处理URL {index}: {url}")
    
    driver = None
    try:
        driver = init_browser()
        rtf_path, title = capture_full_page(driver, url, index, save_folder)
        return rtf_path if rtf_path else None
    except Exception as e:
        print(f"处理URL时出错: {e}")
        return None
    finally:
        if driver:
            driver.quit()

def main():
    if len(sys.argv) < 2:
        print("使用方法: python app.py <url1> [<url2> ...]")
        print("示例: python app.py https://example.com https://google.com")
        sys.exit(1)
    
    urls = sys.argv[1:]
    print(f"准备处理 {len(urls)} 个URL...")
    
    try:
        results = process_urls_parallel(urls)
        print(f"\n处理完成！生成了 {len(results)} 个RTF文件")
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序出错: {e}")
    finally:
        cleanup_on_exit()

if __name__ == "__main__":
    main()

