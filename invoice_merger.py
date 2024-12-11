import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
from PIL import Image
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import tempfile
import traceback
import logging
import sys

# 设置日志记录
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('invoice_merger.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def show_error(exc_type, exc_value, exc_traceback):
    """全局异常处理器"""
    logging.error("Uncaught exception:", exc_info=(exc_type, exc_value, exc_traceback))
    error_msg = str(exc_value)
    messagebox.showerror("错误", f"发生错误：{error_msg}\n请查看日志文件了解详情。")

# 设置全局异常处理器
sys.excepthook = show_error

class InvoiceMergerApp:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("发票合并程序")
        self.window.geometry("600x400")
        
        self.selected_files = []
        self.setup_ui()
        logging.info("GUI initialized successfully")
    
    def setup_ui(self):
        # 主框架
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 按钮
        ttk.Button(button_frame, text="选择文件", command=self.select_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="合并并导出", command=self.merge_and_export).pack(side=tk.LEFT, padx=5)
        
        # 文件列表框架
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 文件列表
        self.file_listbox = tk.Listbox(list_frame)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.file_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.configure(yscrollcommand=scrollbar.set)

    def select_files(self):
        try:
            logging.info("Opening file dialog")
            files = filedialog.askopenfilenames(
                parent=self.window,
                title="选择发票文件",
                filetypes=[("支持的文件", "*.pdf;*.png;*.jpg;*.jpeg")]
            )
            
            if files:
                logging.info(f"Selected {len(files)} files")
                self.selected_files = list(files)
                self.update_file_list()
            else:
                logging.info("No files selected")
        except Exception as e:
            logging.error(f"Error in file selection: {str(e)}")
            logging.error(traceback.format_exc())
            messagebox.showerror("错误", f"选择文件时出错：{str(e)}")

    def update_file_list(self):
        try:
            logging.info("Updating file list")
            self.file_listbox.delete(0, tk.END)
            for file in self.selected_files:
                self.file_listbox.insert(tk.END, os.path.basename(file))
            logging.info("File list updated successfully")
        except Exception as e:
            logging.error(f"Error updating file list: {str(e)}")
            logging.error(traceback.format_exc())
            messagebox.showerror("错误", f"更新文件列表时出错：{str(e)}")

    def merge_and_export(self):
        if not self.selected_files:
            messagebox.showwarning("警告", "请先选择文件！")
            return

        try:
            output_file = filedialog.asksaveasfilename(
                parent=self.window,
                defaultextension=".pdf",
                filetypes=[("PDF文件", "*.pdf")],
                title="保存合并后的PDF"
            )
            
            if output_file:
                self.process_files(output_file)
                messagebox.showinfo("成功", "文件合并完成！")
        except Exception as e:
            logging.error(f"Error in merge and export: {str(e)}")
            logging.error(traceback.format_exc())
            messagebox.showerror("错误", f"处理文件时出错：{str(e)}")

    def process_files(self, output_file):
        # A4纸张尺寸（单位：点）
        page_width, page_height = A4
        
        # 计算每个发票的尺寸（留出边距）
        margin = 20
        invoice_width = (page_width - 3 * margin) / 2
        invoice_height = page_height - 2 * margin
        
        output = PdfWriter()
        current_page = None
        temp_files = []
        
        try:
            for i, file_path in enumerate(self.selected_files):
                logging.info(f"Processing file {i+1}/{len(self.selected_files)}: {file_path}")
                
                # 如果是偶数索引，创建新页面
                if i % 2 == 0:
                    if current_page:
                        temp_path = tempfile.mktemp(suffix='.pdf')
                        current_page.save(temp_path)
                        temp_files.append(temp_path)
                        
                    current_page = canvas.Canvas(tempfile.mktemp(suffix='.pdf'), pagesize=A4)
                
                # 确定当前发票的位置（左侧或右侧）
                x_position = margin if i % 2 == 0 else margin * 2 + invoice_width
                
                # 处理不同类型的文件
                if file_path.lower().endswith('.pdf'):
                    self.process_pdf(file_path, current_page, x_position, margin, invoice_width, invoice_height)
                else:  # 图片文件
                    self.process_image(file_path, current_page, x_position, margin, invoice_width, invoice_height)
                
                # 如果是最后一个文件，保存当前页面
                if i == len(self.selected_files) - 1:
                    temp_path = tempfile.mktemp(suffix='.pdf')
                    current_page.save(temp_path)
                    temp_files.append(temp_path)
            
            # 合并所有临时PDF文件
            for temp_file in temp_files:
                reader = PdfReader(temp_file)
                output.append_pages_from_reader(reader)
            
            # 保存最终的PDF文件
            with open(output_file, 'wb') as f:
                output.write(f)
                
            logging.info("PDF generation completed successfully")
            
        except Exception as e:
            logging.error(f"Error processing files: {str(e)}")
            raise
        finally:
            # 清理临时文件
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except Exception as e:
                    logging.error(f"Error removing temp file {temp_file}: {str(e)}")

    def process_pdf(self, pdf_path, canvas_page, x, y, width, height):
        try:
            reader = PdfReader(pdf_path)
            if len(reader.pages) > 0:
                # 在这里添加PDF页面到画布的逻辑
                pass
        except Exception as e:
            logging.error(f"Error processing PDF {pdf_path}: {str(e)}")
            raise

    def process_image(self, image_path, canvas_page, x, y, width, height):
        try:
            img = Image.open(image_path)
            aspect = img.width / img.height
            
            # 计算适合的尺寸
            if aspect > width / height:
                new_width = width
                new_height = width / aspect
            else:
                new_height = height
                new_width = height * aspect
            
            # 在画布上绘制图片
            canvas_page.drawImage(image_path, x, y, width=new_width, height=new_height)
        except Exception as e:
            logging.error(f"Error processing image {image_path}: {str(e)}")
            raise

    def run(self):
        self.window.mainloop()

def main():
    try:
        app = InvoiceMergerApp()
        app.run()
    except Exception as e:
        logging.error("Fatal error in main:", exc_info=True)
        messagebox.showerror("错误", f"程序发生致命错误：{str(e)}\n请查看日志文件了解详情。")

if __name__ == "__main__":
    main()
