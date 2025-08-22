# AI Issue Generator

[![ru](https://img.shields.io/badge/lang-ru-blue.svg)](README-RU.md)

Automatically create GitHub issues from Pull Requests using AI-powered analysis.

## 🚀 Features

- **Automatic Issue Creation**: Creates issues when `@aiissue` is mentioned in PR comments
- **AI-Powered Analysis**: Uses OpenAI GPT to intelligently analyze PR content and generate meaningful issue descriptions
- **Smart Labeling**: Automatically assigns appropriate labels based on available repository labels
- **Assignee Management**: Preserves PR assignees when creating the issue
- **PR Linking**: Automatically links the created issue to the PR with `Closes #XX`
- **Docker Support**: Containerized action for consistent execution

## 📦 Installation

### As a GitHub Action

1. Create `.github/workflows/ai-issue.yml` in your repository:

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

2. Add the `OPENAI_API_KEY` secret to your repository:
   - Go to Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `OPENAI_API_KEY`
   - Value: Your OpenAI API key

## 🎯 Usage

1. Create a Pull Request in your repository
2. Comment `@aiissue` on the PR
3. The action will automatically:
   - Analyze the PR content
   - Generate an appropriate issue description
   - Create the issue with proper labels and assignees
   - Link the issue to the PR

## ⚙️ Configuration

### Action Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `openai_api_key` | OpenAI API key for content generation | Yes | - |
| `github_token` | GitHub token for API access | No | `${{ github.token }}` |

### Action Outputs

| Output | Description |
|--------|-------------|
| `issue_number` | The number of the created issue |
| `issue_url` | The URL of the created issue |

## 🛠️ Development

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) for dependency management

### Local Setup

```bash
# Clone the repository
git clone https://github.com/barabum0/ai-issue.git
cd ai-issue

# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv pip install -e ".[dev]"
```

### Running Tests

```bash
# Run linting
ruff check src/ tests/
ruff format src/ tests/

# Type checking
mypy src/

# Run tests
pytest tests/ -v --cov=src/ai_issue
```

### Docker Build

```bash
# Build the image
docker build -t ai-issue .

# Run the container
docker run -e GITHUB_TOKEN=your_token \
           -e OPENAI_API_KEY=your_key \
           -e GITHUB_EVENT_PATH=/event.json \
           -v $(pwd)/event.json:/event.json \
           ai-issue
```

## 🏗️ Architecture

The project consists of several key components:

- **`models.py`**: Pydantic models for structured data handling
- **`generator.py`**: Core logic for issue generation using OpenAI API
- **`main.py`**: Entry point for GitHub Actions integration
- **`action.yml`**: GitHub Action configuration
- **`Dockerfile`**: Container configuration for consistent execution

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🐛 Bug Reports

If you find a bug or have a suggestion, please [create an issue](https://github.com/barabum0/ai-issue/issues).

## 🙏 Acknowledgments

- Built with [OpenAI API](https://openai.com/api/) for intelligent content generation
- Uses [PyGithub](https://github.com/PyGithub/PyGithub) for GitHub API interaction
- Powered by [uv](https://github.com/astral-sh/uv) for fast Python package management
- Code quality maintained with [ruff](https://github.com/astral-sh/ruff) and [mypy](http://mypy-lang.org/)

## 📊 Project Status

![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-Ready-success)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Docker](https://img.shields.io/badge/Docker-Supported-blue)
![Code Style](https://img.shields.io/badge/Code%20Style-Ruff-000000)
![Type Checked](https://img.shields.io/badge/Type%20Checked-mypy-blue)