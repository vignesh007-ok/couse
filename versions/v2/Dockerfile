FROM python:3.12-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN addgroup -S app && adduser -S -G app -u 10001 app

COPY requirements.txt .
RUN pip install --no-cache-dir --no-compile -r requirements.txt
COPY --chown=app:app versions/v2/app.py /app/app.py

USER 10001:100
EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "4", "--timeout", "30", "app:app"]
