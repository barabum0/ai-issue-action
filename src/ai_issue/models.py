"""Модели данных для работы с GitHub и OpenAI API."""

from github.NamedUser import NamedUser
from pydantic import BaseModel, ConfigDict, Field


class IssueContent(BaseModel):
    """Модель для структурированного вывода OpenAI.

    Представляет содержимое issue, которое будет создано в GitHub.
    """

    title: str = Field(description="Заголовок issue")
    body: str = Field(description="Описание issue в markdown формате")
    labels: list[str] = Field(description="Список меток для issue", default_factory=list)
    issue_type: str | None = Field(description="Тип issue (выбрать один из доступных)", default=None)


class PRInfo(BaseModel):
    """Информация о Pull Request.

    Содержит основные данные о PR для анализа.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    title: str = Field(description="Заголовок PR")
    body: str = Field(description="Описание PR", default="")
    assignees: list[NamedUser] = Field(description="Список назначенных пользователей", default_factory=list)
    author: str = Field(description="Автор PR")
    created_at: str = Field(description="Дата создания PR")
    files_changed: int = Field(description="Количество измененных файлов")
    additions: int = Field(description="Количество добавленных строк")
    deletions: int = Field(description="Количество удаленных строк")
