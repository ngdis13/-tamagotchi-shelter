
# ХОРОШИЙ Dockerfile 
# Здесь исправлены все bad practices из Dockerfile.bad

# сборка зависимостей
# GOOD: зафиксирована версия базового образа (slim = меньше размер)
FROM python:3.12-slim AS builder

WORKDIR /app

#  не кешируем pip-пакеты -> меньше размер образа.
ENV PIP_NO_CACHE_DIR=1

# сначала копируем ТОЛЬКО requirements.txt.
# Пока зависимости не меняются, этот слой берётся из кеша,
# даже если мы правим код -> быстрая пересборка
COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

#  финальный образ
FROM python:3.12-slim

WORKDIR /app

# переносим только установленные зависимости из стадии сборки
COPY --from=builder /install /usr/local

# копируем только нужный код, а не весь репозиторий
COPY main.py .

#  создаём отдельного пользователя и запускаемся от него, а не от root
RUN useradd -m appuser
USER appuser

EXPOSE 8000

# HEALTHCHECK — Docker сам проверяет, что сервис отвечает.
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/pets')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
