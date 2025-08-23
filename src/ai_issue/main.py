#!/usr/bin/env python
"""Главный модуль для запуска AI Issue Generator из GitHub Actions."""

import json
import logging
import os
import sys
from pathlib import Path

from .generator import AIIssueGenerator

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def parse_github_event() -> tuple[str, int, str]:
    """Парсить событие GitHub из переменных окружения.

    :return: Кортеж (repository, pr_number, comment_body)
    :raises ValueError: Если событие не является комментарием к PR
    """
    event_path = os.environ.get("GITHUB_EVENT_PATH")

    if not event_path:
        raise ValueError("GITHUB_EVENT_PATH не найден в переменных окружения")

    event_file = Path(event_path)
    if not event_file.exists():
        raise ValueError(f"Файл события не найден: {event_path}")

    with event_file.open("r", encoding="utf-8") as f:
        event = json.load(f)

    # Проверяем, что это комментарий к PR
    if not event.get("issue", {}).get("pull_request"):
        raise ValueError("Событие не является комментарием к Pull Request")

    repository = event["repository"]["full_name"]
    pr_number = event["issue"]["number"]
    comment_body = event["comment"]["body"]

    return repository, pr_number, comment_body


def set_github_output(name: str, value: str) -> None:
    """Установить output для GitHub Actions.

    :param name: Имя переменной
    :param value: Значение переменной
    """
    github_output = os.environ.get("GITHUB_OUTPUT")

    if github_output:
        # Новый способ для GitHub Actions
        with Path(github_output).open("a", encoding="utf-8") as f:
            f.write(f"{name}={value}\n")
    else:
        # Старый способ (deprecated, но оставляем для совместимости)
        print(f"::set-output name={name}::{value}")


def main() -> None:
    """Главная функция для запуска из GitHub Actions."""
    try:
        # Получаем данные из окружения
        repository, pr_number, comment_body = parse_github_event()

        # Проверяем наличие триггера в комментарии
        if "@aiissue" not in comment_body.lower():
            logger.info("Комментарий не содержит триггер @aiissue, пропускаем")
            sys.exit(0)

        # Получаем токены из окружения или входных параметров
        github_token = os.environ.get("GITHUB_TOKEN")
        if not github_token:
            github_token = os.environ.get("INPUT_GITHUB_TOKEN")

        openai_api_key = os.environ.get("INPUT_OPENAI_API_KEY")
        if not openai_api_key:
            openai_api_key = os.environ.get("OPENAI_API_KEY")

        if not github_token:
            raise ValueError("GitHub токен не найден. Установите GITHUB_TOKEN или передайте github_token")

        if not openai_api_key:
            raise ValueError("OpenAI API ключ не найден. Установите OPENAI_API_KEY или передайте openai_api_key")

        # Создаем генератор и запускаем процесс
        generator = AIIssueGenerator(
            github_token=github_token,
            openai_api_key=openai_api_key,
            repository=repository,
            pr_number=pr_number,
        )

        issue_number = generator.process()

        # Возвращаем номер issue как output для GitHub Actions
        set_github_output("issue_number", str(issue_number))
        set_github_output("issue_url", f"https://github.com/{repository}/issues/{issue_number}")

        logger.info(f"Issue создан: https://github.com/{repository}/issues/{issue_number}")

    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
