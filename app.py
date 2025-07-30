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
from flask import Flask, request, render_template_string, send_file, jsonify, redirect, url_for
import uuid
import tempfile
import shutil

# 全局变量，用于清理临时文件
temp_files_to_cleanup = []
app = Flask(__name__)

# 存储任务状态
tasks = {}

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

def process_urls_parallel(urls, task_id):
    """并行处理多个URL"""
    save_folder = tempfile.mkdtemp()
    results = []
    
    # 更新任务状态
    tasks[task_id] = {
        'status': 'processing',
        'progress': 0,
        'total_urls': len(urls),
        'processed': 0,
        'results': [],
        'error': None
    }
    
    try:
        # 从任务ID中提取用户ID
        user_id = task_id.split('_')[0] if '_' in task_id else 'anonymous'
        
        # 使用线程池并行处理URL
        with ThreadPoolExecutor(max_workers=min(3, len(urls))) as executor:
            # 提交所有任务
            future_to_url = {
                executor.submit(process_single_url_with_pdf, url, i, save_folder, user_id): (url, i) 
                for i, url in enumerate(urls, 1)
            }
            
            # 收集结果
            for future in as_completed(future_to_url):
                url, index = future_to_url[future]
                try:
                    result = future.result()
                    if result and result['success']:
                        results.append(result)
                        tasks[task_id]['results'].append(result)
                    
                    # 更新进度
                    tasks[task_id]['processed'] += 1
                    tasks[task_id]['progress'] = (tasks[task_id]['processed'] / len(urls)) * 100
                    
                except Exception as e:
                    print(f"处理URL失败 {url}: {e}")
                    tasks[task_id]['error'] = f"处理URL失败: {url} - {str(e)}"
        
        # 更新任务状态
        if results:
            tasks[task_id]['status'] = 'completed'
            tasks[task_id]['progress'] = 100
            print(f"处理完成，共生成 {len(results)} 个PDF文件")
        else:
            tasks[task_id]['status'] = 'failed'
            tasks[task_id]['error'] = "没有成功截图，未生成PDF"
            print("没有成功截图，未生成PDF。")
            
    except Exception as e:
        tasks[task_id]['status'] = 'failed'
        tasks[task_id]['error'] = str(e)
        print(f"处理失败: {e}")

def process_single_url_with_pdf(url, index, save_folder, user_id):
    """处理单个URL并生成PDF"""
    driver = init_browser()
    try:
        print(f"处理URL {index}: {url}")
        result = capture_full_page(driver, url, index, save_folder)
        
        if result and result[0]:
            screenshot_path, page_title = result
            
            # 为每个页面生成单独的PDF，包含用户ID
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_title = "".join(c for c in page_title if c.isalnum() or c.isspace())[:50]
            pdf_name = f'{timestamp}_{user_id}_{index}_{safe_title}.pdf'
            pdf_path = os.path.join(save_folder, pdf_name)
            
            # 生成PDF
            convert_to_pdf([screenshot_path], pdf_path)
            cleanup_temp_files([screenshot_path])
            
            return {
                'success': True,
                'url': url,
                'title': page_title,
                'pdf_path': pdf_path,
                'pdf_name': pdf_name,
                'index': index,
                'user_id': user_id,
                'download_url': f'/download/{user_id}_{timestamp}_{index}'
            }
        else:
            return {
                'success': False,
                'url': url,
                'error': '截图失败',
                'index': index,
                'user_id': user_id
            }
            
    except Exception as e:
        return {
            'success': False,
            'url': url,
            'error': str(e),
            'index': index,
            'user_id': user_id
        }
    finally:
        driver.quit()

def process_single_url(url, index, save_folder):
    """处理单个URL"""
    driver = init_browser()
    try:
        print(f"处理URL {index}: {url}")
        return capture_full_page(driver, url, index, save_folder)
    finally:
        driver.quit()

