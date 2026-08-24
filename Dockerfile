FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# CPU 환경에서 PyTorch 코드 import에 필요
RUN pip install --no-cache-dir \
    torch==2.12.1 \
    --index-url https://download.pytorch.org/whl/cpu

COPY app ./app