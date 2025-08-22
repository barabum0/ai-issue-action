# AI Issue Generator

GitHub Action для автоматического создания issue на основе Pull Request с использованием OpenAI GPT.

## 🚀 Возможности

- Автоматическое создание issue при комментарии с `@aiissue` под PR
- Интеллектуальный анализ PR и генерация описания issue с помощью OpenAI
- Автоматическое назначение меток и типов issue
- Сохранение assignees из PR
- Автоматическая связка PR с созданным issue через `Closes #XX`

## 📦 Установка

### Как GitHub Action в вашем репозитории

1. Создайте файл `.github/workflows/ai-issue.yml`:

```yaml
name: AI Issue Generator

on:
  issue_comment:
    types: [created]

jobs:
  create-issue:
    if: github.event.issue.pull_request != null && contains(github.event.comment.body, '@aiissue')
    runs-on: ubuntu-latest
    
    permissions:
      issues: write
      pull-requests: write
      contents: read
    
    steps:
      - name: Run AI Issue Generator
        uses: barabum0/ai-issue@v1
        with:
          openai_api_key: ${{ secrets.OPENAI_API_KEY }}
```

2. Добавьте секрет `OPENAI_API_KEY` в настройках репозитория:
   - Перейдите в Settings → Secrets and variables → Actions
   - Нажмите "New repository secret"
   - Название: `OPENAI_API_KEY`
   - Значение: ваш API ключ от OpenAI

## 🎯 Использование

1. Создайте Pull Request в вашем репозитории
2. Оставьте комментарий с текстом `@aiissue` под PR
3. Action автоматически:
   - Проанализирует содержимое PR
   - Создаст issue с описанием задачи
   - Назначит подходящие метки и тип
   - Свяжет issue с PR через `Closes #XX`

## ⚙️ Параметры

| Параметр | Описание | Обязательный | По умолчанию |
|----------|----------|--------------|--------------|
| `openai_api_key` | API ключ OpenAI | Да | - |
| `github_token` | GitHub токен для API | Нет | `${{ github.token }}` |

## 📤 Выходные данные

| Параметр | Описание |
|----------|----------|
| `issue_number` | Номер созданного issue |
| `issue_url` | URL созданного issue |

## 🛠️ Локальная разработка

### Требования

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) для управления зависимостями

### Установка для разработки

```bash
# Клонируйте репозиторий
git clone https://github.com/barabum0/ai-issue.git
cd ai-issue

# Установите uv (если еще не установлен)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Установите зависимости
uv pip install -e ".[dev]"
```

### Запуск тестов

```bash
# Линтинг
ruff check src/ tests/
ruff format src/ tests/

# Проверка типов
mypy src/

# Тесты
pytest tests/ -v --cov=src/ai_issue
```

### Docker

```bash
# Сборка образа
docker build -t ai-issue .

# Запуск
docker run -e GITHUB_TOKEN=your_token \
           -e OPENAI_API_KEY=your_key \
           -e GITHUB_EVENT_PATH=/event.json \
           -v $(pwd)/event.json:/event.json \
           ai-issue
```

## 🤝 Вклад в проект

Приветствуются Pull Request'ы! Для больших изменений сначала откройте issue для обсуждения.

## 📄 Лицензия

MIT

## 🐛 Сообщить о проблеме

Если вы нашли баг или у вас есть предложение, создайте [issue](https://github.com/barabum0/ai-issue/issues).