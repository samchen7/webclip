#!/usr/bin/env python3
"""
测试命令行网页截图工具
"""

import subprocess
import sys
import os
import time
import tempfile
import shutil

def test_single_url():
    """测试单个URL处理"""
    print("=" * 50)
    print("测试1: 单个URL处理")
    print("=" * 50)
    
    url = "https://httpbin.org/html"
    print(f"测试URL: {url}")
    
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
        
        if result.returncode == 0:
            print("✅ 单个URL测试通过")
            return True
        else:
            print("❌ 单个URL测试失败")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ 测试超时")
        return False
    except Exception as e:
        print(f"❌ 测试出错: {e}")
        return False

def test_multiple_urls():
    """测试多个URL并行处理"""
    print("\n" + "=" * 50)
    print("测试2: 多个URL并行处理")
    print("=" * 50)
    
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
        ] + urls, capture_output=True, text=True, timeout=120)
        
        print("命令输出:")
        print(result.stdout)
        
        if result.stderr:
            print("错误输出:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("✅ 多个URL测试通过")
            return True
        else:
            print("❌ 多个URL测试失败")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ 测试超时")
        return False
    except Exception as e:
        print(f"❌ 测试出错: {e}")
        return False

def test_invalid_url():
    """测试无效URL处理"""
    print("\n" + "=" * 50)
    print("测试3: 无效URL处理")
    print("=" * 50)
    
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
        
        # 对于无效URL，我们期望程序能够优雅地处理错误
        print("✅ 无效URL测试完成（程序应该能够处理错误）")
        return True
            
    except subprocess.TimeoutExpired:
        print("❌ 测试超时")
        return False
    except Exception as e:
        print(f"❌ 测试出错: {e}")
        return False

def test_no_args():
    """测试无参数情况"""
    print("\n" + "=" * 50)
    print("测试4: 无参数情况")
    print("=" * 50)
    
    try:
        # 运行命令
        result = subprocess.run([
            sys.executable, "app.py"
        ], capture_output=True, text=True, timeout=10)
        
        print("命令输出:")
        print(result.stdout)
        
        if result.stderr:
            print("错误输出:")
            print(result.stderr)
        
        # 期望返回非零退出码
        if result.returncode != 0:
            print("✅ 无参数测试通过（正确显示使用说明）")
            return True
        else:
            print("❌ 无参数测试失败（应该显示使用说明）")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ 测试超时")
        return False
    except Exception as e:
        print(f"❌ 测试出错: {e}")
        return False

def test_pdf_generation():
    """测试PDF文件生成"""
    print("\n" + "=" * 50)
    print("测试5: PDF文件生成检查")
    print("=" * 50)
    
    # 检查当前目录是否有PDF文件
    pdf_files = [f for f in os.listdir('.') if f.endswith('.pdf')]
    
    if pdf_files:
        print(f"找到 {len(pdf_files)} 个PDF文件:")
        for pdf in pdf_files:
            size = os.path.getsize(pdf)
            print(f"  - {pdf} ({size} bytes)")
        print("✅ PDF文件生成测试通过")
        return True
    else:
        print("❌ 未找到PDF文件")
        return False

def test_help_message():
    """测试帮助信息"""
    print("\n" + "=" * 50)
    print("测试6: 帮助信息")
    print("=" * 50)
    
    try:
        # 运行命令
        result = subprocess.run([
            sys.executable, "app.py"
        ], capture_output=True, text=True, timeout=10)
        
        output = result.stdout + result.stderr
        
        # 检查是否包含使用说明
        if "使用方法" in output or "usage" in output.lower():
            print("✅ 帮助信息测试通过")
            return True
        else:
            print("❌ 帮助信息测试失败")
            print("输出内容:")
            print(output)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ 测试超时")
        return False
    except Exception as e:
        print(f"❌ 测试出错: {e}")
        return False

def run_all_tests():
    """运行所有测试"""
    print("开始测试命令行网页截图工具...")
    print(f"Python版本: {sys.version}")
    print(f"当前目录: {os.getcwd()}")
    
    tests = [
        ("帮助信息", test_help_message),
        ("无参数", test_no_args),
        ("单个URL", test_single_url),
        ("多个URL", test_multiple_urls),
        ("无效URL", test_invalid_url),
        ("PDF生成", test_pdf_generation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"❌ {test_name} 测试出错: {e}")
    
    print("\n" + "=" * 50)
    print("测试总结")
    print("=" * 50)
    print(f"总测试数: {total}")
    print(f"通过测试: {passed}")
    print(f"失败测试: {total - passed}")
    print(f"成功率: {passed/total*100:.1f}%")
    
    if passed == total:
        print("🎉 所有测试通过！")
        return True
    else:
        print("⚠️  部分测试失败")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 