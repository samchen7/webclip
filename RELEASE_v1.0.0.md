# Web Screenshot Tool v1.0.0 发布

🎉 **稳定版本发布** - 经过全面测试的网页截图工具

## 📦 下载

- **源代码**: [ZIP下载](https://github.com/samchen7/web-saver/archive/v1.0.0.zip)
- **Git克隆**: `git clone -b v1.0.0 https://github.com/samchen7/web-saver.git`

## ✨ 主要特性

### 🖼️ 智能内容截图
- 自动隐藏header、footer、导航栏等固定元素
- 只截取页面主要内容，避免重复结构
- 支持任意长度的页面，无截图数量限制

### ⚡ 并行处理
- 同时处理多个URL，大幅提升处理效率
- 最多同时处理3个URL（可调整）
- 每个URL使用独立的浏览器实例

### 📄 自动PDF生成
- 将截图自动拼接为PDF文件
- 文件名包含时间戳和页面标题
- 支持各种类型的网页（新闻、博客、企业网站等）

### 🧹 自动清理
- 程序结束或中断时自动清理临时文件
- 防止临时文件堆积
- 支持Ctrl+C中断时的优雅退出

### 📊 智能预估
- 显示页面总高度和预估处理时间
- 1000px步长，平衡截图质量和处理速度
- 每张截图预估3秒处理时间

## 🚀 快速开始

```bash
# 克隆仓库
git clone https://github.com/samchen7/web-saver.git
cd web-saver

# 安装依赖
pip install -r requirements.txt

# 运行测试
python test_command_line.py

# 开始使用
python app.py "https://example.com"
```

## 📋 系统要求

- Python 3.7+
- Chrome浏览器
- 网络连接
- 建议8GB以上内存（并行处理时）

## 🧪 测试结果

- ✅ **总测试数**: 6个
- ✅ **通过测试**: 6个
- ✅ **失败测试**: 0个
- ✅ **成功率**: 100%

### 测试覆盖
- 单个URL处理
- 多个URL并行处理
- 无效URL处理
- 帮助信息显示
- PDF文件生成

## 📝 使用示例

### 单个网页
```bash
python app.py "https://example.com"
```

### 多个网页
```bash
python app.py "https://example.com" "https://google.com" "https://github.com"
```

### 处理特殊字符
```bash
python app.py "https://www.google.com/search?q=test&source=hp"
```

## 🔧 技术特性

### 智能去重策略
- 使用JavaScript隐藏固定定位元素
- 从0像素开始截图，覆盖完整页面内容
- 1000px步长，确保内容连贯且无重复

### 性能优化
- 优化的截图策略，支持长页面处理
- 自动检测页面实际高度
- 智能预估截图时间和数量

### 错误处理
- 网络超时保护
- 页面加载失败重试
- 异常情况的优雅处理

## 📚 文档

- [README.md](README.md) - 详细使用说明
- [CHANGELOG.md](CHANGELOG.md) - 版本变更记录
- [test_command_line.py](test_command_line.py) - 测试脚本

## 🐛 已知问题

- 首次运行需要下载ChromeDriver，可能需要一些时间
- 长页面处理时间较长，请耐心等待
- 并行处理会增加内存使用

## 🔮 未来计划

- 支持更多浏览器（Firefox、Safari）
- 添加Web界面
- 支持更多输出格式（PNG、JPEG）
- 添加更多自定义选项

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个工具！

## 📞 支持

如果您遇到问题或有改进建议，请：
1. 查看README中的故障排除部分
2. 提交Issue描述问题
3. 提供详细的错误信息和复现步骤

---

**发布日期**: 2024年7月30日  
**版本**: v1.0.0  
**状态**: ✅ 稳定版本 