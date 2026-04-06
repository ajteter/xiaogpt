FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    XIAOGPT_PORT=9527

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

COPY xiaogpt ./xiaogpt
COPY xiaogpt.py .
COPY README.md .
COPY LICENSE .
COPY xiao_config.yaml.example ./xiao_config.yaml.example

VOLUME ["/config"]
EXPOSE 9527

ENTRYPOINT ["python3", "xiaogpt.py"]
CMD ["--config", "/config/xiao_config.yaml"]
