"""Генератор GitHub Issue на основе Pull Request с использованием AI."""

import logging

from github import Github
from openai import OpenAI

from .models import IssueContent, PRInfo

logger = logging.getLogger(__name__)


class AIIssueGenerator:
    """Класс для генерации и создания GitHub Issue на основе PR.

    Использует OpenAI API для интеллектуального анализа PR и генерации
    соответствующего issue с правильными метками и описанием.
    """

    def __init__(
        self,
        github_token: str,
        openai_api_key: str,
        repository: str,
        pr_number: int,
    ) -> None:
        """Инициализация генератора issue.

        :param github_token: Токен для доступа к GitHub API
        :param openai_api_key: API ключ OpenAI
        :param repository: Полное имя репозитория (owner/repo)
        :param pr_number: Номер Pull Request
        """
        self.github = Github(github_token)
        self.openai = OpenAI(api_key=openai_api_key)
        self.repository = repository
        self.pr_number = pr_number
        self.repo = self.github.get_repo(repository)
        self.pr = self.repo.get_pull(pr_number)

    def get_available_labels(self) -> list[str]:
        """Получить список доступных меток в репозитории.

        :return: Список названий меток
        """
        labels = self.repo.get_labels()
        return [label.name for label in labels]

    def get_issue_types(self) -> list[str]:
        """Получить список типов issue из меток репозитория.

        Ищет метки, которые могут быть типами issue (bug, feature, enhancement, documentation и т.д.).

        :return: Список типов issue
        """
        # Стандартные типы issue, которые часто используются
        common_types = {
            "bug", "feature", "enhancement", "documentation", "question",
            "help wanted", "wontfix", "duplicate", "invalid", "task",
            "improvement", "refactor", "test", "chore", "breaking change",
            "security", "performance", "dependencies", "ci", "build"
        }

        # Получаем все метки
        all_labels = self.get_available_labels()

        # Фильтруем метки, которые являются типами issue
        issue_types = []
        for label in all_labels:
            label_lower = label.lower()
            # Проверяем, является ли метка типом issue
            if label_lower in common_types or "type:" in label_lower or "kind/" in label_lower:
                issue_types.append(label)

        # Если не нашли специфичных типов, пытаемся найти общие
        if not issue_types:
            for label in all_labels:
                label_lower = label.lower()
                for common_type in common_types:
                    if common_type in label_lower:
                        issue_types.append(label)
                        break

        return issue_types

    def get_pr_info(self) -> PRInfo:
        """Получить информацию о Pull Request.

        :return: Объект PRInfo с информацией о PR
        """
        return PRInfo(
            title=self.pr.title,
            body=self.pr.body or "",
            assignees=[assignee.login for assignee in self.pr.assignees],
            author=self.pr.user.login,
            created_at=self.pr.created_at.isoformat(),
            files_changed=self.pr.changed_files,
            additions=self.pr.additions,
            deletions=self.pr.deletions,
        )

    def generate_issue_content(
        self,
        pr_info: PRInfo,
        available_labels: list[str],
        available_types: list[str],
    ) -> IssueContent:
        """Генерировать содержимое issue с помощью OpenAI.

        :param pr_info: Информация о PR
        :param available_labels: Доступные метки
        :param available_types: Доступные типы issue
        :return: Объект IssueContent с сгенерированным содержимым
        """
        prompt = f"""
        На основе следующего Pull Request создай описание issue, которое должно быть решено этим PR.

        Информация о Pull Request:
        - Заголовок: {pr_info.title}
        - Описание: {pr_info.body}
        - Автор: {pr_info.author}
        - Изменено файлов: {pr_info.files_changed}
        - Добавлено строк: {pr_info.additions}
        - Удалено строк: {pr_info.deletions}

        Доступные метки в репозитории: {", ".join(available_labels) if available_labels else "нет доступных меток"}
        Доступные типы issue: {", ".join(available_types) if available_types else "стандартные: bug, feature, enhancement, documentation"}

        Создай:
        1. Краткий и информативный заголовок для issue
        2. Подробное описание проблемы или задачи, которую решает этот PR
        3. Выбери подходящие метки из списка доступных (только те, что есть в списке!)
        4. Выбери ОДИН наиболее подходящий тип issue из доступных

        Описание должно быть структурированным и включать:
        - Контекст проблемы
        - Что было сделано для решения
        - Почему это важно

        Формат описания: Markdown
        """

        try:
            response = self.openai.beta.chat.completions.parse(
                model="gpt-4o-2024-08-06",
                messages=[
                    {
                        "role": "system",
                        "content": "Ты - опытный разработчик, создающий четкие и информативные GitHub issue.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format=IssueContent,
                temperature=0.7,
            )

            parsed_response = response.choices[0].message.parsed
            if parsed_response is None:
                raise ValueError("OpenAI вернул пустой ответ")

            # Фильтруем метки, оставляя только доступные
            if available_labels:
                parsed_response.labels = [label for label in parsed_response.labels if label in available_labels]

            # Фильтруем тип issue, оставляя только доступный
            if available_types and parsed_response.issue_type and parsed_response.issue_type not in available_types:
                # Если выбранный тип не в списке доступных, пытаемся найти похожий
                parsed_response.issue_type = available_types[0] if available_types else None

            return parsed_response

        except Exception as e:
            logger.error(f"Ошибка при генерации содержимого issue: {e}")
            raise

    def create_issue(
        self,
        issue_content: IssueContent,
        assignees: list[str],
    ) -> int:
        """Создать issue в GitHub.

        :param issue_content: Содержимое issue
        :param assignees: Список пользователей для назначения
        :return: Номер созданного issue
        """
        try:
            # Создаем issue
            issue = self.repo.create_issue(
                title=issue_content.title,
                body=issue_content.body,
                labels=issue_content.labels or [],
                assignees=assignees or [],
            )

            logger.info(f"Issue #{issue.number} успешно создан")
            return issue.number

        except Exception as e:
            logger.error(f"Ошибка при создании issue: {e}")
            raise

    def update_pr_description(self, issue_number: int) -> None:
        """Обновить описание PR, добавив ссылку на созданное issue.

        :param issue_number: Номер созданного issue
        """
        try:
            current_body = self.pr.body or ""

            # Проверяем, не добавлена ли уже ссылка
            if f"#{issue_number}" not in current_body:
                new_body = f"{current_body}\n\nCloses #{issue_number}"
                self.pr.edit(body=new_body)
                logger.info(f"Описание PR обновлено ссылкой на issue #{issue_number}")
            else:
                logger.info(f"Ссылка на issue #{issue_number} уже присутствует в описании PR")

        except Exception as e:
            logger.error(f"Ошибка при обновлении описания PR: {e}")
            raise

    def process(self) -> int:
        """Основной процесс создания issue на основе PR.

        :return: Номер созданного issue
        """
        try:
            logger.info(f"Начинаем обработку PR #{self.pr_number} в репозитории {self.repository}")

            # Получаем информацию
            pr_info = self.get_pr_info()
            available_labels = self.get_available_labels()
            available_types = self.get_issue_types()

            logger.info("Генерируем содержимое issue с помощью OpenAI...")
            issue_content = self.generate_issue_content(pr_info, available_labels, available_types)

            logger.info("Создаем issue в GitHub...")
            issue_number = self.create_issue(issue_content, pr_info.assignees)

            logger.info("Обновляем описание PR...")
            self.update_pr_description(issue_number)

            logger.info(f"Процесс завершен успешно! Issue #{issue_number} создан и связан с PR #{self.pr_number}")

            return issue_number

        except Exception as e:
            logger.error(f"Ошибка в процессе обработки: {e}")
            raise
