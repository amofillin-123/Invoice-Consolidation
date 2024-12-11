FROM python:3.12.1-slim

# 安装系统依赖和中文字体
RUN apt-get update && apt-get install -y \
    poppler-utils \
    fonts-wqy-zenhei \
    fonts-wqy-microhei \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用程序代码
COPY . .

# 设置环境变量
ENV FLASK_ENV=production
ENV UPLOAD_FOLDER=/tmp/uploads
ENV PYTHONIOENCODING=utf8
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# 创建上传目录并设置权限
RUN mkdir -p /tmp/uploads && chmod 777 /tmp/uploads

# 暴露端口
EXPOSE 8080

# 启动命令
CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]
