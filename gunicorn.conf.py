import multiprocessing

# 工作进程数
workers = multiprocessing.cpu_count() * 2 + 1

# 工作模式
worker_class = 'sync'

# 超时设置
timeout = 300  # 5分钟
graceful_timeout = 300

# 日志设置
loglevel = 'info'
accesslog = '-'
errorlog = '-'

# 绑定
bind = '0.0.0.0:8080'

# 限制请求大小（100MB）
limit_request_line = 0
limit_request_field_size = 0
limit_request_fields = 0
