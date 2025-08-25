"""
Тесты для главного модуля.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from ai_issue.main import main, parse_github_event, set_github_output


class TestParseGithubEvent:
    """Тесты для функции parse_github_event."""

    def test_parse_valid_pr_comment_event(self) -> None:
        """Тест парсинга валидного события комментария к PR."""
        event_data = {
            "issue": {
                "number": 123,
                "pull_request": {"url": "https://api.github.com/repos/owner/repo/pulls/123"},
            },
            "comment": {
                "body": "Please @aiissue create an issue for this",
            },
            "repository": {
                "full_name": "owner/repo",
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(event_data, f)
            temp_path = f.name

        try:
            with patch.dict(os.environ, {"GITHUB_EVENT_PATH": temp_path}):
                repository, pr_number, comment_body = parse_github_event()

            assert repository == "owner/repo"
            assert pr_number == 123
            assert comment_body == "Please @aiissue create an issue for this"
        finally:
            Path(temp_path).unlink()

    def test_parse_event_not_pr_comment(self) -> None:
        """Тест парсинга события, которое не является комментарием к PR."""
        event_data = {
            "issue": {
                "number": 123,
                # Отсутствует поле pull_request
            },
            "comment": {
                "body": "@aiissue",
            },
            "repository": {
                "full_name": "owner/repo",
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(event_data, f)
            temp_path = f.name

        try:
            with patch.dict(os.environ, {"GITHUB_EVENT_PATH": temp_path}), pytest.raises(ValueError, match="не является комментарием к Pull Request"):
                parse_github_event()
        finally:
            Path(temp_path).unlink()

    def test_parse_event_no_path(self) -> None:
        """Тест парсинга когда GITHUB_EVENT_PATH не установлен."""
        with patch.dict(os.environ, {}, clear=True), pytest.raises(ValueError, match="GITHUB_EVENT_PATH не найден"):
            parse_github_event()

    def test_parse_event_file_not_found(self) -> None:
        """Тест парсинга когда файл события не существует."""
        with patch.dict(os.environ, {"GITHUB_EVENT_PATH": "/nonexistent/path.json"}), pytest.raises(ValueError, match="Файл события не найден"):
            parse_github_event()


class TestSetGithubOutput:
    """Тесты для функции set_github_output."""

    def test_set_output_with_github_output_env(self) -> None:
        """Тест установки output через GITHUB_OUTPUT."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            temp_path = f.name

        try:
            with patch.dict(os.environ, {"GITHUB_OUTPUT": temp_path}):
                set_github_output("issue_number", "123")

            with Path(temp_path).open() as f:
                content = f.read()

            assert "issue_number=123\n" in content
        finally:
            Path(temp_path).unlink()

    def test_set_output_legacy_method(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Тест установки output через старый метод."""
        with patch.dict(os.environ, {}, clear=True):
            set_github_output("issue_number", "456")

        captured = capsys.readouterr()
        assert "::set-output name=issue_number::456" in captured.out


class TestMain:
    """Тесты для главной функции main."""

    @patch("ai_issue.main.AIIssueGenerator")
    @patch("ai_issue.main.parse_github_event")
    @patch("ai_issue.main.set_github_output")
    def test_main_successful_flow(
        self,
        mock_set_output: Mock,
        mock_parse_event: Mock,
        mock_generator_class: Mock,
    ) -> None:
        """Тест успешного выполнения main."""
        # Настройка моков
        mock_parse_event.return_value = ("owner/repo", 123, "Please @aiissue create issue")

        mock_generator = MagicMock()
        mock_generator.process.return_value = 456
        mock_generator_class.return_value = mock_generator

        # Запуск с необходимыми переменными окружения
        with patch.dict(
            os.environ,
            {
                "GITHUB_TOKEN": "test_github_token",
                "INPUT_OPENAI_API_KEY": "test_openai_key",
            },
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 0

        # Проверка вызовов
        mock_generator_class.assert_called_once_with(
            github_token="test_github_token",
            openai_api_key="test_openai_key",
            repository="owner/repo",
            pr_number=123,
        )

        mock_generator.process.assert_called_once()

        # Проверка установки outputs
        assert mock_set_output.call_count == 2
        mock_set_output.assert_any_call("issue_number", "456")
        mock_set_output.assert_any_call("issue_url", "https://github.com/owner/repo/issues/456")

    @patch("ai_issue.main.parse_github_event")
    def test_main_no_trigger_in_comment(
        self,
        mock_parse_event: Mock,
    ) -> None:
        """Тест когда комментарий не содержит триггер."""
        mock_parse_event.return_value = ("owner/repo", 123, "Regular comment without trigger")

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0

    @patch("ai_issue.main.parse_github_event")
    def test_main_missing_tokens(
        self,
        mock_parse_event: Mock,
    ) -> None:
        """Тест когда отсутствуют необходимые токены."""
        mock_parse_event.return_value = ("owner/repo", 123, "@aiissue create issue")

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

    @patch("ai_issue.main.AIIssueGenerator")
    @patch("ai_issue.main.parse_github_event")
    def test_main_generator_error(
        self,
        mock_parse_event: Mock,
        mock_generator_class: Mock,
    ) -> None:
        """Тест обработки ошибки в генераторе."""
        mock_parse_event.return_value = ("owner/repo", 123, "@aiissue create issue")

        mock_generator = MagicMock()
        mock_generator.process.side_effect = Exception("API Error")
        mock_generator_class.return_value = mock_generator

        with patch.dict(
            os.environ,
            {
                "GITHUB_TOKEN": "test_github_token",
                "INPUT_OPENAI_API_KEY": "test_openai_key",
            },
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1
