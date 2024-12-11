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
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

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
        
        # 注册中文字体
        try:
            font_paths = [
                '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',  # WenQuanYi Zen Hei
                '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',  # WenQuanYi Micro Hei
            ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    font_name = os.path.splitext(os.path.basename(font_path))[0]
                    pdfmetrics.registerFont(TTFont(font_name, font_path))
                    logging.info(f"成功注册字体: {font_name}")
                    break
            else:
                logging.warning("未找到可用的中文字体")
        except Exception as e:
            logging.error(f"注册字体时出错: {str(e)}")

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

    def merge_invoices(self, files):
        """合并发票文件"""
        processed_files = []
        
        # 创建一个临时目录来存储上传的文件
        temp_dir = tempfile.mkdtemp()
        
        try:
            # 保存上传的文件
            for file in files:
                if file.filename:
                    filepath = os.path.join(temp_dir, secure_filename(file.filename))
                    file.save(filepath)
                    processed_files.append(filepath)
            
            # 处理所有文件
            image_files = []
            for filepath in processed_files:
                try:
                    if filepath.lower().endswith('.pdf'):
                        logging.info(f"处理文件: {filepath}")
                        # 将 PDF 转换为图片
                        img_path = self.convert_pdf_to_image(filepath)
                        if img_path:
                            image_files.append(img_path)
                    elif any(filepath.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg']):
                        logging.info(f"开始处理图片: {filepath}")
                        img = Image.open(filepath)
                        logging.info(f"图片大小: {img.size}, 模式: {img.mode}")
                        image_files.append(filepath)
                except Exception as e:
                    logging.error(f"处理文件 {filepath} 时出错: {str(e)}")
                    continue
            
            logging.info(f"共处理了 {len(processed_files)} 个文件")
            
            if not image_files:
                raise ValueError("没有可处理的文件")
            
            # 创建输出目录
            os.makedirs(self.temp_dir, exist_ok=True)
            output_path = os.path.join(self.temp_dir, 'merged_invoices.pdf')
            
            # 创建新的 PDF 文档
            c = canvas.Canvas(output_path, pagesize=A4)
            c.setPageCompression(1)  # 启用压缩以减小文件大小
            
            # 设置默认字体为中文字体
            if 'wqy-zenhei' in pdfmetrics.getRegisteredFontNames():
                c.setFont('wqy-zenhei', 10)
            
            page_width, page_height = A4
            logging.info(f"PDF页面大小: {A4}")
            
            # 计算每页可以放置的图片数量和大小
            margin = 20  # 页面边距
            image_width = page_width - 2 * margin
            max_image_height = (page_height - 3 * margin) / 2  # 每页放2张图片
            
            # 处理每个图片
            for i, img_path in enumerate(image_files):
                if i > 0 and i % 2 == 0:
                    c.showPage()  # 创建新页面
                    if 'wqy-zenhei' in pdfmetrics.getRegisteredFontNames():
                        c.setFont('wqy-zenhei', 10)
                
                img = Image.open(img_path)
                width, height = img.size
                
                # 计算缩放比例
                scale = min(image_width / width, max_image_height / height)
                new_width = width * scale
                new_height = height * scale
                
                logging.info(f"原始大小: {(width, height)}, 调整后大小: {(new_width, new_height)}")
                
                # 计算图片在页面上的位置
                x = margin
                y = page_height - margin - new_height if i % 2 == 0 else page_height - 2 * margin - 2 * new_height
                
                # 将图片绘制到 PDF
                c.drawImage(img_path, x, y, width=new_width, height=new_height, preserveAspectRatio=True)
                
                # 在图片下方添加文件名
                filename = os.path.basename(img_path)
                c.drawString(x, y - 15, filename[:50])  # 限制文件名长度
            
            # 保存最后一页
            c.save()
            
            logging.info(f"PDF文件已保存到: {output_path}")
            return output_path
            
        except Exception as e:
            logging.error(f"合并文件时出错: {str(e)}")
            raise
        finally:
            # 清理临时文件
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                logging.error(f"清理临时文件时出错: {str(e)}")

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
            
            # 设置默认字体为中文字体
            if 'wqy-zenhei' in pdfmetrics.getRegisteredFontNames():
                c.setFont('wqy-zenhei', 10)
            
            page_width, page_height = A4
            logging.info(f"PDF页面大小: {A4}")

            # 每页只放2张图片，上下排列
            margin = 20  # 页边距
            spacing = 20  # 图片间距
            max_image_height = (page_height - 2 * margin - spacing) / 2  # 每张图片的最大高度
            max_image_width = page_width - 2 * margin  # 图片的最大宽度

            # 分批处理图片，每页2张
            for i in range(0, len(processed_images), 2):
                y_position = page_height - margin
                
                # 处理当前页的图片（最多2张）
                current_images = processed_images[i:i+2]
                for image in current_images:
                    # 计算图片在页面上的大小
                    width, height = self.calculate_image_size(image, max_image_width, max_image_height)
                    x_position = (page_width - width) / 2  # 水平居中
                    
                    # 在PDF中绘制图片
                    c.drawImage(ImageReader(image), x_position, y_position - height, width, height)
                    y_position -= (height + spacing)  # 移动到下一个位置
                    
                    if progress_callback:
                        current_progress = i + current_images.index(image) + 1
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
