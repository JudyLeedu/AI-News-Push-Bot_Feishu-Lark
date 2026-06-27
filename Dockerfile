FROM python:3.12-slim

# 禁用 Python 缓冲以实时查看日志，并设置默认系统时区
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Shanghai

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制源码
COPY src/ ./src/

# 创建日志目录
RUN mkdir -p logs

CMD ["python", "-m", "src.main", "scheduler"]
