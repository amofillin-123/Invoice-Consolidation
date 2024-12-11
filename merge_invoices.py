#!/usr/bin/env python3
import os
import sys
from PIL import Image
from pdf2image import convert_from_path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import tempfile
import logging
import argparse
import shutil
from reportlab.lib.utils import ImageReader

# 设置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class InvoiceMerger:
    def __init__(self):
        self.temp_dir = os.getenv('UPLOAD_FOLDER', tempfile.mkdtemp())
        os.makedirs(self.temp_dir, exist_ok=True)
        os.chmod(self.temp_dir, 0o777)  # 确保目录有正确的权限
        
    def convert_pdf_to_image(self, pdf_path):
        """将PDF转换为图片"""
        try:
            logging.info(f"开始转换PDF文件: {pdf_path}")
            # 使用更高的DPI来确保图片清晰度
            images = convert_from_path(pdf_path, dpi=600)
            logging.info(f"PDF转换完成，获得 {len(images)} 页")
            if images:
                # 只取第一页
                image = images[0]
                # 保存为临时文件，使用高质量设置
                temp_image_path = os.path.join(self.temp_dir, f"{os.path.basename(pdf_path)}.png")
                image.save(temp_image_path, 'PNG', optimize=False, quality=100)
                logging.info(f"临时图片已保存到: {temp_image_path}")
                return temp_image_path
            else:
                logging.error(f"PDF文件 {pdf_path} 转换后没有图片")
        except Exception as e:
            logging.error(f"转换PDF文件时出错 {pdf_path}: {str(e)}", exc_info=True)
            raise
        return None

    def process_image(self, image_path):
        """处理图片，返回PIL Image对象"""
        try:
            logging.info(f"开始处理图片: {image_path}")
            image = Image.open(image_path)
            logging.info(f"图片大小: {image.size}, 模式: {image.mode}")
            return image
        except Exception as e:
            logging.error(f"处理图片时出错 {image_path}: {str(e)}", exc_info=True)
            raise

    def calculate_image_size(self, image, max_width, max_height):
        """计算图片在页面上的大小，保持原始比例"""
        width, height = image.size
        aspect = width / height
        
        if width > max_width:
            width = max_width
            height = width / aspect
        
        if height > max_height:
            height = max_height
            width = height * aspect
            
        logging.info(f"原始大小: {image.size}, 调整后大小: ({width}, {height})")
        return width, height

    def merge_files(self, input_files, output_file, progress_callback=None):
        try:
            # 创建一个列表存储所有处理后的图片
            processed_images = []
            total_files = len(input_files)
            
            # 处理所有文件
            for index, file_path in enumerate(input_files):
                logging.info(f"处理文件: {file_path}")
                if not os.path.exists(file_path):
                    logging.error(f"文件不存在: {file_path}")
                    continue
                
                filename = os.path.basename(file_path)
                if progress_callback:
                    progress_callback(index, total_files, filename)
                    
                if file_path.lower().endswith('.pdf'):
                    # 将PDF转换为图片
                    image_path = self.convert_pdf_to_image(file_path)
                    if image_path:
                        processed_images.append(self.process_image(image_path))
                else:
                    # 直接处理图片文件
                    processed_images.append(self.process_image(file_path))
            
            if not processed_images:
                raise Exception("没有可处理的图片")
                
            logging.info(f"共处理了 {len(processed_images)} 个文件")
            
            # 创建新的PDF文件，使用更高的质量设置
            output_dir = os.path.dirname(output_file)
            os.makedirs(output_dir, exist_ok=True)
            
            c = canvas.Canvas(output_file, pagesize=A4)
            c.setPageCompression(0)  # 禁用压缩以保持质量
            page_width, page_height = A4
            logging.info(f"PDF页面大小: {A4}")

            # 计算每页可以放置的图片数量和大小
            max_images_per_page = 2
            max_image_height = (page_height - 40) / max_images_per_page  # 留出页边距
            max_image_width = page_width - 40  # 留出页边距

            # 分批处理图片
            for i in range(0, len(processed_images), max_images_per_page):
                batch = processed_images[i:i + max_images_per_page]
                y_position = page_height - 20  # 从顶部开始
                
                for image in batch:
                    # 计算图片在页面上的大小
                    width, height = self.calculate_image_size(image, max_image_width, max_image_height)
                    x_position = (page_width - width) / 2  # 居中放置
                    
                    # 在PDF中绘制图片
                    c.drawImage(ImageReader(image), x_position, y_position - height, width, height)
                    y_position -= (height + 20)  # 添加间距
                    
                    if progress_callback:
                        current_progress = i + batch.index(image) + 1
                        progress_callback(current_progress, len(processed_images), "正在生成PDF...")
                
                c.showPage()  # 创建新页面
            
            c.save()
            logging.info(f"PDF文件已保存到: {output_file}")
            
            # 确保文件存在并且可读
            if not os.path.exists(output_file):
                raise Exception(f"PDF文件未能成功保存到: {output_file}")
            
        except Exception as e:
            logging.error(f"合并文件时出错: {str(e)}", exc_info=True)
            raise

def main():
    parser = argparse.ArgumentParser(description='合并发票文件为PDF')
    parser.add_argument('input_files', nargs='+', help='输入文件列表（支持PDF和图片格式）')
    parser.add_argument('-o', '--output', required=True, help='输出PDF文件路径')
    
    args = parser.parse_args()
    
    def progress_callback(current, total, message):
        print(f"\r进度：{current}/{total} - {message}", end="")
    
    try:
        merger = InvoiceMerger()
        merger.merge_files(args.input_files, args.output, progress_callback)
        print(f"\n合并完成！输出文件：{args.output}")
    except Exception as e:
        print(f"错误：{str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
