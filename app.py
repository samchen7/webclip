import os
import sys
import time
import signal
import atexit
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image
from datetime import datetime

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

def capture_full_page(driver, url, index, save_folder):
    try:
        # 自动补全协议
        if not url.startswith('http://') and not url.startswith('https://'):
            url = 'http://' + url
        driver.get(url)
        time.sleep(3)
        
        # 获取页面标题
        page_title = driver.title
        safe_title = "".join(c for c in page_title if c.isalnum() or c.isspace())[:50]
        
        # 设置固定的浏览器窗口大小
        window_width = 1200
        window_height = 1200
        driver.set_window_size(window_width, window_height)
        
        # 获取页面实际高度，并限制最大值
        total_height = driver.execute_script("return document.body.scrollHeight")
        if total_height > 10000:
            print(f"页面高度异常({total_height}px)，限制为10000px")
            total_height = 10000
        
        print(f"页面高度: {total_height}px, 窗口大小: {window_width}x{window_height}px")
        
        # 隐藏固定header和footer，只截取内容
        driver.execute_script("""
            // 隐藏固定定位的元素（通常是header和footer）
            var fixedElements = document.querySelectorAll('header, nav, .header, .nav, .fixed, .sticky, [style*="position: fixed"], [style*="position: sticky"], footer, .footer');
            for(var i = 0; i < fixedElements.length; i++) {
                fixedElements[i].style.display = 'none';
            }
        """)
        
        # 从0像素开始截图，覆盖整个页面
        scroll_step = 1000  # 使用1000px步长
        
        print(f"截取完整页面内容: (0-{total_height}px)")
        
        temp_screenshots = []
        screen_count = 0
        current_position = 0
        
        while current_position < total_height and screen_count < 15:  # 限制最多15张
            driver.execute_script(f"window.scrollTo(0, {current_position})")
            time.sleep(2)
            
            temp_file = os.path.join(save_folder, f"temp_{index}_{screen_count}_{current_position}.png")
            driver.save_screenshot(temp_file)
            temp_screenshots.append(temp_file)
            temp_files_to_cleanup.append(temp_file)
            screen_count += 1
            
            print(f"截图 {screen_count}: 位置 {current_position}/{total_height}px, 步长 {scroll_step}px")
            current_position += scroll_step
        
        # 拼接截图
        output_path = os.path.join(save_folder, f"screenshot_{index}.png")
        stitch_screenshots(temp_screenshots, output_path)
        cleanup_temp_files(temp_screenshots)
        return output_path, safe_title
        
    except Exception as e:
        print(f"截图失败 {url}: {e}")
        return None, None

def stitch_screenshots(screenshot_files, output_path):
    images = [Image.open(file) for file in screenshot_files]
    total_height = sum(img.height for img in images)
    max_width = max(img.width for img in images)
    
    stitched_image = Image.new("RGB", (max_width, total_height))
    current_y = 0
    
    for img in images:
        stitched_image.paste(img, (0, current_y))
        current_y += img.height
    
    stitched_image.save(output_path)
    print(f"拼接完成: {output_path}")

def convert_to_pdf(screenshot_files, pdf_path):
    images = [Image.open(file).convert("RGB") for file in screenshot_files]
    images[0].save(pdf_path, save_all=True, append_images=images[1:], optimize=True)
    print(f"PDF已保存: {pdf_path}")

def cleanup_temp_files(files):
    for file in files:
        try:
            if os.path.exists(file):
                os.remove(file)
                print(f"删除临时文件: {file}")
                if file in temp_files_to_cleanup:
                    temp_files_to_cleanup.remove(file)
        except Exception as e:
            print(f"删除临时文件失败 {file}: {e}")

def main():
    if len(sys.argv) < 2:
        print("用法: python app.py <url1> [<url2> ...]")
        sys.exit(1)
    
    urls = sys.argv[1:]
    save_folder = os.getcwd()
    driver = init_browser()
    screenshots = []
    page_titles = []
    
    try:
        for i, url in enumerate(urls, start=1):
            print(f"处理URL {i}: {url}")
            result = capture_full_page(driver, url, i, save_folder)
            if result[0]:
                screenshots.append(result[0])
                page_titles.append(result[1])
    finally:
        driver.quit()
    
    if screenshots:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        title = page_titles[0] if page_titles else "webpage"
        pdf_name = f'{timestamp}_{title}.pdf'
        pdf_path = os.path.join(save_folder, pdf_name)
        convert_to_pdf(screenshots, pdf_path)
        cleanup_temp_files(screenshots)
        print(f"所有网页已保存为PDF: {pdf_name}")
    else:
        print("没有成功截图，未生成PDF。")

if __name__ == "__main__":
    main()

