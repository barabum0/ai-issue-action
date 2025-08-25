"""
Тесты для моделей данных.
"""

import pytest
from pydantic import ValidationError

from ai_issue.models import IssueContent, PRInfo


class TestIssueContent:
    """Тесты для модели IssueContent."""

    def test_valid_issue_content(self) -> None:
        """Тест создания валидного IssueContent."""
        issue = IssueContent(
            title="Fix bug in authentication",
            body="This issue addresses authentication problems",
            labels=["bug", "security"],
            issue_type="bug",
        )

        assert issue.title == "Fix bug in authentication"
        assert issue.body == "This issue addresses authentication problems"
        assert issue.labels == ["bug", "security"]
        assert issue.issue_type == "bug"

    def test_issue_content_without_optional_fields(self) -> None:
        """Тест создания IssueContent без опциональных полей."""
        issue = IssueContent(
            title="New feature",
            body="Add new functionality",
        )

        assert issue.title == "New feature"
        assert issue.body == "Add new functionality"
        assert issue.labels == []
        assert issue.issue_type is None

    def test_issue_content_missing_required_fields(self) -> None:
        """Тест валидации при отсутствии обязательных полей."""
        with pytest.raises(ValidationError) as exc_info:
            IssueContent(title="Only title")

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("body",)
        assert errors[0]["type"] == "missing"


class TestPRInfo:
    """Тесты для модели PRInfo."""

    def test_valid_pr_info(self) -> None:
        """Тест создания валидного PRInfo."""
        pr_info = PRInfo(
            title="Add new feature",
            body="This PR adds a new feature",
            assignees=["user1", "user2"],
            author="author1",
            created_at="2024-01-01T00:00:00",
            files_changed=5,
            additions=100,
            deletions=20,
        )

        assert pr_info.title == "Add new feature"
        assert pr_info.body == "This PR adds a new feature"
        assert pr_info.assignees == ["user1", "user2"]
        assert pr_info.author == "author1"
        assert pr_info.created_at == "2024-01-01T00:00:00"
        assert pr_info.files_changed == 5
        assert pr_info.additions == 100
        assert pr_info.deletions == 20

    def test_pr_info_with_defaults(self) -> None:
        """Тест создания PRInfo с значениями по умолчанию."""
        pr_info = PRInfo(
            title="Quick fix",
            author="developer",
            created_at="2024-01-01T00:00:00",
            files_changed=1,
            additions=5,
            deletions=2,
        )

        assert pr_info.title == "Quick fix"
        assert pr_info.body == ""
        assert pr_info.assignees == []
        assert pr_info.author == "developer"

    def test_pr_info_missing_required_fields(self) -> None:
        """Тест валидации при отсутствии обязательных полей."""
        with pytest.raises(ValidationError) as exc_info:
            PRInfo(
                title="Incomplete PR",
                author="dev",
            )

        errors = exc_info.value.errors()
        assert len(errors) == 4  # created_at, files_changed, additions, deletions

        error_fields = {error["loc"][0] for error in errors}
        assert error_fields == {"created_at", "files_changed", "additions", "deletions"}
