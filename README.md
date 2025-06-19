# Web Saver - 网页截图PDF生成器

## 功能说明

一个简单的网页批量截图工具，上传包含网站链接的CSV文件，自动截取完整网页并生成PDF文档。

## 主要特性

- 📝 批量处理CSV文件中的网站链接
- 📄 自动截取完整网页（包括滚动内容）
- 🖼️ 将多个截图拼接成单个PDF文件
- ⚡ 实时显示处理进度
- 📥 自动下载生成的PDF

## 安装使用

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 启动应用
```bash
python app.py
```
应用将在 `http://localhost:8000` 启动。

### 3. 使用方法
1. 准备CSV文件，每行一个网址：
   ```
   https://example1.com
   https://example2.com
   ```
2. 访问 `http://localhost:8000`
3. 上传CSV文件
4. 等待处理完成并下载PDF

## 技术依赖

- **Flask** - Web服务框架
- **Selenium** - 浏览器自动化截图
- **Pillow** - 图像处理和PDF生成
- **Chrome** - 需要安装Chrome浏览器

## 注意事项

- 首次运行会自动下载ChromeDriver
- 生成的PDF保存在 `/tmp/Web_Saver_Output/` 目录
- 确保网络连接稳定以获得最佳截图效果
