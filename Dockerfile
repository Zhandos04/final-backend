FROM python:3.9-alpine

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Устанавливаем зависимости
RUN apk update \
    && apk add postgresql-dev gcc python3-dev musl-dev \
    netcat-openbsd jpeg-dev zlib-dev libjpeg \
    libffi-dev openssl-dev cargo

# Папки для статических и медиа файлов
RUN mkdir -p /app/staticfiles
RUN mkdir -p /app/mediafiles

# Устанавливаем зависимости Python
COPY requirements.txt /app/
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Копируем проект
COPY . /app/

# Даем права на выполнение скрипту
RUN chmod +x /app/entrypoint.sh

# Экспортируем порт (Railway установит свой PORT)
EXPOSE ${PORT:-8000}

# Запускаем entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]