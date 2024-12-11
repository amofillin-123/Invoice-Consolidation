import PySimpleGUI as sg
import os
from PIL import Image
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import tempfile
import logging
import io

# 设置日志记录
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('invoice_merger.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class InvoiceMerger:
    def __init__(self):
        self.selected_files = []
        sg.theme('LightGrey1')
        
        # 定义窗口布局
        self.layout = [
            [sg.Text('选择发票文件（支持PDF和图片格式）：')],
            [sg.Button('选择文件', key='-SELECT-'), sg.Button('清空列表', key='-CLEAR-')],
            [sg.Listbox(values=[], size=(60, 15), key='-FILE_LIST-')],
            [sg.Button('合并并导出', key='-MERGE-'), sg.Button('退出', key='-EXIT-')]
        ]
        
        # 创建窗口
        self.window = sg.Window('发票合并程序', self.layout, finalize=True)
        logging.info("GUI initialized successfully")

    def run(self):
        while True:
            event, values = self.window.read()
            
            if event in (sg.WIN_CLOSED, '-EXIT-'):
                break
                
            try:
                if event == '-SELECT-':
                    self.select_files()
                elif event == '-CLEAR-':
                    self.clear_files()
                elif event == '-MERGE-':
                    self.merge_files()
            except Exception as e:
                logging.error(f"Error in event handling: {str(e)}", exc_info=True)
                sg.popup_error(f"操作出错：{str(e)}\n请查看日志文件了解详情。")
        
        self.window.close()

    def select_files(self):
        try:
            files = sg.popup_get_file(
                '选择发票文件',
                multiple_files=True,
                file_types=(('PDF Files', '*.pdf'), ('Image Files', '*.png;*.jpg;*.jpeg')),
            )
            
            if files:
                if isinstance(files, str):
                    files = files.split(';')
                
                self.selected_files.extend(files)
                self.update_file_list()
                logging.info(f"Added {len(files)} files")
        except Exception as e:
            logging.error(f"Error selecting files: {str(e)}", exc_info=True)
            raise

    def clear_files(self):
        self.selected_files = []
        self.update_file_list()
        logging.info("File list cleared")

    def update_file_list(self):
        file_names = [os.path.basename(f) for f in self.selected_files]
        self.window['-FILE_LIST-'].update(file_names)

    def merge_files(self):
        if not self.selected_files:
            sg.popup_warning('请先选择文件！')
            return
        
        try:
            output_file = sg.popup_get_file(
                '保存合并后的PDF',
                save_as=True,
                file_types=(('PDF Files', '*.pdf'),),
                default_extension='pdf'
            )
            
            if output_file:
                self.process_files(output_file)
                sg.popup('成功', '文件合并完成！')
        except Exception as e:
            logging.error(f"Error in merge operation: {str(e)}", exc_info=True)
            raise

    def process_files(self, output_file):
        output = PdfWriter()
        
        try:
            # 创建一个空白的A4页面模板
            page_width, page_height = A4
            margin = 20
            invoice_width = (page_width - 3 * margin) / 2
            invoice_height = page_height - 2 * margin
            
            for i in range(0, len(self.selected_files), 2):
                # 创建新页面
                output.add_blank_page(width=page_width, height=page_height)
                current_page = output.pages[-1]
                
                # 处理左侧文件
                left_file = self.selected_files[i]
                self.process_file(left_file, current_page, margin, margin)
                
                # 处理右侧文件（如果存在）
                if i + 1 < len(self.selected_files):
                    right_file = self.selected_files[i + 1]
                    self.process_file(right_file, current_page, margin * 2 + invoice_width, margin)
            
            # 保存最终的PDF文件
            with open(output_file, 'wb') as f:
                output.write(f)
            
            logging.info("PDF generation completed successfully")
        
        except Exception as e:
            logging.error(f"Error processing files: {str(e)}", exc_info=True)
            raise

    def process_file(self, file_path, output_page, x, y):
        try:
            if file_path.lower().endswith('.pdf'):
                self.process_pdf(file_path, output_page, x, y)
            else:
                self.process_image(file_path, output_page, x, y)
        except Exception as e:
            logging.error(f"Error processing file {file_path}: {str(e)}", exc_info=True)
            raise

    def process_pdf(self, pdf_path, output_page, x, y):
        try:
            # 创建一个临时PDF用于存储转换后的页面
            temp_pdf = tempfile.mktemp(suffix='.pdf')
            c = canvas.Canvas(temp_pdf, pagesize=A4)
            
            # 读取源PDF
            reader = PdfReader(pdf_path)
            if len(reader.pages) > 0:
                # 获取第一页的尺寸
                source_page = reader.pages[0]
                source_width = float(source_page.mediabox.width)
                source_height = float(source_page.mediabox.height)
                
                # 计算缩放比例
                scale = min((A4[0]/2 - 40) / source_width, (A4[1] - 40) / source_height)
                
                # 创建一个新的PDF，将源页面作为XObject
                c.saveState()
                c.translate(x, y)
                c.scale(scale, scale)
                
                # 使用PDFContentStream将源页面内容复制到新页面
                page_content = source_page.extract_text()
                c.drawString(0, 0, page_content)
                
                c.restoreState()
                c.save()
                
                # 将临时PDF合并到输出页面
                temp_reader = PdfReader(temp_pdf)
                if len(temp_reader.pages) > 0:
                    output_page.merge_page(temp_reader.pages[0])
                
                # 清理临时文件
                if os.path.exists(temp_pdf):
                    os.remove(temp_pdf)
                
        except Exception as e:
            logging.error(f"Error processing PDF {pdf_path}: {str(e)}", exc_info=True)
            raise

    def process_image(self, image_path, output_page, x, y):
        try:
            # 创建一个临时的PDF来存储图片
            temp_pdf = tempfile.mktemp(suffix='.pdf')
            c = canvas.Canvas(temp_pdf, pagesize=A4)
            
            # 读取图片并计算尺寸
            img = Image.open(image_path)
            img_width, img_height = img.size
            
            # 计算缩放比例
            scale = min((A4[0]/2 - 40) / img_width, (A4[1] - 40) / img_height)
            new_width = img_width * scale
            new_height = img_height * scale
            
            # 在画布上绘制图片
            c.drawImage(image_path, x, y, width=new_width, height=new_height)
            c.save()
            
            # 将临时PDF合并到输出页面
            temp_reader = PdfReader(temp_pdf)
            if len(temp_reader.pages) > 0:
                output_page.merge_page(temp_reader.pages[0])
            
            # 清理临时文件
            if os.path.exists(temp_pdf):
                os.remove(temp_pdf)
                
        except Exception as e:
            logging.error(f"Error processing image {image_path}: {str(e)}", exc_info=True)
            raise

def main():
    try:
        app = InvoiceMerger()
        app.run()
    except Exception as e:
        logging.error("Fatal error in main:", exc_info=True)
        sg.popup_error(f"程序发生致命错误：{str(e)}\n请查看日志文件了解详情。")

if __name__ == "__main__":
    main()
