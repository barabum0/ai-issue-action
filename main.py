#!/usr/bin/env python
"""
Модуль для автоматического создания GitHub Issue на основе Pull Request.

При появлении комментария с отметкой "@aiissue" под PR, создаёт issue с описанием задачи,
которую решает данный PR, используя OpenAI API для генерации контента.
"""

import json
import logging
import os
import sys
from typing import List, Optional

import requests
from github import Github
from openai import OpenAI
from pydantic import BaseModel, Field

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IssueContent(BaseModel):
    """Модель для структурированного вывода OpenAI."""
    
    title: str = Field(description="Заголовок issue")
    body: str = Field(description="Описание issue")
    labels: List[str] = Field(description="Список меток для issue")
    issue_type: Optional[str] = Field(description="Тип issue", default=None)


class AIIssueGenerator:
    """Класс для генерации и создания GitHub Issue на основе PR."""
    
    def __init__(
        self,
        github_token: str,
        openai_api_key: str,
        repository: str,
        pr_number: int
    ):
        """
        Инициализация генератора issue.
        
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
        
    def get_available_labels(self) -> List[str]:
        """
        Получить список доступных меток в репозитории.
        
        :return: Список названий меток
        """
        labels = self.repo.get_labels()
        return [label.name for label in labels]
    
    def get_pr_info(self) -> dict:
        """
        Получить информацию о Pull Request.
        
        :return: Словарь с информацией о PR
        """
        return {
            "title": self.pr.title,
            "body": self.pr.body or "",
            "assignees": [assignee.login for assignee in self.pr.assignees],
            "author": self.pr.user.login,
            "created_at": self.pr.created_at.isoformat(),
            "files_changed": self.pr.changed_files,
            "additions": self.pr.additions,
            "deletions": self.pr.deletions
        }
    
    def generate_issue_content(self, pr_info: dict, available_labels: List[str]) -> IssueContent:
        """
        Генерировать содержимое issue с помощью OpenAI.
        
        :param pr_info: Информация о PR
        :param available_labels: Доступные метки
        :return: Объект IssueContent с сгенерированным содержимым
        """
        prompt = f"""
        На основе следующего Pull Request создай описание issue, которое должно быть решено этим PR.
        
        Информация о Pull Request:
        - Заголовок: {pr_info['title']}
        - Описание: {pr_info['body']}
        - Автор: {pr_info['author']}
        - Изменено файлов: {pr_info['files_changed']}
        - Добавлено строк: {pr_info['additions']}
        - Удалено строк: {pr_info['deletions']}
        
        Доступные метки в репозитории: {', '.join(available_labels)}
        
        Создай:
        1. Краткий и информативный заголовок для issue
        2. Подробное описание проблемы или задачи, которую решает этот PR
        3. Выбери подходящие метки из списка доступных
        4. Определи тип issue (например: bug, feature, enhancement, documentation)
        
        Описание должно быть структурированным и включать:
        - Контекст проблемы
        - Что было сделано для решения
        - Почему это важно
        """
        
        try:
            response = self.openai.beta.chat.completions.parse(
                model="gpt-4o-2024-08-06",
                messages=[
                    {"role": "system", "content": "Ты - опытный разработчик, создающий четкие и информативные GitHub issue."},
                    {"role": "user", "content": prompt}
                ],
                response_format=IssueContent,
                temperature=0.7
            )
            
            return response.choices[0].message.parsed
        except Exception as e:
            logger.error(f"Ошибка при генерации содержимого issue: {e}")
            raise
    
    def create_issue(self, issue_content: IssueContent, assignees: List[str]) -> int:
        """
        Создать issue в GitHub.
        
        :param issue_content: Содержимое issue
        :param assignees: Список пользователей для назначения
        :return: ID созданного issue
        """
        try:
            # Создаем issue
            issue = self.repo.create_issue(
                title=issue_content.title,
                body=issue_content.body,
                labels=issue_content.labels,
                assignees=assignees
            )
            
            logger.info(f"Issue #{issue.number} успешно создан")
            return issue.number
            
        except Exception as e:
            logger.error(f"Ошибка при создании issue: {e}")
            raise
    
    def update_pr_description(self, issue_number: int):
        """
        Обновить описание PR, добавив ссылку на созданное issue.
        
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
    
    def process(self):
        """Основной процесс создания issue на основе PR."""
        try:
            logger.info(f"Начинаем обработку PR #{self.pr_number} в репозитории {self.repository}")
            
            # Получаем информацию
            pr_info = self.get_pr_info()
            available_labels = self.get_available_labels()
            
            logger.info("Генерируем содержимое issue с помощью OpenAI...")
            issue_content = self.generate_issue_content(pr_info, available_labels)
            
            logger.info("Создаем issue в GitHub...")
            issue_number = self.create_issue(issue_content, pr_info['assignees'])
            
            logger.info("Обновляем описание PR...")
            self.update_pr_description(issue_number)
            
            logger.info(f"Процесс завершен успешно! Issue #{issue_number} создан и связан с PR #{self.pr_number}")
            
            return issue_number
            
        except Exception as e:
            logger.error(f"Ошибка в процессе обработки: {e}")
            raise


def parse_github_event() -> tuple[str, int, str]:
    """
    Парсить событие GitHub из переменных окружения.
    
    :return: Кортеж (repository, pr_number, comment_body)
    """
    event_path = os.environ.get('GITHUB_EVENT_PATH')
    
    if not event_path:
        raise ValueError("GITHUB_EVENT_PATH не найден")
    
    with open(event_path, 'r') as f:
        event = json.load(f)
    
    # Проверяем, что это комментарий к PR
    if event.get('issue', {}).get('pull_request') is None:
        raise ValueError("Событие не является комментарием к Pull Request")
    
    repository = event['repository']['full_name']
    pr_number = event['issue']['number']
    comment_body = event['comment']['body']
    
    return repository, pr_number, comment_body


def main():
    """Главная функция для запуска из GitHub Actions."""
    try:
        # Получаем данные из окружения
        repository, pr_number, comment_body = parse_github_event()
        
        # Проверяем наличие триггера в комментарии
        if '@aiissue' not in comment_body.lower():
            logger.info("Комментарий не содержит триггер @aiissue, пропускаем")
            return
        
        # Получаем токены
        github_token = os.environ.get('GITHUB_TOKEN')
        openai_api_key = os.environ.get('OPENAI_API_KEY')
        
        if not github_token or not openai_api_key:
            raise ValueError("Необходимые токены не найдены в переменных окружения")
        
        # Создаем генератор и запускаем процесс
        generator = AIIssueGenerator(
            github_token=github_token,
            openai_api_key=openai_api_key,
            repository=repository,
            pr_number=pr_number
        )
        
        issue_number = generator.process()
        
        # Возвращаем номер issue как output для GitHub Actions
        print(f"::set-output name=issue_number::{issue_number}")
        
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()