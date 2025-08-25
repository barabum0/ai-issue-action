"""
Тесты для генератора issue.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from ai_issue.generator import AIIssueGenerator
from ai_issue.models import IssueContent, PRInfo


@pytest.fixture
def mock_github() -> Mock:
    """Мок для GitHub API."""
    mock = MagicMock()

    # Мок для PR
    mock_pr = MagicMock()
    mock_pr.title = "Test PR"
    mock_pr.body = "Test PR description"
    mock_pr.assignees = []
    mock_pr.user.login = "test_user"
    mock_pr.created_at.isoformat.return_value = "2024-01-01T00:00:00"
    mock_pr.changed_files = 3
    mock_pr.additions = 50
    mock_pr.deletions = 10
    mock_pr.number = 123

    # Мок для репозитория
    mock_repo = MagicMock()
    mock_repo.get_pull.return_value = mock_pr
    mock_repo.get_labels.return_value = [
        MagicMock(name="bug"),
        MagicMock(name="feature"),
        MagicMock(name="enhancement"),
    ]

    # Мок для созданного issue
    mock_issue = MagicMock()
    mock_issue.number = 456
    mock_repo.create_issue.return_value = mock_issue

    mock.get_repo.return_value = mock_repo

    return mock


@pytest.fixture
def mock_openai() -> Mock:
    """Мок для OpenAI API."""
    mock = MagicMock()

    # Мок для ответа OpenAI
    mock_response = MagicMock()
    mock_response.choices[0].message.parsed = IssueContent(
        title="Generated Issue Title",
        body="Generated issue body",
        labels=["bug"],
        issue_type="bug",
    )

    mock.beta.chat.completions.parse.return_value = mock_response

    return mock


class TestAIIssueGenerator:
    """Тесты для класса AIIssueGenerator."""

    @patch("ai_issue.generator.Github")
    @patch("ai_issue.generator.OpenAI")
    def test_initialization(
        self,
        mock_openai_class: Mock,
        mock_github_class: Mock,
        mock_github: Mock,
        mock_openai: Mock,
    ) -> None:
        """Тест инициализации генератора."""
        mock_github_class.return_value = mock_github
        mock_openai_class.return_value = mock_openai

        generator = AIIssueGenerator(
            github_token="test_token",
            openai_api_key="test_api_key",
            repository="owner/repo",
            pr_number=123,
        )

        assert generator.repository == "owner/repo"
        assert generator.pr_number == 123
        mock_github_class.assert_called_once_with("test_token")
        mock_openai_class.assert_called_once_with(api_key="test_api_key")

    @patch("ai_issue.generator.Github")
    @patch("ai_issue.generator.OpenAI")
    def test_get_available_labels(
        self,
        mock_openai_class: Mock,
        mock_github_class: Mock,
        mock_github: Mock,
        mock_openai: Mock,
    ) -> None:
        """Тест получения доступных меток."""
        mock_github_class.return_value = mock_github
        mock_openai_class.return_value = mock_openai

        generator = AIIssueGenerator(
            github_token="test_token",
            openai_api_key="test_api_key",
            repository="owner/repo",
            pr_number=123,
        )

        labels = generator.get_available_labels()

        assert labels == ["bug", "feature", "enhancement"]

    @patch("ai_issue.generator.Github")
    @patch("ai_issue.generator.OpenAI")
    def test_get_pr_info(
        self,
        mock_openai_class: Mock,
        mock_github_class: Mock,
        mock_github: Mock,
        mock_openai: Mock,
    ) -> None:
        """Тест получения информации о PR."""
        mock_github_class.return_value = mock_github
        mock_openai_class.return_value = mock_openai

        generator = AIIssueGenerator(
            github_token="test_token",
            openai_api_key="test_api_key",
            repository="owner/repo",
            pr_number=123,
        )

        pr_info = generator.get_pr_info()

        assert isinstance(pr_info, PRInfo)
        assert pr_info.title == "Test PR"
        assert pr_info.body == "Test PR description"
        assert pr_info.author == "test_user"
        assert pr_info.files_changed == 3
        assert pr_info.additions == 50
        assert pr_info.deletions == 10

    @patch("ai_issue.generator.Github")
    @patch("ai_issue.generator.OpenAI")
    def test_generate_issue_content(
        self,
        mock_openai_class: Mock,
        mock_github_class: Mock,
        mock_github: Mock,
        mock_openai: Mock,
    ) -> None:
        """Тест генерации содержимого issue."""
        mock_github_class.return_value = mock_github
        mock_openai_class.return_value = mock_openai

        generator = AIIssueGenerator(
            github_token="test_token",
            openai_api_key="test_api_key",
            repository="owner/repo",
            pr_number=123,
        )

        pr_info = PRInfo(
            title="Test PR",
            body="Test description",
            author="test_user",
            created_at="2024-01-01T00:00:00",
            files_changed=3,
            additions=50,
            deletions=10,
        )

        issue_content = generator.generate_issue_content(
            pr_info=pr_info,
            available_labels=["bug", "feature"],
            available_types=["bug", "feature", "enhancement"],
        )

        assert isinstance(issue_content, IssueContent)
        assert issue_content.title == "Generated Issue Title"
        assert issue_content.body == "Generated issue body"
        assert issue_content.labels == ["bug"]
        assert issue_content.issue_type == "bug"

    @patch("ai_issue.generator.Github")
    @patch("ai_issue.generator.OpenAI")
    def test_create_issue(
        self,
        mock_openai_class: Mock,
        mock_github_class: Mock,
        mock_github: Mock,
        mock_openai: Mock,
    ) -> None:
        """Тест создания issue в GitHub."""
        mock_github_class.return_value = mock_github
        mock_openai_class.return_value = mock_openai

        generator = AIIssueGenerator(
            github_token="test_token",
            openai_api_key="test_api_key",
            repository="owner/repo",
            pr_number=123,
        )

        issue_content = IssueContent(
            title="Test Issue",
            body="Test issue body",
            labels=["bug"],
            issue_type="bug",
        )

        issue_number = generator.create_issue(
            issue_content=issue_content,
            assignees=["user1", "user2"],
        )

        assert issue_number == 456
        generator.repo.create_issue.assert_called_once_with(
            title="Test Issue",
            body="Test issue body",
            labels=["bug"],  # Метка bug уже содержит тип, не дублируем
            assignees=["user1", "user2"],
        )

    @patch("ai_issue.generator.Github")
    @patch("ai_issue.generator.OpenAI")
    def test_create_issue_with_different_type(
        self,
        mock_openai_class: Mock,
        mock_github_class: Mock,
        mock_github: Mock,
        mock_openai: Mock,
    ) -> None:
        """Тест создания issue когда тип отличается от меток."""
        mock_github_class.return_value = mock_github
        mock_openai_class.return_value = mock_openai

        generator = AIIssueGenerator(
            github_token="test_token",
            openai_api_key="test_api_key",
            repository="owner/repo",
            pr_number=123,
        )

        issue_content = IssueContent(
            title="New Feature",
            body="Feature description",
            labels=["documentation", "help wanted"],
            issue_type="feature",
        )

        issue_number = generator.create_issue(
            issue_content=issue_content,
            assignees=["user1"],
        )

        assert issue_number == 456
        generator.repo.create_issue.assert_called_once_with(
            title="New Feature",
            body="Feature description",
            labels=["documentation", "help wanted", "feature"],  # Тип добавлен к меткам
            assignees=["user1"],
        )

    @patch("ai_issue.generator.Github")
    @patch("ai_issue.generator.OpenAI")
    def test_update_pr_description(
        self,
        mock_openai_class: Mock,
        mock_github_class: Mock,
        mock_github: Mock,
        mock_openai: Mock,
    ) -> None:
        """Тест обновления описания PR."""
        mock_github_class.return_value = mock_github
        mock_openai_class.return_value = mock_openai

        generator = AIIssueGenerator(
            github_token="test_token",
            openai_api_key="test_api_key",
            repository="owner/repo",
            pr_number=123,
        )

        generator.update_pr_description(issue_number=456)

        generator.pr.edit.assert_called_once()
        call_args = generator.pr.edit.call_args
        assert "Closes #456" in call_args[1]["body"]

    @patch("ai_issue.generator.Github")
    @patch("ai_issue.generator.OpenAI")
    def test_process_full_flow(
        self,
        mock_openai_class: Mock,
        mock_github_class: Mock,
        mock_github: Mock,
        mock_openai: Mock,
    ) -> None:
        """Тест полного процесса создания issue."""
        mock_github_class.return_value = mock_github
        mock_openai_class.return_value = mock_openai

        generator = AIIssueGenerator(
            github_token="test_token",
            openai_api_key="test_api_key",
            repository="owner/repo",
            pr_number=123,
        )

        issue_number = generator.process()

        assert issue_number == 456

        # Проверяем, что все методы были вызваны
        generator.repo.get_labels.assert_called()
        mock_openai.beta.chat.completions.parse.assert_called_once()
        generator.repo.create_issue.assert_called_once()
        generator.pr.edit.assert_called_once()
