"""Генератор GitHub Issue на основе Pull Request с использованием AI."""

import logging

from github import Github
from github.Issue import Issue
from github.NamedUser import NamedUser
from openai import OpenAI

from .models import IssueContent, PRInfo

logger = logging.getLogger(__name__)
NEXT_LINE = "\n"


class AIIssueGenerator:
    """Класс для генерации и создания GitHub Issue на основе PR."""

    def __init__(self, github_token: str, openai_api_key: str, repository: str, pr_number: int):
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

    def get_available_labels(self) -> list[tuple[str, str]]:
        """Получить список доступных меток в репозитории.

        :return: Список названий и описаний меток
        """
        labels = self.repo.get_labels()
        return [(label.name, label.description) for label in labels]

    def get_available_issue_types(self) -> list[tuple[str, str]]:
        """Получить список доступных типов Issue.

        :return: Список названий и описаний типов
        """
        _, data = self.github.requester.requestJsonAndCheck("GET", f"/orgs/{self.repo.organization.login}/issue-types")
        return [(t.get("name"), t.get("description")) for t in data]

    def get_pr_info(self) -> PRInfo:
        """Получить информацию о Pull Request.

        :return: Объект PRInfo с информацией о PR
        """
        return PRInfo(
            title=self.pr.title,
            body=self.pr.body or "",
            assignees=self.pr.assignees,
            author=self.pr.user.login,
            created_at=self.pr.created_at.isoformat(),
            files_changed=self.pr.changed_files,
            additions=self.pr.additions,
            deletions=self.pr.deletions,
        )

    def generate_issue_content(
        self,
        pr_info: PRInfo,
        available_labels: list[tuple[str, str]],
        available_types: list[tuple[str, str]],
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

        Доступные метки issue в репозитории:
        {NEXT_LINE.join(f"- {title}{NEXT_LINE}Описание метки: {desc}" for title, desc in available_labels)}

        Доступные типы issue в репозитории:
        {NEXT_LINE.join(f"- {title}{NEXT_LINE}Описание типа: {desc}" for title, desc in available_types)}

        Создай:
        1. Краткий и информативный заголовок для issue
        2. Подробное описание проблемы или задачи, которую решает этот PR
        3. Выбери подходящие метки из списка доступных
        4. Выбери подходящий тип issue из списка доступных

        Описание должно быть структурированным и включать:
        - Контекст проблемы
        - Почему это важно
        """

        try:
            response = self.openai.responses.parse(
                model="gpt-5",
                instructions="Ты - опытный разработчик, создающий четкие и информативные GitHub issue.",
                input=prompt,
                text_format=IssueContent,
                temperature=0.7,
            )
            assert response.output_parsed is not None
            return response.output_parsed
        except Exception as e:
            logger.error(f"Ошибка при генерации содержимого issue: {e}")
            raise

    def create_issue(self, issue_content: IssueContent, assignees: list[NamedUser]) -> int:
        """Создать issue в GitHub.

        :param issue_content: Содержимое issue
        :param assignees: Список пользователей для назначения
        :return: ID созданного issue
        """
        try:
            # Создаем issue
            headers, data = self.github.requester.requestJsonAndCheck(
                "POST",
                f"{self.repo.url}/issues",
                input={
                    "title": issue_content.title,
                    "body": issue_content.body,
                    "labels": issue_content.labels,
                    "type": issue_content.issue_type,
                    "assignees": [element.login for element in assignees],
                },
            )
            issue = Issue(self.github.requester, headers, data, completed=True)

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
            new_body = f"{current_body}\n\nCloses #{issue_number}"

            self.pr.edit(body=new_body)
            logger.info(f"Описание PR обновлено ссылкой на issue #{issue_number}")

        except Exception as e:
            logger.error(f"Ошибка при обновлении описания PR: {e}")
            raise

    def process(self) -> int:
        """Основной процесс создания issue на основе PR."""
        try:
            logger.info(f"Начинаем обработку PR #{self.pr_number} в репозитории {self.repository}")

            # Получаем информацию
            pr_info = self.get_pr_info()
            available_labels = self.get_available_labels()
            available_types = self.get_available_issue_types()

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
