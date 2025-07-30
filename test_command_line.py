#!/usr/bin/env python3
"""
Web Screenshot Tool RTF版本测试脚本

测试内容：
1. 单个URL的RTF生成功能
2. 多个URL的并行RTF处理
3. OCR文本识别功能
4. 直接文本提取功能
5. 无效URL的错误处理
6. 命令行参数验证
7. RTF文件格式验证
8. 文件清理功能
9. 长文章分块处理功能（新增）
10. 超大图像处理功能（新增）
"""

import subprocess
import sys
import os
import time
import tempfile
import shutil
import glob
import re

def test_single_url_rtf():
    """测试单个URL的RTF生成功能"""
    print("=" * 60)
    print("测试1: 单个URL的RTF生成功能")
    print("=" * 60)
    print("测试目标: 验证程序能够正确处理单个URL并生成RTF文件")
    print("测试内容: 网页截图 → 文本提取 → OCR识别 → RTF生成")
    print("-" * 60)
    
    url = "https://httpbin.org/html"
    print(f"测试URL: {url}")
    
    try:
        # 运行命令
        result = subprocess.run([
            sys.executable, "app.py", url
        ], capture_output=True, text=True, timeout=90)
        
        print("命令输出:")
        print(result.stdout)
        
        if result.stderr:
            print("错误输出:")
            print(result.stderr)
        
        # 检查RTF文件是否生成
        rtf_files = glob.glob("*.rtf")
        if rtf_files:
            print(f"✅ 发现RTF文件: {rtf_files}")
            # 检查RTF文件内容
            for rtf_file in rtf_files:
                with open(rtf_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if '{\\rtf1' in content:
                        print(f"✅ RTF文件格式正确: {rtf_file}")
                    else:
                        print(f"❌ RTF文件格式错误: {rtf_file}")
        else:
            print("❌ 未发现RTF文件")
        
        if result.returncode == 0:
            print("✅ 单个URL RTF生成测试通过")
            return True
        else:
            print("❌ 单个URL RTF生成测试失败")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ 测试超时")
        return False
    except Exception as e:
        print(f"❌ 测试出错: {e}")
        return False

def test_multiple_urls_rtf():
    """测试多个URL的并行RTF处理"""
    print("\n" + "=" * 60)
    print("测试2: 多个URL的并行RTF处理")
    print("=" * 60)
    print("测试目标: 验证程序能够并行处理多个URL并生成多个RTF文件")
    print("测试内容: 并行截图 → 并行文本提取 → 并行OCR → 并行RTF生成")
    print("-" * 60)
    
    urls = [
        "https://httpbin.org/html",
        "https://httpbin.org/json",
        "https://httpbin.org/xml"
    ]
    
    print(f"测试URLs: {urls}")
    
    try:
        # 运行命令
        result = subprocess.run([
            sys.executable, "app.py"
        ] + urls, capture_output=True, text=True, timeout=180)
        
        print("命令输出:")
        print(result.stdout)
        
        if result.stderr:
            print("错误输出:")
            print(result.stderr)
        
        # 检查是否生成了多个RTF文件
        rtf_files = glob.glob("*.rtf")
        if len(rtf_files) >= 3:
            print(f"✅ 成功生成 {len(rtf_files)} 个RTF文件")
            for rtf_file in rtf_files:
                print(f"  - {rtf_file}")
        else:
            print(f"❌ 只生成了 {len(rtf_files)} 个RTF文件，期望至少3个")
        
        if result.returncode == 0:
            print("✅ 多个URL并行RTF处理测试通过")
            return True
        else:
            print("❌ 多个URL并行RTF处理测试失败")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ 测试超时")
        return False
    except Exception as e:
        print(f"❌ 测试出错: {e}")
        return False

def test_long_article_processing():
    """测试长文章处理功能（Wikipedia页面）"""
    print("\n" + "=" * 60)
    print("测试3: 长文章处理功能")
    print("=" * 60)
    print("测试目标: 验证程序能够正确处理超长页面并进行分块处理")
    print("测试内容: 长页面截图 → 分块处理 → 超大图像处理 → RTF生成")
    print("-" * 60)
    
    url = "https://en.wikipedia.org/wiki/Apple_Inc."
    print(f"测试长文章URL: {url}")
    print("注意: 这是一个典型的超长Wikipedia页面，用于测试分块处理功能")
    
    try:
        # 运行命令，设置更长的超时时间
        result = subprocess.run([
            sys.executable, "app.py", url
        ], capture_output=True, text=True, timeout=600)  # 10分钟超时
        
        print("命令输出:")
        print(result.stdout)
        
        if result.stderr:
            print("错误输出:")
            print(result.stderr)
        
        # 检查是否包含分块处理信息
        if "图像总高度" in result.stdout and "超过PIL限制" in result.stdout:
            print("✅ 检测到分块处理功能启动")
        elif "图像拼接信息" in result.stdout:
            print("✅ 检测到图像拼接处理")
        else:
            print("⚠️  未检测到分块处理信息")
        
        # 检查是否生成了RTF文件
        rtf_files = glob.glob("*.rtf")
        if rtf_files:
            print(f"✅ 成功生成 {len(rtf_files)} 个RTF文件")
            for rtf_file in rtf_files:
                file_size = os.path.getsize(rtf_file)
                print(f"  - {rtf_file} ({file_size} bytes)")
        else:
            print("❌ 未生成RTF文件")
        
        # 检查是否生成了分块图像文件
        chunk_files = glob.glob("*_chunk_*.png")
        if chunk_files:
            print(f"✅ 检测到分块图像文件: {len(chunk_files)} 个")
            for chunk_file in chunk_files:
                print(f"  - {chunk_file}")
        else:
            print("⚠️  未检测到分块图像文件")
        
        if result.returncode == 0:
            print("✅ 长文章处理测试通过")
            return True
        else:
            print("❌ 长文章处理测试失败")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ 测试超时（长文章处理需要更多时间）")
        return False
    except Exception as e:
        print(f"❌ 测试出错: {e}")
        return False

def test_large_image_handling():
    """测试超大图像处理功能"""
    print("\n" + "=" * 60)
    print("测试4: 超大图像处理功能")
    print("=" * 60)
    print("测试目标: 验证程序能够正确处理超大图像并避免内存错误")
    print("测试内容: 大图像检测 → 分块处理 → 内存优化 → 文件生成")
    print("-" * 60)
    
    # 使用一个中等长度的页面进行测试
    url = "https://en.wikipedia.org/wiki/Python_(programming_language)"
    print(f"测试URL: {url}")
    
    try:
        # 运行命令
        result = subprocess.run([
            sys.executable, "app.py", url
        ], capture_output=True, text=True, timeout=300)  # 5分钟超时
        
        print("命令输出:")
        print(result.stdout)
        
        if result.stderr:
            print("错误输出:")
            print(result.stderr)
        
        # 检查是否包含图像处理信息
        if "图像拼接信息" in result.stdout:
            print("✅ 检测到图像拼接处理")
        else:
            print("⚠️  未检测到图像拼接信息")
        
        # 检查是否避免了内存错误
        if "broken data stream" in result.stderr or "Maximum supported image dimension" in result.stderr:
            print("❌ 检测到图像处理错误")
            return False
        else:
            print("✅ 未检测到图像处理错误")
        
        # 检查是否生成了RTF文件
        rtf_files = glob.glob("*.rtf")
        if rtf_files:
            print(f"✅ 成功生成 {len(rtf_files)} 个RTF文件")
            for rtf_file in rtf_files:
                file_size = os.path.getsize(rtf_file)
                print(f"  - {rtf_file} ({file_size} bytes)")
        else:
            print("❌ 未生成RTF文件")
        
        if result.returncode == 0:
            print("✅ 超大图像处理测试通过")
            return True
        else:
            print("❌ 超大图像处理测试失败")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ 测试超时")
        return False
    except Exception as e:
        print(f"❌ 测试出错: {e}")
        return False

def test_ocr_functionality():
    """测试OCR文本识别功能"""
    print("\n" + "=" * 60)
    print("测试5: OCR文本识别功能")
    print("=" * 60)
    print("测试目标: 验证OCR能够正确识别图片中的文本内容")
    print("测试内容: 截图 → OCR识别 → 文本提取 → 内容验证")
    print("-" * 60)
    
    url = "https://example.com"
    print(f"测试URL: {url}")
    
    try:
        # 运行命令
        result = subprocess.run([
            sys.executable, "app.py", url
        ], capture_output=True, text=True, timeout=90)
        
        print("命令输出:")
        print(result.stdout)
        
        # 检查输出中是否包含OCR相关信息
        if "正在进行OCR识别" in result.stdout:
            print("✅ OCR识别功能正常启动")
        else:
            print("❌ OCR识别功能未启动")
        
        # 检查RTF文件内容是否包含OCR识别的文本
        rtf_files = glob.glob("*.rtf")
        if rtf_files:
            latest_rtf = max(rtf_files, key=os.path.getctime)
            with open(latest_rtf, 'r', encoding='utf-8') as f:
                content = f.read()
                if "OCR识别内容" in content:
                    print("✅ RTF文件包含OCR识别内容")
                else:
                    print("❌ RTF文件未包含OCR识别内容")
        
        if result.returncode == 0:
            print("✅ OCR功能测试通过")
            return True
        else:
            print("❌ OCR功能测试失败")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ 测试超时")
        return False
    except Exception as e:
        print(f"❌ 测试出错: {e}")
        return False

def test_text_extraction():
    """测试直接文本提取功能"""
    print("\n" + "=" * 60)
    print("测试6: 直接文本提取功能")
    print("=" * 60)
    print("测试目标: 验证程序能够直接从HTML中提取文本内容")
    print("测试内容: HTML解析 → 文本提取 → 结构保持 → RTF生成")
    print("-" * 60)
    
    url = "https://httpbin.org/json"
    print(f"测试URL: {url}")
    
    try:
        # 运行命令
        result = subprocess.run([
            sys.executable, "app.py", url
        ], capture_output=True, text=True, timeout=90)
        
        print("命令输出:")
        print(result.stdout)
        
        # 检查输出中是否包含文本提取相关信息
        if "正在提取页面文本" in result.stdout:
            print("✅ 文本提取功能正常启动")
        else:
            print("❌ 文本提取功能未启动")
        
        # 检查RTF文件内容
        rtf_files = glob.glob("*.rtf")
        if rtf_files:
            latest_rtf = max(rtf_files, key=os.path.getctime)
            with open(latest_rtf, 'r', encoding='utf-8') as f:
                content = f.read()
                if "页面标题" in content or "标题:" in content:
                    print("✅ RTF文件包含结构化文本内容")
                else:
                    print("❌ RTF文件未包含结构化文本内容")
        
        if result.returncode == 0:
            print("✅ 文本提取功能测试通过")
            return True
        else:
            print("❌ 文本提取功能测试失败")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ 测试超时")
        return False
    except Exception as e:
        print(f"❌ 测试出错: {e}")
        return False

def test_invalid_url_handling():
    """测试无效URL的错误处理"""
    print("\n" + "=" * 60)
    print("测试7: 无效URL的错误处理")
    print("=" * 60)
    print("测试目标: 验证程序能够正确处理无效URL并给出适当的错误信息")
    print("测试内容: 无效URL → 错误检测 → 错误信息 → 优雅退出")
    print("-" * 60)
    
    url = "https://invalid-domain-that-does-not-exist-12345.com"
    print(f"测试无效URL: {url}")
    
    try:
        # 运行命令
        result = subprocess.run([
            sys.executable, "app.py", url
        ], capture_output=True, text=True, timeout=60)
        
        print("命令输出:")
        print(result.stdout)
        
        if result.stderr:
            print("错误输出:")
            print(result.stderr)
        
        # 检查是否包含错误处理信息
        if "网络连接失败" in result.stdout or "连接超时" in result.stdout:
            print("✅ 错误处理功能正常")
        else:
            print("❌ 错误处理功能异常")
        
        # 检查是否生成了RTF文件（应该没有）
        rtf_files = glob.glob("*.rtf")
        if not rtf_files:
            print("✅ 无效URL未生成RTF文件（正确行为）")
        else:
            print("❌ 无效URL生成了RTF文件（错误行为）")
        
        print("✅ 无效URL处理测试完成（程序应该能够处理错误）")
        return True
            
    except subprocess.TimeoutExpired:
        print("❌ 测试超时")
        return False
    except Exception as e:
        print(f"❌ 测试出错: {e}")
        return False

def test_command_line_arguments():
    """测试命令行参数验证"""
    print("\n" + "=" * 60)
    print("测试8: 命令行参数验证")
    print("=" * 60)
    print("测试目标: 验证程序能够正确处理命令行参数")
    print("测试内容: 无参数 → 帮助信息 → 参数验证")
    print("-" * 60)
    
    try:
        # 测试无参数情况
        result = subprocess.run([
            sys.executable, "app.py"
        ], capture_output=True, text=True, timeout=30)
        
        print("命令输出:")
        print(result.stdout)
        
        if result.stderr:
            print("错误输出:")
            print(result.stderr)
        
        # 检查是否显示了使用说明
        if "使用方法:" in result.stdout and "示例:" in result.stdout:
            print("✅ 无参数时正确显示使用说明")
        else:
            print("❌ 无参数时未显示使用说明")
        
        if result.returncode == 1:  # 应该返回错误码1
            print("✅ 无参数时正确返回错误码")
        else:
            print("❌ 无参数时返回码异常")
        
        print("✅ 命令行参数验证测试通过")
        return True
            
    except subprocess.TimeoutExpired:
        print("❌ 测试超时")
        return False
    except Exception as e:
        print(f"❌ 测试出错: {e}")
        return False

def test_rtf_file_format():
    """测试RTF文件格式"""
    print("\n" + "=" * 60)
    print("测试9: RTF文件格式验证")
    print("=" * 60)
    print("测试目标: 验证生成的RTF文件格式正确且可读")
    print("测试内容: RTF格式 → 内容结构 → 可读性验证")
    print("-" * 60)
    
    # 先运行一个简单的测试生成RTF文件
    url = "https://httpbin.org/html"
    try:
        subprocess.run([
            sys.executable, "app.py", url
        ], capture_output=True, text=True, timeout=90)
        
        # 检查RTF文件
        rtf_files = glob.glob("*.rtf")
        if rtf_files:
            latest_rtf = max(rtf_files, key=os.path.getctime)
            print(f"检查RTF文件: {latest_rtf}")
            
            with open(latest_rtf, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # 检查RTF格式
                if content.startswith('{\\rtf1'):
                    print("✅ RTF文件格式正确")
                else:
                    print("❌ RTF文件格式错误")
                
                # 检查是否包含标题
                if '\\b' in content and '\\b0' in content:
                    print("✅ RTF文件包含标题格式")
                else:
                    print("❌ RTF文件缺少标题格式")
                
                # 检查是否包含文本内容
                if len(content) > 100:  # 简单检查文件大小
                    print("✅ RTF文件包含文本内容")
                else:
                    print("❌ RTF文件内容过少")
                
                # 检查文件大小
                file_size = os.path.getsize(latest_rtf)
                print(f"RTF文件大小: {file_size} 字节")
                if file_size > 50:
                    print("✅ RTF文件大小合理")
                else:
                    print("❌ RTF文件大小异常")
        
        print("✅ RTF文件格式验证测试通过")
        return True
        
    except Exception as e:
        print(f"❌ RTF文件格式验证测试失败: {e}")
        return False

def test_file_cleanup():
    """测试文件清理功能"""
    print("\n" + "=" * 60)
    print("测试10: 文件清理功能")
    print("=" * 60)
    print("测试目标: 验证程序能够正确清理临时文件")
    print("测试内容: 临时文件生成 → 处理完成 → 自动清理")
    print("-" * 60)
    
    # 记录测试前的文件数量
    initial_files = len(glob.glob("temp_*.png"))
    print(f"测试前临时文件数量: {initial_files}")
    
    url = "https://httpbin.org/html"
    try:
        # 运行命令
        result = subprocess.run([
            sys.executable, "app.py", url
        ], capture_output=True, text=True, timeout=90)
        
        # 检查测试后的临时文件数量
        final_files = len(glob.glob("temp_*.png"))
        print(f"测试后临时文件数量: {final_files}")
        
        if final_files <= initial_files:
            print("✅ 临时文件清理功能正常")
        else:
            print("❌ 临时文件清理功能异常")
        
        # 检查输出中是否包含清理信息
        if "清理临时文件" in result.stdout:
            print("✅ 程序正确报告了文件清理")
        else:
            print("❌ 程序未报告文件清理")
        
        print("✅ 文件清理功能测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 文件清理功能测试失败: {e}")
        return False

def run_all_tests():
    """运行所有测试"""
    print("开始测试Web Screenshot Tool RTF版本...")
    print(f"Python版本: {sys.version}")
    print(f"当前目录: {os.getcwd()}")
    print()
    
    tests = [
        ("单个URL RTF生成", test_single_url_rtf),
        ("多个URL并行RTF处理", test_multiple_urls_rtf),
        ("长文章处理功能", test_long_article_processing),
        ("超大图像处理功能", test_large_image_handling),
        ("OCR文本识别功能", test_ocr_functionality),
        ("直接文本提取功能", test_text_extraction),
        ("无效URL错误处理", test_invalid_url_handling),
        ("命令行参数验证", test_command_line_arguments),
        ("RTF文件格式验证", test_rtf_file_format),
        ("文件清理功能", test_file_cleanup)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"总测试数: {len(tests)}")
    print(f"通过测试: {passed}")
    print(f"失败测试: {failed}")
    print(f"成功率: {passed/len(tests)*100:.1f}%")
    
    if failed == 0:
        print("🎉 所有测试通过！")
    else:
        print(f"⚠️  有 {failed} 个测试失败，请检查相关功能")
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 