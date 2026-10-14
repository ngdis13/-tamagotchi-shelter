### Отчёт по Лабораторной работе №2 🐳

**Тема:** Контейнеризация сервиса с помощью Docker и Docker Compose

### Введение

В Лабе 0 у нас был живой приют с бэкендом, фронтом и базой, но всё это запускалось руками: где-то питоновский сервер, где-то контейнер с Postgres, где-то ещё что-то. В Лабе 1 мы спрятали это добро за Nginx. А теперь пришло время упаковать весь приют в Docker, чтобы поднимать его одной командой и не зависеть от того, что я случайно забыла запустить.

Смысл лабы — сделать два образа одного и того же сервиса: «плохой» (с кучей bad practices) и «хороший» (где эти практики исправлены), а потом собрать весь стек (бэк + фронт + база) через `docker compose`.

### Часть 1. Плохой Dockerfile

Для начала я специально сделала максимально «неправильный» Dockerfile, чтобы потом было с чем сравнивать. Вот он ([`backend/Dockerfile.bad`](../../backend/Dockerfile.bad)):

```dockerfile
# ПЛОХОЙ Dockerfile
# Намеренно содержит bad practices, чтобы сравнить с хорошим

# BAD PRACTICE 1: плавающий тег latest.
# Версия Python не зафиксирована -> сборка невоспроизводима:
# завтра образ может собраться на другой версии и что-то сломать.
FROM python:latest

WORKDIR /app

# BAD PRACTICE 2: ADD вместо COPY.
# ADD умеет распаковывать архивы и качать по URL — здесь это не нужно,
# а поведение менее предсказуемо, чем у COPY.
#
# BAD PRACTICE 3: копируем ВЕСЬ контекст (ADD . /app).
# В образ уезжают .git, reports/, ssl/nginx.key, auth/htpasswd, __pycache__.
#
# BAD PRACTICE 4: нет .dockerignore, который бы это отфильтровал.
ADD . /app

# Переходим в папку бэкенда, чтобы запускать сервис оттуда.
WORKDIR /app/backend

# BAD PRACTICE 5: код уже скопирован выше, поэтому любая правка main.py
# сбрасывает кеш этого слоя и pip install выполняется заново -> долгая пересборка.
RUN pip install -r requirements.txt

# BAD PRACTICE 6: нет USER -> контейнер работает от root.
# BAD PRACTICE 7: нет HEALTHCHECK -> Docker не знает, жив ли сервис.

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Что здесь не так (разбор bad practices)

1. **`FROM python:latest`** — версия базового образа не зафиксирована. Сегодня это Python 3.15, завтра может быть другая версия, и сборка станет невоспроизводимой.
2. **`ADD` вместо `COPY`** — `ADD` умеет распаковывать архивы и качать файлы по URL. Здесь это не нужно, а поведение менее предсказуемо, чем у честного `COPY`.
3. **`ADD . /app` копирует весь репозиторий** — в образ уезжает всё подряд: `.git`, `reports/`, `check.sh`, `nginx.conf`, `frontend/`, `docs/`, `fake_site/`. Мусор и лишний вес.
4. **Нет `.dockerignore`** — именно он должен был отфильтровать всё лишнее, но его нет.
5. **Код копируется до `pip install`** — любая правка `main.py` сбрасывает кеш слоя, и зависимости ставятся заново. Пересборка долгая.
6. **Нет `USER`** — контейнер работает от `root`, а это лишние права и риск.
7. **Нет `HEALTHCHECK`** — Docker не понимает, жив ли сервис внутри.

### Доказательства, что образ реально плохой

**1. Размер образа — 1.74 GB.** Огромный, потому что базовый `python:latest` жирный, а внутрь залит весь репозиторий.

```bash
docker images tama-backend:bad
```

![Размер плохого образа](./screenshotics/sc_1.png)

**2. Контейнер работает от root.** Никакого отдельного пользователя нет.

```bash
docker run --rm tama-backend:bad whoami
```

![whoami возвращает root](./screenshotics/sc_2.png)

**3. В образ уехал весь репозиторий.** В `/app` лежат `.git`, `reports`, `check.sh`, `nginx.conf`, `frontend`, `docs`, `fake_site` — всё, что не имеет отношения к работе сервиса.

```bash
docker run --rm tama-backend:bad ls -la /app
```

![Внутри образа весь репозиторий](./screenshotics/sc_3.png)

**4. Внутри `.git` с полной историей.** Это самое неприятное: вместе с кодом в образ попала вся история коммитов, а значит и всё, что когда-либо было в репозитории.

```bash
docker run --rm tama-backend:bad sh -c "git -C /app log --oneline | head"
```

![История git внутри образа](./screenshotics/sc_4.png)

**5. Слои образа.** Видно, что слои жирные и их много — образ собирается неэкономно.

```bash
docker history tama-backend:bad
```

![Слои плохого образа](./screenshotics/sc_5.png)

**6. Образ не работает без базы.** При запуске сервис пытается подключиться к PostgreSQL, не находит его и падает с ошибкой `Connection refused`. То есть сам по себе, без окружения, этот образ бесполезен.

```bash
docker run --rm -e DATABASE_URL=postgresql://user:password@localhost:5432/tamagotchi_db tama-backend:bad
```

![Падение без базы данных](./screenshotics/sc_6.png)

### Вывод по плохому образу

Получился классический «антипример»: большой (1.74 GB), запускается от root, тащит в себе весь репозиторий вместе с историей git и не умеет сообщать о своём состоянии. Именно эти проблемы мы и будем исправлять в хорошем Dockerfile.

### Часть 2. Хороший Dockerfile

Теперь исправляем всё, что нашли выше. Вот хороший Dockerfile ([`backend/Dockerfile`](../../backend/Dockerfile)):

```dockerfile
# ХОРОШИЙ Dockerfile
# Здесь исправлены все bad practices из Dockerfile.bad

