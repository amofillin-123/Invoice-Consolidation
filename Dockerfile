FROM python:3.12.1-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    poppler-utils \
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

# 创建上传目录
RUN mkdir -p /tmp/uploads

# 暴露端口
EXPOSE 8080

# 启动命令
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
