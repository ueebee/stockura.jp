# ベースイメージ
FROM python:3.12-bookworm AS base

WORKDIR /usr/src/app

# 本番用ステージ
FROM base AS production
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# テスト用ステージ
FROM base AS test
COPY requirements.txt requirements-test.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-test.txt
COPY . .
CMD ["pytest", "-v"] 