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

# 设置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class InvoiceMerger:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()  # 创建临时目录
        
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

    def merge_files(self, input_files, output_file):
        try:
            # 创建一个列表存储所有处理后的图片
            processed_images = []
            
            # 处理所有文件
            for file_path in input_files:
                logging.info(f"处理文件: {file_path}")
                if not os.path.exists(file_path):
                    logging.error(f"文件不存在: {file_path}")
                    continue
                    
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
            c = canvas.Canvas(output_file, pagesize=A4)
            c.setPageCompression(0)  # 禁用压缩以保持质量
            page_width, page_height = A4
            logging.info(f"PDF页面大小: {A4}")
            
            # 设置边距和图片之间的间距
            margin = 20  # 减小页面边距
            spacing = 20  # 减小图片之间的间距
            
            # 计算可用区域
            usable_width = page_width - 2 * margin
            usable_height = (page_height - 2 * margin - spacing) / 2  # 减去边距和间距后平分高度
            logging.info(f"可用区域: 宽度={usable_width}, 高度={usable_height}")
            
            # 处理所有图片
            for i in range(0, len(processed_images), 2):
                logging.info(f"处理第 {i+1}/{len(processed_images)} 张图片")
                # 处理第一张图片（上方）
                img1 = processed_images[i]
                width1, height1 = self.calculate_image_size(img1, usable_width, usable_height)
                
                # 计算上方图片的位置（水平居中）
                x1 = (page_width - width1) / 2
                y1 = page_height - margin - height1
                logging.info(f"图片1位置: x={x1}, y={y1}, 宽度={width1}, 高度={height1}")
                
                # 将图片保存为临时文件
                temp_img1 = os.path.join(self.temp_dir, f"temp_img1_{i}.png")
                img1.save(temp_img1, 'PNG', optimize=False, quality=100)
                logging.info(f"保存临时图片1: {temp_img1}")
                c.drawImage(temp_img1, x1, y1, width=width1, height=height1)
                
                # 如果还有第二张图片（下方）
                if i + 1 < len(processed_images):
                    img2 = processed_images[i + 1]
                    width2, height2 = self.calculate_image_size(img2, usable_width, usable_height)
                    
                    # 计算下方图片的位置（水平居中）
                    x2 = (page_width - width2) / 2
                    y2 = margin
                    logging.info(f"图片2位置: x={x2}, y={y2}, 宽度={width2}, 高度={height2}")
                    
                    # 将图片保存为临时文件
                    temp_img2 = os.path.join(self.temp_dir, f"temp_img2_{i}.png")
                    img2.save(temp_img2, 'PNG', optimize=False, quality=100)
                    logging.info(f"保存临时图片2: {temp_img2}")
                    c.drawImage(temp_img2, x2, y2, width=width2, height=height2)
                
                c.showPage()  # 结束当前页面
                logging.info("页面已完成")
            
            logging.info("开始保存PDF文件...")
            c.save()  # 保存PDF文件
            logging.info(f"PDF生成成功: {output_file}")
            
        except Exception as e:
            logging.error(f"合并文件时出错: {str(e)}", exc_info=True)
            raise
        finally:
            self.cleanup()

    def cleanup(self):
        """清理临时文件和目录"""
        try:
            for file in os.listdir(self.temp_dir):
                os.remove(os.path.join(self.temp_dir, file))
            os.rmdir(self.temp_dir)
        except Exception as e:
            logging.error(f"清理临时文件时出错: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='合并发票文件为PDF')
    parser.add_argument('input_files', nargs='+', help='输入文件列表（支持PDF和图片格式）')
    parser.add_argument('-o', '--output', required=True, help='输出PDF文件路径')
    
    args = parser.parse_args()
    
    try:
        merger = InvoiceMerger()
        merger.merge_files(args.input_files, args.output)
        print(f"合并完成！输出文件：{args.output}")
    except Exception as e:
        print(f"错误：{str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
