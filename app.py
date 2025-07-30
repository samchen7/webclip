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
            print(f"拼接完成: {temp_screenshots[0]}")
            final_image = stitch_screenshots(temp_screenshots, os.path.join(save_folder, f'final_screenshot_{index}.png'))
        else:
            final_image = temp_screenshots[0]
        
        # 转换为PDF
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        pdf_name = f'{timestamp}_{index}_{safe_title}.pdf'
        pdf_path = os.path.join(save_folder, pdf_name)
        
        convert_to_pdf([final_image], pdf_path)
        print(f"PDF已保存: {pdf_path}")
        
        return pdf_path, page_title
        
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
    """拼接多张截图"""
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
    
    # 创建新图像
    stitched_image = Image.new('RGB', (max_width, total_height))
    
    # 拼接图像
    y_offset = 0
    for img in images:
        stitched_image.paste(img, (0, y_offset))
        y_offset += img.height
    
    stitched_image.save(output_path)
    return output_path

def convert_to_pdf(screenshot_files, pdf_path):
    """将截图转换为PDF"""
    images = []
    for file in screenshot_files:
        if os.path.exists(file):
            img = Image.open(file)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            images.append(img)
    
    if images:
        images[0].save(pdf_path, 'PDF', save_all=True, append_images=images[1:])
        print(f"PDF文件已生成: {pdf_path}")

def cleanup_temp_files(files):
    """清理临时文件"""
    for file in files:
        try:
            if os.path.exists(file):
                os.remove(file)
        except Exception as e:
            print(f"清理文件失败 {file}: {e}")

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
    
    print(f"\n所有网页已保存为PDF: {len(results)} 个文件")
    return results

def process_single_url(url, index, save_folder):
    """处理单个URL"""
    print(f"\n处理URL {index}: {url}")
    
    driver = None
    try:
        driver = init_browser()
        pdf_path, title = capture_full_page(driver, url, index, save_folder)
        return pdf_path if pdf_path else None
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
        print(f"\n处理完成！生成了 {len(results)} 个PDF文件")
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序出错: {e}")
    finally:
        cleanup_on_exit()

if __name__ == "__main__":
    main()