# сборка зависимостей
# зафиксирована версия базового образа (slim = меньше размер).
FROM python:3.12-slim AS builder

WORKDIR /app

# не кешируем pip-пакеты -> меньше размер образа.
ENV PIP_NO_CACHE_DIR=1

# сначала копируем ТОЛЬКО requirements.txt.
# Пока зависимости не меняются, этот слой берётся из кеша,
# даже если мы правим код -> быстрая пересборка.
COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

# финальный образ 
FROM python:3.12-slim

WORKDIR /app

#переносим только установленные зависимости из стадии сборки.
COPY --from=builder /install /usr/local

# копируем только нужный код, а не весь репозиторий.
COPY main.py .

# создаём отдельного пользователя и запускаемся от него, а не от root.
RUN useradd -m appuser
USER appuser

EXPOSE 8000

#  HEALTHCHECK — Docker сам проверяет, что сервис отвечает.
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/pets')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

И файл [`backend/.dockerignore`](../../backend/.dockerignore), который не пускает в образ мусор и секреты:

```
__pycache__/
*.pyc
*.pyo
*.pyd
.env
*.key
*.crt
*.pem
.git
.gitignore
*.md
Dockerfile.bad
```

### Что именно исправлено

| Было (плохо) | Стало (хорошо) |
|--------------|----------------|
| `FROM python:latest` | `FROM python:3.12-slim` — версия зафиксирована, база лёгкая |
| `ADD . /app` — весь репозиторий | `COPY main.py .` — только нужный код |
| нет `.dockerignore` | есть `backend/.dockerignore` |
| код копируется до `pip install` | сначала `requirements.txt`, потом код — кеш не ломается |
| нет `USER` — root | `USER appuser` — обычный пользователь |
| нет `HEALTHCHECK` | есть `HEALTHCHECK` |
| один этап | multi-stage: зависимости собираются отдельно |

### Доказательства, что образ стал хорошим

**7. Сборка быстрая, контекст крошечный.** В логе видно `transferring context: 460B` (у плохого было 22.34kB), а все слои берутся из кеша — сборка заняла 1.3 секунды.

```bash
docker build -f backend/Dockerfile -t tama-backend:good ./backend
```

![Сборка хорошего образа](./screenshotics/sc_7.png)

**8. Размер уменьшился в 7 раз.** 249 MB против 1.74 GB.

```bash
docker images | grep tama-backend
```

![Сравнение размеров](./screenshotics/sc_8.png)

**9. Контейнер работает от обычного пользователя.**

```bash
docker run --rm tama-backend:good whoami
```

![whoami возвращает appuser](./screenshotics/sc_9.png)

**10. Внутри только нужный код.** В `/app` лежит один `main.py` — никакого `.git`, `reports` и `check.sh`.

```bash
docker run --rm tama-backend:good ls -la /app
```

![Внутри только main.py](./screenshotics/sc_10.png)

**11. Слои тонкие и осмысленные.** Видно `USER appuser`, `HEALTHCHECK` и перенос зависимостей `COPY /install /usr/local` (35.1 MB).

```bash
docker history tama-backend:good
```

![Слои хорошего образа](./screenshotics/sc_11.png)

**12. Кеш работает.** При пересборке плохого образа после правки кода `pip install` выполняется заново (17.1 секунды, всего 20.7 секунды), потому что код копируется до установки зависимостей. У хорошего образа этот слой остаётся в кеше, и пересборка почти мгновенная.

```bash
time docker build -f backend/Dockerfile.bad -t tama-backend:bad .
time docker build -f backend/Dockerfile -t tama-backend:good ./backend
```

![Время пересборки](./screenshotics/sc_12.png)

### Вывод по хорошему образу

Хороший образ получился в 7 раз меньше, запускается от непривилегированного пользователя, содержит только нужный код и умеет сообщать о своём состоянии через `HEALTHCHECK`. А благодаря правильному порядку слоёв пересборка после правки кода стала быстрой.
