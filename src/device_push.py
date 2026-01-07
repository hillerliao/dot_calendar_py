#!/usr/bin/env python3
"""
设备图片推送工具
支持推送任意图片到Dot设备
"""

import os
import sys
import base64
import argparse
from PIL import Image
import requests
from io import BytesIO

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config


def blackwhite_image(image: Image.Image) -> Image.Image:
    """Convert image to black and white for Dot device"""
    # Work with RGBA image to properly handle transparency
    if image.mode != 'RGBA':
        rgba_image = image.convert('RGBA')
    else:
        rgba_image = image
    
    # Create new image with white background
    bw_image = Image.new('RGB', rgba_image.size, (255, 255, 255))
    
    # Threshold for determining black vs white
    threshold = 200
    
    # Process each pixel
    for x in range(rgba_image.width):
        for y in range(rgba_image.height):
            r, g, b, a = rgba_image.getpixel((x, y))
            # If pixel is transparent, keep it white
            if a < 128:  # Transparent or semi-transparent
                bw_image.putpixel((x, y), (255, 255, 255))
            else:
                # Convert to grayscale
                gray = int(0.299 * r + 0.587 * g + 0.114 * b)
                # Apply threshold
                if gray < threshold:
                    bw_image.putpixel((x, y), (0, 0, 0))
                else:
                    bw_image.putpixel((x, y), (255, 255, 255))
    
    return bw_image


def push_image_to_device(image_path: str, device_id: str = None, app_key: str = None):
    """Push image to Dot device"""
    
    # Use defaults from config if not provided
    device_id = device_id or config.DOT_DEVICE_ID
    app_key = app_key or config.DOT_APP_KEY
    
    if not device_id or not app_key:
        print("❌ 错误: 设备ID或应用密钥未配置")
        print("请在.env文件中设置 DOT_DEVICE_ID 和 DOT_APP_KEY")
        return False
    
    if not os.path.exists(image_path):
        print(f"❌ 错误: 图片文件不存在: {image_path}")
        return False
    
    try:
        print(f"📱 正在推送图片到设备...")
        print(f"📁 图片文件: {image_path}")
        print(f"🔧 设备ID: {device_id}")
        
        # Load and convert image
        image = Image.open(image_path)
        print(f"📏 图片尺寸: {image.width}x{image.height}")
        
        # Convert to black and white
        print("🎨 转换为黑白图片...")
        bw_image = blackwhite_image(image)
        
        # Save image to bytes
        img_buffer = BytesIO()
        bw_image.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        image_content = img_buffer.getvalue()
        
        # Send to Dot devices
        devices = [d.strip() for d in device_id.split(',')]
        success_count = 0
        
        for device in devices:
            try:
                print(f"📡 推送到设备: {device}")
                
                url = 'https://dot.mindreset.tech/api/open/image'
                payload = {
                    "deviceId": device,
                    "image": base64.b64encode(image_content).decode('utf-8'),
                    "refreshNow": True,
                    "border": 0,
                    "ditherType": "NONE",
                    "link": "https://dot.mindreset.tech"
                }
                
                headers = {
                    'Authorization': f'Bearer {app_key}',
                    'Content-Type': 'application/json',
                    'Accept-Encoding': 'identity'  # 禁用gzip压缩
                }
                
                response = requests.post(url, json=payload, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    print(f"✅ 设备 {device} 推送成功")
                    success_count += 1
                else:
                    print(f"❌ 设备 {device} 推送失败: {response.status_code}")
                    if response.text:
                        print(f"   错误信息: {response.text}")
                        
            except requests.RequestException as e:
                print(f"❌ 设备 {device} 推送异常: {str(e)}")
        
        print(f"📊 推送结果: {success_count}/{len(devices)} 个设备成功")
        return success_count > 0
        
    except Exception as e:
        print(f"❌ 推送失败: {str(e)}")
        return False


def main():
    """命令行主函数"""
    parser = argparse.ArgumentParser(description='推送图片到Dot设备')
    parser.add_argument('image_path', help='图片文件路径')
    parser.add_argument('--device-id', help='设备ID (覆盖配置文件)')
    parser.add_argument('--app-key', help='应用密钥 (覆盖配置文件)')
    parser.add_argument('--resize', help='调整图片尺寸 (格式: 296x152)')
    
    args = parser.parse_args()
    
    # Optional resize
    if args.resize:
        try:
            width, height = map(int, args.resize.split('x'))
            print(f"🔧 调整图片尺寸为: {width}x{height}")
            
            image = Image.open(args.image_path)
            resized_image = image.resize((width, height), Image.Resampling.LANCZOS)
            
            # Save resized image temporarily
            temp_path = f"temp_resized_{os.path.basename(args.image_path)}"
            resized_image.save(temp_path)
            
            # Push resized image
            success = push_image_to_device(
                temp_path, 
                args.device_id, 
                args.app_key
            )
            
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
            sys.exit(0 if success else 1)
            
        except ValueError:
            print("❌ 错误: 尺寸格式不正确，请使用格式: 296x152")
            sys.exit(1)
    
    # Push original image
    success = push_image_to_device(args.image_path, args.device_id, args.app_key)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()