# Flask路由
@app.route('/')
def index():
    """主页"""
    html_template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>网页截图工具</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .form-group { margin-bottom: 15px; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input[type="text"], textarea { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
            textarea { height: 100px; resize: vertical; }
            button { background-color: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background-color: #0056b3; }
            .status { margin-top: 20px; padding: 10px; border-radius: 4px; }
            .processing { background-color: #fff3cd; border: 1px solid #ffeaa7; }
            .completed { background-color: #d4edda; border: 1px solid #c3e6cb; }
            .failed { background-color: #f8d7da; border: 1px solid #f5c6cb; }
            .progress-bar { width: 100%; height: 20px; background-color: #f0f0f0; border-radius: 10px; overflow: hidden; }
            .progress-fill { height: 100%; background-color: #007bff; transition: width 0.3s; }
        </style>
    </head>
    <body>
        <h1>网页截图工具</h1>
        <p>输入要截图的网页URL，每行一个URL：</p>
        
        <form id="screenshotForm">
            <div class="form-group">
                <label for="urls">网页URL（每行一个）：</label>
                <textarea id="urls" name="urls" placeholder="https://example.com&#10;https://google.com&#10;https://github.com" required></textarea>
            </div>
            <button type="submit">开始截图</button>
        </form>
        
        <div id="status" style="display: none;">
            <h3>处理状态</h3>
            <div id="statusContent"></div>
            <div class="progress-bar">
                <div id="progressFill" class="progress-fill" style="width: 0%;"></div>
            </div>
            <div id="downloadLinks" style="display: none; margin-top: 20px;">
                <h4>下载链接</h4>
                <div id="downloadList"></div>
            </div>
        </div>
        
        <script>
            document.getElementById('screenshotForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const urls = document.getElementById('urls').value.split('\\n').filter(url => url.trim());
                if (urls.length === 0) {
                    alert('请输入至少一个URL');
                    return;
                }
                
                // 显示状态区域
                document.getElementById('status').style.display = 'block';
                document.getElementById('statusContent').innerHTML = '<div class="status processing">正在提交任务...</div>';
                
                try {
                    const response = await fetch('/submit', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ urls: urls })
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        const taskId = result.task_id;
                        pollStatus(taskId);
                    } else {
                        document.getElementById('statusContent').innerHTML = '<div class="status failed">提交失败: ' + result.error + '</div>';
                    }
                } catch (error) {
                    document.getElementById('statusContent').innerHTML = '<div class="status failed">提交失败: ' + error.message + '</div>';
                }
            });
            
            async function pollStatus(taskId) {
                try {
                    const response = await fetch('/status/' + taskId);
                    const status = await response.json();
                    
                    let statusHtml = '';
                    let progress = 0;
                    
                    if (status.status === 'processing') {
                        statusHtml = '<div class="status processing">正在处理中... (' + status.processed + '/' + status.total_urls + ' URL)</div>';
                        progress = status.progress || 0;
                    } else if (status.status === 'completed') {
                        statusHtml = '<div class="status completed">处理完成！共生成 ' + (status.results ? status.results.length : 0) + ' 个PDF文件</div>';
                        progress = 100;
                        document.getElementById('downloadLinks').style.display = 'block';
                        
                        // 生成下载链接
                        let downloadHtml = '';
                        if (status.results && status.results.length > 0) {
                            status.results.forEach(function(result, index) {
                                downloadHtml += '<div style="margin-bottom: 15px; padding: 10px; border: 1px solid #ddd; border-radius: 4px;">';
                                downloadHtml += '<div style="font-weight: bold; margin-bottom: 5px;">' + (result.title || '页面 ' + result.index) + '</div>';
                                downloadHtml += '<div style="color: #666; font-size: 12px; margin-bottom: 8px;">' + result.url + '</div>';
                                downloadHtml += '<a href="/download/' + taskId + '/' + result.index + '" class="btn btn-success" style="background-color: #28a745; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; display: inline-block;">下载PDF</a>';
                                downloadHtml += '</div>';
                            });
                        }
                        document.getElementById('downloadList').innerHTML = downloadHtml;
                    } else if (status.status === 'failed') {
                        statusHtml = '<div class="status failed">处理失败: ' + (status.error || '未知错误') + '</div>';
                    }
                    
                    document.getElementById('statusContent').innerHTML = statusHtml;
                    document.getElementById('progressFill').style.width = progress + '%';
                    
                    if (status.status === 'processing') {
                        setTimeout(() => pollStatus(taskId), 2000);
                    }
                } catch (error) {
                    document.getElementById('statusContent').innerHTML = '<div class="status failed">状态查询失败: ' + error.message + '</div>';
                }
            }
        </script>
    </body>
    </html>
    '''
    return render_template_string(html_template)

@app.route('/submit', methods=['POST'])
def submit_task():
    """提交截图任务（Web界面）"""
    try:
        data = request.get_json()
        urls = data.get('urls', [])
        
        if not urls:
            return jsonify({'success': False, 'error': '没有提供URL'})
        
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 启动后台处理
        thread = threading.Thread(target=process_urls_parallel, args=(urls, task_id))
        thread.daemon = True
        thread.start()
        
        return jsonify({'success': True, 'task_id': task_id})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/submit', methods=['POST'])
def api_submit_task():
    """API端点：提交截图任务（支持多用户）"""
    try:
        data = request.get_json()
        urls = data.get('urls', [])
        user_id = data.get('user_id', 'anonymous')  # 用户ID，可选
        
        if not urls:
            return jsonify({'success': False, 'error': '没有提供URL'})
        
        # 生成任务ID（包含用户ID信息）
        task_id = f"{user_id}_{str(uuid.uuid4())}"
        
        # 启动后台处理
        thread = threading.Thread(target=process_urls_parallel, args=(urls, task_id))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True, 
            'task_id': task_id,
            'user_id': user_id,
            'urls_count': len(urls),
            'message': f'任务已提交，任务ID: {task_id}'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/status/<task_id>')
def api_get_status(task_id):
    """API端点：获取任务状态"""
    if task_id not in tasks:
        return jsonify({'error': '任务不存在'})
    
    task = tasks[task_id]
    
    # 构建详细的URL状态信息
    url_status = []
    if task.get('results'):
        for result in task['results']:
            url_info = {
                'url': result['url'],
                'index': result['index'],
                'status': 'completed' if result['success'] else 'failed',
                'title': result.get('title', ''),
                'pdf_name': result.get('pdf_name', ''),
                'download_url': result.get('download_url', ''),
                'error': result.get('error', None)
            }
            url_status.append(url_info)
    
    return jsonify({
        'task_id': task_id,
        'status': task['status'],
        'progress': task.get('progress', 0),
        'processed': task.get('processed', 0),
        'total_urls': task.get('total_urls', 0),
        'results': task.get('results', []),
        'url_status': url_status,  # 新增：详细的URL状态
        'error': task.get('error', None)
    })

@app.route('/status/<task_id>')
def get_status(task_id):
    """获取任务状态"""
    if task_id not in tasks:
        return jsonify({'error': '任务不存在'})
    
    return jsonify(tasks[task_id])

@app.route('/download/<task_id>')
@app.route('/download/<task_id>/<int:result_index>')
@app.route('/download/<user_id>/<timestamp>/<int:result_index>')
def download_pdf(task_id, result_index=None, user_id=None, timestamp=None):
    """下载PDF文件"""
    
    # 处理新的下载链接格式：/download/user_id/timestamp/index
    if user_id and timestamp and result_index is not None:
        # 查找对应的任务
        target_task = None
        for task_id_key, task in tasks.items():
            if task_id_key.startswith(f"{user_id}_") and task.get('results'):
                for result in task['results']:
                    if (result.get('user_id') == user_id and 
                        result.get('index') == result_index and 
                        result.get('success')):
                        return send_file(result['pdf_path'], as_attachment=True, download_name=result['pdf_name'])
        
        return "PDF文件不存在", 404
    
    # 处理原有的下载链接格式
    if task_id not in tasks:
        return "任务不存在", 404
    
    task = tasks[task_id]
    if task['status'] != 'completed':
        return "PDF未准备好", 404
    
    try:
        if result_index is not None:
            # 下载特定的PDF文件
            if not task['results'] or result_index >= len(task['results']):
                return "PDF文件不存在", 404
            
            result = task['results'][result_index]
            if not result['success']:
                return "PDF文件处理失败", 404
            
            return send_file(result['pdf_path'], as_attachment=True, download_name=result['pdf_name'])
        else:
            # 下载所有PDF的压缩包（如果需要的话）
            return "请选择具体的PDF文件下载", 400
            
    except Exception as e:
        return f"下载失败: {str(e)}", 500

def main():
    if len(sys.argv) < 2:
        print("启动Web服务器...")
        print("访问 http://localhost:5001 使用Web界面")
        print("或者使用命令行: python app.py <url1> [<url2> ...]")
        app.run(host='0.0.0.0', port=5001, debug=False)
        return
    
    # 命令行模式
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

