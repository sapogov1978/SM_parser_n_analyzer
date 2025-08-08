\# SM\_parser\_n\_analyzer



\*\*Overview:\*\* 
Multi-network social media parser and analyzer with a FastAPI backend and PostgreSQL storage. Puppeteer is used for scraping, and the project is designed to run inside a single container (Puppeteer + FastAPI). It supports collecting posts/metrics, storing them centrally, and performing analytics.



---



\## Features



\- Collect posts and metadata from accounts across multiple social networks.

\- Centralized storage of posts and accounts in PostgreSQL.

\- Centralized logging and metrics.

\- Account ingestion via Telegram bot.

\- Synchronization and account import from Google Sheets.



---



\## Tech Stack



\- Python, FastAPI  

\- Puppeteer (Node.js) — parsers  

\- PostgreSQL  

\- Docker  

\- Git  



---



\## Security Notes



\- \*\*Never\*\* store secrets (Google credentials, tokens, keys) in the repository. Add them to `.gitignore` and use environment variables.



\- Example `.gitignore` entries:



&nbsp; ```gitignore

&nbsp; backend/config/google/\*.json

&nbsp; .env

&nbsp; .secret```
---


\## Running



\- Clone the repository:



```git clone https://github.com/sapogov1978/SM\_parser\_n\_analyzer.git

cd SM\_parser\_n\_analyzer```



\- Start:

&nbsp; - `start.bat` (Windows)

&nbsp; - `docker-compose up -d --build` (Linux)





This will start:



\- backend (FastAPI application)



\- puppeteer (scraping service)



\- db (PostgreSQL)

