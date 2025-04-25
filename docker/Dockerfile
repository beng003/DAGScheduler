# 根目录执行
# docker build -f docker/Dockerfile -t your-image-name .

FROM python:3.10-slim
# 更新并安装 libgomp 以及 gcc 
RUN apt-get update && apt-get install -y libgomp1 gcc && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
COPY . .
EXPOSE 9099
CMD ["python3", "app.py", "--env=docker"]