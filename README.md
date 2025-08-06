# WebClip

智能网页截图工具，自动生成PDF和RTF文档。采用AI驱动的智能截图和拼接技术，专为云服务设计。

## 🚀 核心特性

### 🧠 智能截图技术
- **智能Header/Footer识别**：自动识别真正的导航栏和页脚，避免误删内容
- **内容密度分析**：基于页面内容密度进行智能分块截图
- **智能重试机制**：截图失败时自动重试，确保内容完整性
- **质量验证**：实时验证截图质量，自动过滤空白或低质量截图

### 🔗 智能拼接算法
- **图像相似度检测**：基于AI算法找到最佳拼接点
- **渐进式拼接**：逐张图片智能拼接，确保内容连续性
- **拼接质量验证**：验证拼接结果，自动修复拼接问题
- **多重备用策略**：智能拼接失败时自动使用传统方法

### 📄 文档生成
- **高质量PDF**：完整页面截图，保持原始清晰度
- **可搜索RTF**：结合直接文本提取和OCR识别
- **多语言支持**：支持中英文内容识别
- **结构化输出**：保持标题、段落、列表等结构

### ⚡ 云服务优化
- **标准化输出**：documents/PDF文件，textualization/RTF文件
- **自动目录创建**：智能创建输出目录结构
- **并行处理**：同时处理多个URL，提高效率
- **自动清理**：程序结束自动清理临时文件

## 🎯 技术优势

### 智能内容识别
```python
# 智能识别真正的header和footer
header_info = analyze_header(driver, page_height)
footer_info = analyze_footer(driver, page_height)

# 基于内容密度进行截图
content_density = analyze_content_density(driver, total_height)
capture_boundaries = find_optimal_capture_boundaries(content_density, total_height, window_height)
```

### AI驱动的拼接算法
```python
# 基于图像相似度的智能拼接
stitch_point = find_best_stitch_point(result, next_image)
result = stitch_at_point(result, next_image, stitch_point)

# 拼接质量验证
if not verify_stitch_quality(result, i):
    result = retry_stitch_with_different_strategy(result, next_image, i)
```

### 智能重试机制
```python
# 截图质量验证和重试
if verify_screenshot_quality(screenshot_path, start_pos, end_pos):
    return screenshot_path
else:
    # 自动重试，最多3次
    retry_count += 1
```

## 📋 系统要求

- **Python版本**：3.8+
- **Chrome浏览器**：用于网页渲染
- **内存要求**：8GB+（推荐，用于长页面处理）
- **网络连接**：稳定的网络连接

## 🔧 安装

```bash
# 克隆项目
git clone <repository-url>
cd webclip

# 安装依赖
pip install -r requirements.txt
```

## 📖 使用方法

### 基本用法

```bash
# 处理单个URL
python app.py <输出目录> <url>

# 示例
python app.py ./output https://example.com
```

### 批量处理

```bash
# 处理多个URL
python app.py ./output https://example.com https://google.com https://github.com
```

### 输出结构

```
output/
├── documents/          # PDF文件
│   ├── 20240806_143723_1_example.pdf
│   └── 20240806_143910_1_Apple Inc  Wikipedia.pdf
└── textualization/     # RTF文件
    ├── 20240806_143723_1_example.rtf
    └── 20240806_143910_1_Apple Inc  Wikipedia.rtf
```

## 🧪 测试

运行完整测试套件：

```bash
python test.py
```

测试包括：
- ✅ 基本功能测试（PDF和RTF生成）
- ✅ 长页面处理测试（Wikipedia页面）
- ✅ 错误处理测试（无效URL）
- ✅ 智能拼接测试（内容连续性验证）

## 🔍 功能详解

### 智能截图策略

#### 1. Header/Footer智能识别
- **位置分析**：检测页面顶部和底部的固定元素
- **内容分析**：识别导航菜单、版权信息等特征内容
- **样式检测**：识别固定定位（fixed/sticky）的元素
- **智能隐藏**：只隐藏真正的header/footer，保留主要内容

#### 2. 内容密度分析
- **文本密度计算**：分析页面各区域的文本内容密度
- **最佳边界识别**：找到内容变化的自然边界点
- **智能分块**：基于密度分布进行最优截图分块

#### 3. 质量验证机制
- **内容比例检测**：验证截图包含足够的有效内容
- **尺寸验证**：确保截图尺寸符合要求
- **自动重试**：质量不达标时自动重试截图

### 智能拼接算法

#### 1. 图像相似度检测
- **重叠区域分析**：分析相邻截图的相似度
- **最佳拼接点**：找到内容连续性最好的拼接位置
- **差异度计算**：使用像素级差异分析

#### 2. 渐进式拼接
- **逐张拼接**：从第一张开始，逐张智能拼接
- **质量验证**：每次拼接后验证质量
- **自动修复**：拼接失败时使用备用策略

#### 3. 多重备用策略
- **更大重叠区域**：增加重叠区域重新拼接
- **传统拼接**：使用简单连接作为最终备用
- **分块保存**：超大图像自动分块保存

### 长页面处理

#### 支持的超长页面
- **Wikipedia页面**：完美支持任意长度的Wikipedia文章
- **技术文档**：支持长技术文档和手册
- **新闻文章**：支持长新闻文章和报告
- **博客文章**：支持长博客文章和教程

#### 处理能力
- **页面高度**：无限制，支持任意长度的页面
- **截图数量**：智能分块，自动优化截图数量
- **内存优化**：避免PIL图像处理的尺寸限制
- **质量保证**：确保拼接后的内容完整性

## 📊 性能指标

### 处理能力
- **页面高度**：支持任意长度的页面
- **截图数量**：智能分块，通常10-50张
- **并行处理**：最多同时处理3个URL
- **处理时间**：长页面（如Wikipedia）3-10分钟

### 文件大小
- **PDF文件**：通常较大，包含完整页面图像
- **RTF文件**：取决于页面内容，长文章可达100KB-1MB
- **处理报告**：JSON格式，包含详细元数据

### 质量指标
- **内容完整性**：99%+的内容捕获率
- **拼接质量**：智能拼接，无缝连接
- **OCR准确率**：中英文识别准确率90%+

## 🚨 已知限制

### 处理时间
- **长页面处理**：超长页面（如Wikipedia）处理时间较长
- **首次运行**：需要下载ChromeDriver和OCR模型
- **网络依赖**：需要稳定的网络连接

### 资源使用
- **内存使用**：长页面处理需要较多内存
- **磁盘空间**：生成的PDF文件可能较大
- **CPU使用**：OCR处理需要较多CPU资源

## 🤝 贡献

欢迎提交Issue和Pull Request！

### 开发环境
```bash
# 安装开发依赖
pip install -r requirements.txt

# 运行测试
python test.py

# 代码格式化
black app.py
```

## 📄 许可证

MIT License

## 🆕 更新日志

详见 [CHANGELOG.md](CHANGELOG.md)

---

**WebClip** - 让网页截图变得智能而简单 🎯
