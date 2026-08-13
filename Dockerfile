FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# CPU 환경에서도 import에 필요
RUN pip install --no-cache-dir torch

COPY app ./app