import os
import time
from flask import Flask, request, render_template, jsonify, Response, send_file
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image
from datetime import datetime
import csv

app = Flask(__name__)
CORS(app)

# 文件保存路径（存储在临时目录，避免权限问题）
save_folder = '/tmp/Web_Saver_Output'
if not os.path.exists(save_folder):
    os.makedirs(save_folder)

# 更新进度状态
progress = {"total": 0, "current": 0}

# 路由：主页
@app.route('/')
def index():
    return render_template("index.html")

# 路由：进度推送
@app.route('/progress')
def progress_stream():
    def generate():
        while progress["current"] < progress["total"]:
            time.sleep(0.5)
            yield f'data: {{"current": {progress["current"]}, "total": {progress["total"]}, "percentage": {int((progress["current"]/progress["total"])*100)}}}\n\n'
        yield 'data: {"current": 100, "total": 100, "percentage": 100}\n\n'
    return Response(generate(), mimetype='text/event-stream')

# 路由：文件上传处理
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'File type not supported. Please upload a CSV file.'}), 400

    # 保存文件
    file_path = os.path.join(save_folder, file.filename)
    file.save(file_path)
    print(f"File uploaded successfully: {file_path}")

    # 处理文件
    output_filename = process_urls_from_csv(file_path)
    return jsonify({'success': f'File processed successfully.', 
                    'download_url': f'/download/{output_filename}'}), 200

# 路由：文件下载
@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(save_folder, filename)
    try:
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return jsonify({'error': f'File not found: {str(e)}'}), 404

# 使用 Selenium 抓取网页并生成 PDF
def process_urls_from_csv(csv_path):
    output_pdf = 'processed_output.pdf'
    pdf_path = os.path.join(save_folder, output_pdf)
    driver = init_browser()

    try:
        with open(csv_path, mode="r") as file:
            reader = csv.reader(file)
            urls = [row[0].strip() for row in reader if row and row[0].strip()]

        update_progress(0, len(urls))

        screenshots = []
        for i, url in enumerate(urls, start=1):
            print(f"Processing URL {i}: {url}")
            screenshot = capture_full_page(driver, url, i)
            if screenshot:
                screenshots.append(screenshot)
            update_progress(i, len(urls))

        if screenshots:
            stitch_and_convert_to_pdf(screenshots, pdf_path)
            cleanup_temp_files(screenshots)

        return output_pdf
    except Exception as e:
        print(f"Error processing URLs: {e}")
        return None
    finally:
        driver.quit()

# 初始化浏览器
def init_browser():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# 截取网页全页面
def capture_full_page(driver, url, index):
    try:
        driver.get(url)
        time.sleep(3)

        # 动态获取高度并截屏
        total_height = driver.execute_script("return document.body.scrollHeight")
        viewport_height = driver.execute_script("return window.innerHeight")

        temp_screenshots = []
        for y in range(0, total_height, viewport_height):
            driver.execute_script(f"window.scrollTo(0, {y});")
            time.sleep(1)
            temp_file = os.path.join(save_folder, f"temp_{index}_{y}.png")
            driver.save_screenshot(temp_file)
            temp_screenshots.append(temp_file)

        # 拼接完整截图
        output_path = os.path.join(save_folder, f"screenshot_{index}.png")
        stitch_screenshots(temp_screenshots, output_path)
        cleanup_temp_files(temp_screenshots)

        return output_path
    except Exception as e:
        print(f"Error capturing URL {url}: {e}")
        return None

# 拼接截图
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
    print(f"Stitched image saved: {output_path}")

# 转换 PNG 文件列表为 PDF
def stitch_and_convert_to_pdf(screenshot_files, pdf_path):
    images = [Image.open(file).convert("RGB") for file in screenshot_files]
    images[0].save(pdf_path, save_all=True, append_images=images[1:], optimize=True)
    print(f"PDF saved at {pdf_path}")

    # 压缩 PDF 文件大小
    if os.path.getsize(pdf_path) > 5 * 1024 * 1024:
        resize_and_compress_pdf(pdf_path)

# 压缩 PDF
def resize_and_compress_pdf(pdf_path):
    compressed_pdf_path = pdf_path.replace(".pdf", "_compressed.pdf")
    try:
        with Image.open(pdf_path) as img:
            img.save(compressed_pdf_path, "PDF", quality=50, optimize=True)
        os.replace(compressed_pdf_path, pdf_path)
        print(f"PDF compressed to under 5MB: {pdf_path}")
    except Exception as e:
        print(f"Error compressing PDF: {e}")

# 清理临时文件
def cleanup_temp_files(files):
    for file in files:
        os.remove(file)
        print(f"Deleted temporary file: {file}")

# 更新进度
def update_progress(current, total):
    global progress
    progress["current"] = current
    progress["total"] = total

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # 使用 Azure 提供的端口
    app.run(host="0.0.0.0", port=port)

