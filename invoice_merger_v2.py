import os
from PIL import Image
from pdf2image import convert_from_path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import tempfile
import logging
import io
from datetime import datetime
import tkinter as tk
from tkinter import filedialog

# 设置日志记录
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('invoice_merger.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def main():
    try:
        # 创建一个隐藏的根窗口
        root = tk.Tk()
        root.withdraw()
        
        # 使用tkinter的文件选择对话框
        files = filedialog.askopenfilenames(
            title='选择要合并的发票文件',
            filetypes=[
                ('PDF文件', '*.pdf'),
                ('图片文件', '*.png *.jpg *.jpeg'),
                ('所有文件', '*.*')
            ]
        )
        
        if not files:
            return
            
        # 创建合并器实例并处理文件
        merger = InvoiceMerger()
        try:
            # 生成输出文件名（在下载文件夹中，使用时间戳）
            downloads_folder = os.path.expanduser('~/Downloads')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = os.path.join(downloads_folder, f'merged_invoices_{timestamp}.pdf')
            
            # 处理文件
            merger.process_files(files, output_file)
            
            logging.info(f"文件已保存至：{output_file}")
        finally:
            merger.cleanup()
            
    except Exception as e:
        logging.error("Fatal error in main:", exc_info=True)
    finally:
        # 确保关闭隐藏的根窗口
        root.destroy()

class InvoiceMerger:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()  # 创建临时目录

    def process_files(self, files, output_file):
        """处理文件并生成合并后的PDF"""
        try:
            # 创建一个新的PDF文件
            c = canvas.Canvas(output_file, pagesize=A4)
            width, height = A4  # 获取A4纸张的宽度和高度
            
            # 设置页面边距
            margin = 50
            spacing = 20
            max_width = (width - 2 * margin)
            max_height = (height - 2 * margin - spacing) / 2
            
            # 处理所有文件
            for i in range(0, len(files), 2):
                # 处理第一个文件
                file1 = files[i]
                img1 = self.process_image(file1)
                if img1:
                    width1, height1 = self.calculate_image_size(img1, max_width, max_height)
                    x1 = (width - width1) / 2
                    y1 = height - margin - height1
                    
                    temp_img1 = os.path.join(self.temp_dir, f"temp_img1_{i}.png")
                    img1.save(temp_img1)
                    c.drawImage(temp_img1, x1, y1, width=width1, height=height1)
                
                # 如果还有第二个文件，处理它
                if i + 1 < len(files):
                    file2 = files[i + 1]
                    img2 = self.process_image(file2)
                    if img2:
                        width2, height2 = self.calculate_image_size(img2, max_width, max_height)
                        x2 = (width - width2) / 2
                        y2 = margin
                        
                        temp_img2 = os.path.join(self.temp_dir, f"temp_img2_{i}.png")
                        img2.save(temp_img2)
                        c.drawImage(temp_img2, x2, y2, width=width2, height=height2)
                
                c.showPage()
            
            c.save()
            logging.info("PDF generation completed successfully")
            
        except Exception as e:
            logging.error(f"Error processing files: {str(e)}", exc_info=True)
            raise

    def convert_pdf_to_image(self, pdf_path):
        """将PDF转换为图片"""
        try:
            logging.info(f"Converting PDF: {pdf_path}")
            images = convert_from_path(
                pdf_path,
                dpi=200,
                poppler_path='/opt/homebrew/bin',
                first_page=1,
                last_page=1
            )
            
            if not images:
                raise Exception(f"无法从PDF文件中提取图片：{pdf_path}")
            
            # 保存第一页为临时图片文件
            temp_image_path = os.path.join(self.temp_dir, f"temp_pdf_{os.path.basename(pdf_path)}.png")
            images[0].save(temp_image_path, 'PNG')
            return temp_image_path
            
        except Exception as e:
            logging.error(f"转换PDF文件时出错 {pdf_path}: {str(e)}", exc_info=True)
            raise Exception(f"PDF文件处理失败 {os.path.basename(pdf_path)}: {str(e)}")

    def process_image(self, image_path):
        """处理图片，返回PIL Image对象"""
        try:
            logging.info(f"Processing image: {image_path}")
            # 如果是PDF，先转换为图片
            if image_path.lower().endswith('.pdf'):
                image_path = self.convert_pdf_to_image(image_path)
            
            # 打开并转换图片
            with Image.open(image_path) as img:
                # 转换为RGB模式
                if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1])
                    return background
                elif img.mode != 'RGB':
                    return img.convert('RGB')
                return img.copy()
                
        except Exception as e:
            logging.error(f"处理图片时出错 {image_path}: {str(e)}", exc_info=True)
            raise Exception(f"图片处理失败 {os.path.basename(image_path)}: {str(e)}")

    def calculate_image_size(self, image, max_width, max_height):
        """计算图片在页面上的大小，保持原始比例"""
        # 获取原始尺寸
        width, height = image.size
        
        # 计算缩放比例
        width_ratio = max_width / width
        height_ratio = max_height / height
        ratio = min(width_ratio, height_ratio)
        
        # 返回新的尺寸
        return width * ratio, height * ratio

    def cleanup(self):
        """清理临时文件和目录"""
        try:
            for file in os.listdir(self.temp_dir):
                os.remove(os.path.join(self.temp_dir, file))
            os.rmdir(self.temp_dir)
            logging.info("Cleaned up temporary files")
        except Exception as e:
            logging.error(f"Error cleaning up temporary files: {str(e)}")

if __name__ == "__main__":
    main()
