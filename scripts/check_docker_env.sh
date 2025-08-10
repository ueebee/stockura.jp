#!/bin/bash
# Docker 環境内の環境変数を確認するスクリプト

echo "======================================================================"
echo "Docker 環境変数確認スクリプト"
echo "======================================================================"

# 各コンテナの環境変数を確認
services=("app" "celery-beat" "celery-worker")

for service in "${services[@]}"; do
    echo ""
    echo "[$service コンテナの環境変数]"
    echo "----------------------------------------------------------------------"
    
    # Redis Sync 関連の環境変数を確認
    docker compose exec -T $service sh -c '
        echo "CELERY_BEAT_REDIS_SYNC_ENABLED: $CELERY_BEAT_REDIS_SYNC_ENABLED"
        echo "CELERY_BEAT_MIN_SYNC_INTERVAL: $CELERY_BEAT_MIN_SYNC_INTERVAL"
        echo "CELERY_BEAT_REDIS_CHANNEL: $CELERY_BEAT_REDIS_CHANNEL"
        echo ""
        echo "REDIS_URL: $REDIS_URL"
        echo "CELERY_BROKER_URL: $CELERY_BROKER_URL"
        echo "CELERY_RESULT_BACKEND: $CELERY_RESULT_BACKEND"
        echo ""
        echo "LOG_LEVEL: $LOG_LEVEL"
        echo "DEBUG: $DEBUG"
    ' 2>/dev/null
    
    if [ $? -ne 0 ]; then
        echo "⚠️  $service コンテナにアクセスできません。起動していることを確認してください。"
    fi
done

echo ""
echo "======================================================================"
echo "Celery Beat のログ確認（最新 20 行）"
echo "======================================================================"
docker compose logs celery-beat --tail=20 2>/dev/null | grep -E "(Redis|sync|schedule|CELERY_BEAT)" || echo "関連するログが見つかりません"

echo ""
echo "======================================================================"
echo "診断完了"
echo "======================================================================"