FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы проекта
COPY pyproject.toml .
COPY src/ ./src/

# Устанавливаем зависимости с помощью uv
RUN uv pip install --system -e .

# Запускаем приложение
ENTRYPOINT ["python", "-m", "ai_issue.main"]