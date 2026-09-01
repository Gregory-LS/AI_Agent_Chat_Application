# Project Title

## Overview

This project is a multi-agent software development workflow system. It uses GitLab issues to assign tickets to worker agents, who then complete the tasks and submit merge requests for review by an orchestrator agent.

## Requirements

- Python 3.8+
- GitLab account with API access
- `python-gitlab` library (for GitLab API interactions)
- `pytest` (for running tests)

## Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Install the required Python packages:

   ```bash
   pip install -r requirements.txt
   ```

3. Set up your GitLab API token and project ID as environment variables:

   ```bash
   export GITLAB_TOKEN=<your-token>
   export GITLAB_PROJECT_ID=<your-project-id>
   ```

## Usage

To run the worker agent:

```bash
python worker.py
```

The worker will fetch the next open ticket assigned to it, complete the task, and create a merge request with the changes.

## Testing

Run the tests using pytest:

```bash
pytest tests/
```

## Project Structure

```
.
├── README.md
├── requirements.txt
├── worker.py
├── tests/
│   └── test_worker.py
└── .gitlab-ci.yml
```

## Contributing

Please follow the standard GitLab workflow: create a branch, make your changes, and submit a merge request for review.
