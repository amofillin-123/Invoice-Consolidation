#!/usr/bin/env python3
from flask import Flask, request, send_file, render_template, jsonify
import os
from werkzeug.utils import secure_filename
from merge_invoices import InvoiceMerger
import tempfile
import logging
import shutil
import uuid

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='invoice_merger.log'
)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制上传文件大小为16MB
app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()  # 创建临时上传目录

# 用于存储处理进度的字典
processing_status = {}

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/progress/<task_id>')
def get_progress(task_id):
    """获取处理进度"""
    if task_id in processing_status:
        return jsonify(processing_status[task_id])
    return jsonify({'status': 'unknown'})

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'files[]' not in request.files:
        return jsonify({'error': '没有选择文件'}), 400
    
    files = request.files.getlist('files[]')
    if not files or files[0].filename == '':
        return jsonify({'error': '没有选择文件'}), 400

    # 检查所有文件
    for file in files:
        if not allowed_file(file.filename):
            return jsonify({'error': f'文件 {file.filename} 格式不正确，仅支持 PDF 和常见图片格式'}), 400

    # 生成任务ID
    task_id = str(uuid.uuid4())
    processing_status[task_id] = {
        'status': 'starting',
        'progress': 0,
        'total_files': len(files),
        'processed_files': 0,
        'current_file': '',
        'message': '准备处理文件...'
    }

    # 保存文件并处理
    try:
        temp_dir = tempfile.mkdtemp()
        saved_files = []
        
        # 保存文件
        for i, file in enumerate(files):
            filename = secure_filename(file.filename)
            filepath = os.path.join(temp_dir, filename)
            file.save(filepath)
            saved_files.append(filepath)
            
            # 更新保存进度
            processing_status[task_id].update({
                'status': 'saving',
                'progress': int((i + 1) / len(files) * 40),  # 文件保存占总进度的40%
                'processed_files': i + 1,
                'current_file': filename,
                'message': f'正在保存文件 {filename}...'
            })

        # 合并文件
        processing_status[task_id].update({
            'status': 'merging',
            'progress': 40,
            'message': '开始合并文件...'
        })

        merger = InvoiceMerger()
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'merged_invoices.pdf')
        
        # 更新处理进度的回调函数
        def progress_callback(current, total, filename):
            progress = int(40 + (current / total) * 60)  # 文件处理占总进度的60%
            processing_status[task_id].update({
                'status': 'processing',
                'progress': progress,
                'current_file': filename,
                'message': f'正在处理 {filename}...'
            })

        merger.merge_files(saved_files, output_path, progress_callback)

        # 更新完成状态
        processing_status[task_id].update({
            'status': 'completed',
            'progress': 100,
            'message': '处理完成！'
        })

        # 清理临时文件
        shutil.rmtree(temp_dir)
        
        return jsonify({
            'message': '发票合并成功',
            'download_url': '/download/merged_invoices.pdf',
            'task_id': task_id
        })

    except Exception as e:
        logging.error(f"处理文件时出错: {str(e)}", exc_info=True)
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        
        # 更新错误状态
        if task_id in processing_status:
            processing_status[task_id].update({
                'status': 'error',
                'message': f'处理出错: {str(e)}'
            })
        
        return jsonify({'error': f'处理文件时出错: {str(e)}'}), 500

@app.route('/download/<filename>')
def download_file(filename):
    try:
        return send_file(
            os.path.join(app.config['UPLOAD_FOLDER'], filename),
            as_attachment=True,
            download_name='合并后的发票.pdf'
        )
    except Exception as e:
        logging.error(f"下载文件时出错: {str(e)}", exc_info=True)
        return jsonify({'error': '文件下载失败'}), 404

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': '文件太大，请确保单个文件不超过16MB'}), 413

def cleanup_temp_files():
    """清理临时文件"""
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        shutil.rmtree(app.config['UPLOAD_FOLDER'])

# 确保程序退出时清理临时文件
import atexit
atexit.register(cleanup_temp_files)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=1573)
