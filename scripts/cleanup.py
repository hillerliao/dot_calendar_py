#!/usr/bin/env python3
"""
项目清理脚本
清理临时文件、过期缓存，保持项目结构清爽
"""

import os
import sys
import glob
from datetime import datetime, timedelta

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config
from utils import W2FileCache


def clean_temp_images():
    """清理临时生成的图像文件"""
    print("🧹 清理临时图像文件...")
    
    # 定义要清理的文件模式
    temp_patterns = [
        "*chart*.png",
        "*test*.png", 
        "*demo*.png",
        "*final*.png",
        "*enhanced*.png",
        "*fixed*.png",
        "*temporary*.png",
        "*temp*.png"
    ]
    
    cleaned_count = 0
    cleaned_size = 0
    
    for pattern in temp_patterns:
        files = glob.glob(pattern)
        for file in files:
            # 保留主要示例文件
            if file in ['weather_forecast_chart.png', 'output.png']:
                print(f"   ✅ 保留主要示例: {file}")
                continue
                
            try:
                size = os.path.getsize(file)
                os.remove(file)
                cleaned_count += 1
                cleaned_size += size
                print(f"   🗑️ 删除: {file} ({size//1024} KB)")
            except Exception as e:
                print(f"   ❌ 删除失败 {file}: {str(e)}")
    
    print(f"✅ 清理完成: 删除了 {cleaned_count} 个文件，释放 {cleaned_size//1024} KB 空间")


def clean_old_cache(max_age_hours=24):
    """清理过期的缓存文件"""
    print(f"🧹 清理过期缓存 ({max_age_hours}小时前的）...")
    
    try:
        # 这里只是演示概念，实际的缓存清理需要根据W2FileCache的实现
        print("   💡 缓存清理需要根据具体缓存实现进行")
        print("   💡 建议定期删除cache目录下的旧文件")
    except Exception as e:
        print(f"   ❌ 缓存清理失败: {str(e)}")


def check_project_structure():
    """检查并建议项目结构优化"""
    print("🔍 检查项目结构...")
    
    # 统计文件类型
    files = os.listdir('.')
    
    py_files = [f for f in files if f.endswith('.py')]
    png_files = [f for f in files if f.endswith('.png')]
    md_files = [f for f in files if f.endswith('.md')]
    
    print(f"   📄 Python文件: {len(py_files)} 个")
    print(f"   🖼️  图像文件: {len(png_files)} 个")
    print(f"   📚 文档文件: {len(md_files)} 个")
    
    # 检查临时文件
    temp_files = [f for f in files if any(
        f.startswith('temp_') or 
        f.startswith('tmp_') or 
        f.startswith('test_') and f.endswith('.png') or
        f.startswith('demo_') and f.endswith('.png')
    )]
    
    if temp_files:
        print(f"   ⚠️  发现临时文件: {len(temp_files)} 个")
        for temp_file in temp_files[:5]:  # 只显示前5个
            print(f"      - {temp_file}")
        if len(temp_files) > 5:
            print(f"      ... 还有 {len(temp_files) - 5} 个")
    
    # 建议改进
    print("\n💡 项目结构建议:")
    if len(temp_files) > 0:
        print("   - 考虑创建 tests/ 目录存放测试文件")
        print("   - 考虑创建 output/ 目录存放生成的图像")
        print("   - 考虑创建 docs/ 目录存放文档")
    
    if len(png_files) > 5:
        print("   - 清理不需要的临时图像文件")
        print("   - 只保留重要的示例图像")


def organize_suggestions():
    """提供项目整理建议"""
    print("📁 项目整理建议:")
    print("=" * 50)
    
    print("1. 🗂️ 建议目录结构:")
    print("   ├── src/          # 核心源代码")
    print("   ├── tests/        # 测试文件") 
    print("   ├── docs/         # 文档文件")
    print("   ├── examples/     # 示例输出")
    print("   ├── scripts/      # 脚本文件")
    print("   └── resources/    # 资源文件")
    
    print("\n2. 🧹 清理建议:")
    print("   - 删除临时测试文件 (test_*.png)")
    print("   - 删除重复示例图像")
    print("   - 整理缓存文件到cache/目录")
    print("   - 合并相似功能的文档")
    
    print("\n3. 📚 文档建议:")
    print("   - 统一文档格式和结构")
    print("   - 添加更多使用示例")
    print("   - 包含故障排除指南")
    print("   - 添加版本更新日志")
    
    print("\n4. ⚙️ 维护建议:")
    print("   - 定期运行清理脚本")
    print("   - 更新依赖包版本")
    print("   - 检查API密钥有效性")
    print("   - 备份重要配置文件")


def main():
    """主函数"""
    print("🧪 项目清理和维护工具")
    print("=" * 50)
    
    try:
        # 1. 清理临时图像
        clean_temp_images()
        
        print("\n" + "=" * 50)
        
        # 2. 检查项目结构
        check_project_structure()
        
        print("\n" + "=" * 50)
        
        # 3. 提供整理建议
        organize_suggestions()
        
        print("\n" + "=" * 50)
        print("✅ 项目清理分析完成！")
        print("💡 根据建议手动执行整理操作")
        
    except Exception as e:
        print(f"❌ 清理过程出错: {str(e)}")
        return False
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)