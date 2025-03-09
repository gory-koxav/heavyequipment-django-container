#!/bin/sh

# DB 비밀번호 파일이 있는 경우 처리
if [ -n "$DJANGO_POSTGRES_PASSWORD_FILE" ] && [ -f "$DJANGO_POSTGRES_PASSWORD_FILE" ]; then
    export DJANGO_POSTGRES_PASSWORD=$(cat $DJANGO_POSTGRES_PASSWORD_FILE)
    echo "PostgreSQL password loaded from file"
fi

# DB 연결 대기
echo "Waiting for PostgreSQL..."
while ! nc -z $DJANGO_POSTGRES_SERVER 5432; do
    sleep 1
done
echo "PostgreSQL is up"

# InfluxDB 연결 대기
echo "Waiting for InfluxDB..."
while ! nc -z $(echo $DJANGO_INFLUXDB_URL | sed 's|http://||' | sed 's|:.*||') 8086; do
    sleep 1
done
echo "InfluxDB is up"

# 마이그레이션 수행
echo "Applying database migrations..."
python manage.py migrate

# 정적 파일 수집 (선택 사항)
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Gunicorn 실행
echo "Starting Gunicorn..."
exec gunicorn myproject.wsgi:application --bind 0.0.0.0:8000