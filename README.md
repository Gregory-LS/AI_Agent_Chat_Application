# Business Game API

A FastAPI-based backend for a business simulation game where players manage virtual companies, compete in markets, and make strategic decisions.

## Overview

This project provides a RESTful API that powers a business simulation game. Players can create accounts, manage their virtual companies, analyze market conditions, and compete against other players or AI opponents. The API is designed to be extensible and scalable, supporting multiple game modes and real-time updates.

## Features

- User authentication and profile management
- Company management (create, update, view financials)
- Market simulation (supply/demand, pricing, competitors)
- Turn-based decision making
- Leaderboards and statistics
- AI-driven competitors

## Installation

### Prerequisites

- Python 3.9+
- PostgreSQL (optional, SQLite used by default)
- pip

### Setup

1. Clone the repository:
   ```bash
   git clone https://gitlab.com/example/business-game-api.git
   cd business-game-api
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Apply database migrations:
   ```bash
   alembic upgrade head
   ```

5. Start the development server:
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000`. Interactive documentation can be accessed at `http://localhost:8000/docs`.

## Usage

### Creating a user

```bash
curl -X POST "http://localhost:8000/users/" -H "Content-Type: application/json" -d '{"username": "player1", "email": "player1@example.com", "password": "secret"}'
```

### Creating a company

```bash
curl -X POST "http://localhost:8000/companies/" -H "Content-Type: application/json" -d '{"name": "My Startup", "industry": "tech", "initial_capital": 100000}'
```

### Making a decision

```bash
curl -X POST "http://localhost:8000/decisions/" -H "Content-Type: application/json" -d '{"company_id": 1, "action": "invest", "amount": 5000}'
```

### Viewing leaderboard

```bash
curl "http://localhost:8000/leaderboard/"
```

## Project Structure

```
business-game-api/
├── app/
│   ├── main.py            # FastAPI application entry point
│   ├── models/            # SQLAlchemy models
│   ├── schemas/           # Pydantic schemas
│   ├── routers/           # API route handlers
│   ├── services/          # Business logic
│   ├── dependencies.py    # Dependency injection
│   └── database.py        # Database setup
├── tests/                 # Unit and integration tests
├── alembic/               # Database migrations
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

## Testing

Run tests with pytest:

```bash
pytest tests/
```

For coverage report:

```bash
pytest --cov=app tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Merge Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.