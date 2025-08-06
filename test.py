#!/usr/bin/env python3
"""
WebClip 精简测试脚本
测试核心功能：PDF生成、RTF生成、错误处理、长页面处理
"""

import subprocess
import sys
import os
import glob
import json
import shutil

def test_basic_functionality():
    """测试基本功能"""
    print("=" * 50)
    print("WebClip 核心功能测试")
    print("=" * 50)
    
    # 测试URL
    test_url = "https://httpbin.org/html"
    output_dir = "test_output"
    
    print(f"测试URL: {test_url}")
    print(f"输出目录: {output_dir}")
    
    # 清理之前的测试输出
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    
    try:
        # 运行程序
        result = subprocess.run([
            sys.executable, "app.py", output_dir, test_url
        ], capture_output=True, text=True, timeout=120)
        
        print("\n程序输出:")
        print(result.stdout)
        
        if result.stderr:
            print("\n错误输出:")
            print(result.stderr)
        
        # 检查输出文件
        pdf_files = glob.glob(f"{output_dir}/documents/*.pdf")
        rtf_files = glob.glob(f"{output_dir}/textualization/*.rtf")
        report_files = glob.glob(f"{output_dir}/processing_report_*.json")
        
        print(f"\n检查结果:")
        print(f"PDF文件: {len(pdf_files)} 个")
        print(f"RTF文件: {len(rtf_files)} 个")
        print(f"报告文件: {len(report_files)} 个")
        
        if pdf_files and rtf_files:
            print("✅ 基本功能测试通过")
            
            # 显示文件大小
            for pdf_file in pdf_files:
                size = os.path.getsize(pdf_file)
                print(f"  PDF: {os.path.basename(pdf_file)} ({size} bytes)")
            
            for rtf_file in rtf_files:
                size = os.path.getsize(rtf_file)
                print(f"  RTF: {os.path.basename(rtf_file)} ({size} bytes)")
            
            return True
        else:
            print("❌ 基本功能测试失败")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ 测试超时")
        return False
    except Exception as e:
        print(f"❌ 测试出错: {e}")
        return False

def test_long_page_processing():
    """测试长页面处理功能"""
    print("\n" + "=" * 50)
    print("长页面处理测试")
    print("=" * 50)
    
    # 测试Apple Wikipedia主页
    test_url = "https://en.wikipedia.org/wiki/Apple_Inc."
    output_dir = "test_long_output"
    
    print(f"测试URL: {test_url}")
    print(f"输出目录: {output_dir}")
    print("注意: 这是一个超长Wikipedia页面，用于测试分块处理功能")
    
    # 清理之前的测试输出
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    
    try:
        # 运行程序，设置更长的超时时间
        result = subprocess.run([
            sys.executable, "app.py", output_dir, test_url
        ], capture_output=True, text=True, timeout=600)  # 10分钟超时
        
        print("\n程序输出:")
        print(result.stdout)
        
        if result.stderr:
            print("\n错误输出:")
            print(result.stderr)
        
        # 检查输出文件
        pdf_files = glob.glob(f"{output_dir}/documents/*.pdf")
        rtf_files = glob.glob(f"{output_dir}/textualization/*.rtf")
        report_files = glob.glob(f"{output_dir}/processing_report_*.json")
        
        print(f"\n检查结果:")
        print(f"PDF文件: {len(pdf_files)} 个")
        print(f"RTF文件: {len(rtf_files)} 个")
        print(f"报告文件: {len(report_files)} 个")
        
        # 检查是否包含分块处理信息
        if "图像拼接信息" in result.stdout or "开始拼接" in result.stdout:
            print("✅ 检测到长页面分块处理功能")
        else:
            print("⚠️  未检测到分块处理信息（可能是短页面）")
        
        if pdf_files and rtf_files:
            print("✅ 长页面处理测试通过")
            
            # 显示文件大小
            for pdf_file in pdf_files:
                size = os.path.getsize(pdf_file)
                print(f"  PDF: {os.path.basename(pdf_file)} ({size} bytes)")
            
            for rtf_file in rtf_files:
                size = os.path.getsize(rtf_file)
                print(f"  RTF: {os.path.basename(rtf_file)} ({size} bytes)")
            
            return True
        else:
            print("❌ 长页面处理测试失败")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ 长页面处理测试超时（可能需要更多时间）")
        return False
    except Exception as e:
        print(f"❌ 长页面处理测试出错: {e}")
        return False

def test_error_handling():
    """测试错误处理"""
    print("\n" + "=" * 50)
    print("错误处理测试")
    print("=" * 50)
    
    invalid_url = "https://invalid-domain-that-does-not-exist-12345.com"
    output_dir = "test_error_output"
    
    print(f"测试无效URL: {invalid_url}")
    
    # 清理之前的测试输出
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    
    try:
        result = subprocess.run([
            sys.executable, "app.py", output_dir, invalid_url
        ], capture_output=True, text=True, timeout=60)
        
        # 检查是否正确处理了错误
        if "处理失败" in result.stdout or "错误" in result.stdout:
            print("✅ 错误处理测试通过")
            return True
        else:
            print("❌ 错误处理测试失败")
            return False
            
    except Exception as e:
        print(f"❌ 错误处理测试出错: {e}")
        return False

def cleanup_test_files():
    """清理测试文件"""
    print("\n" + "=" * 50)
    print("清理测试文件")
    print("=" * 50)
    
    test_dirs = ["test_output", "test_long_output", "test_error_output"]
    cleaned = 0
    
    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
            print(f"✅ 清理目录: {test_dir}")
            cleaned += 1
    
    # 清理临时文件
    temp_files = glob.glob("temp_*.png") + glob.glob("final_screenshot_*.png")
    for temp_file in temp_files:
        try:
            os.remove(temp_file)
            print(f"✅ 清理临时文件: {temp_file}")
            cleaned += 1
        except:
            pass
    
    print(f"清理完成，共清理 {cleaned} 个项目")

def main():
    """主测试函数"""
    print("开始 WebClip 精简测试...")
    print(f"Python版本: {sys.version}")
    print(f"当前目录: {os.getcwd()}")
    
    # 运行测试
    test1_passed = test_basic_functionality()
    test2_passed = test_long_page_processing()
    test3_passed = test_error_handling()
    
    # 清理测试文件
    cleanup_test_files()
    
    # 输出结果
    print("\n" + "=" * 50)
    print("测试总结")
    print("=" * 50)
    print(f"基本功能测试: {'✅ 通过' if test1_passed else '❌ 失败'}")
    print(f"长页面处理测试: {'✅ 通过' if test2_passed else '❌ 失败'}")
    print(f"错误处理测试: {'✅ 通过' if test3_passed else '❌ 失败'}")
    
    total_tests = 3
    passed_tests = sum([test1_passed, test2_passed, test3_passed])
    
    print(f"\n总测试数: {total_tests}")
    print(f"通过测试: {passed_tests}")
    print(f"成功率: {passed_tests/total_tests*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  有 {total_tests - passed_tests} 个测试失败")
        return 1

if __name__ == "__main__":
    exit(main()) 