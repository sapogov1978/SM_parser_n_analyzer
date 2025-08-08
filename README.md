# SM_parser_n_analyzer

**Overview:** 

Multi-network social media parser and analyzer with a FastAPI backend and PostgreSQL storage. Puppeteer is used for scraping, and the project is designed to run inside a single container (Puppeteer + FastAPI). It supports collecting posts/metrics, storing them centrally, and performing analytics.

---

## Features

- Collect posts and metadata from accounts across multiple social networks.
- Centralized storage of posts and accounts in PostgreSQL.
- Centralized logging and metrics.
- Account ingestion via Telegram bot (https://github.com/sapogov1978/Links-Collection-Telegram-Bot).
- Synchronization and account import from Google Sheets.

---

## Tech Stack

- Python, FastAPI  
- Puppeteer (Node.js) — parsers  
- PostgreSQL  
- Docker  
- Git  

---

## Security Notes

- **Never** store secrets (Google credentials, tokens, keys) in the repository. Add them to `.gitignore` and use environment variables.

- Example `.gitignore` entries:
```
backend/config/google/\*.json
.env
.secret
```

---

## Running

- Clone the repository:
```
git clone https://github.com/sapogov1978/SM\_parser\_n\_analyzer.git
cd SM\_parser\_n\_analyzer
```

- Start:
    - `start.bat` (Windows)
    - `docker-compose up -d --build` (Linux)

This will start:
- backend (FastAPI application)
- puppeteer (scraping service)
- db (PostgreSQL)

