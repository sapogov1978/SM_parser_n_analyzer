FROM python:3.11-slim

# Puppeteer dependencies
RUN apt-get update && apt-get install -y \
    nodejs npm \
    wget libasound2 libatk1.0-0 libc6 libcairo2 \
    libcups2 libdbus-1-3 libexpat1 libfontconfig1 libgcc-s1 \
    libgdk-pixbuf-xlib-2.0-0 libglib2.0-0 libgtk-3-0 \
    libnspr4 libnss3 libpango-1.0-0 libx11-xcb1 libxcb1 \
    libxcomposite1 libxcursor1 libxdamage1 libxext6 \
    libxfixes3 libxi6 libxrandr2 libxrender1 libxss1 \
    libxtst6 xdg-utils \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY backend/parser/package*.json /tmp/parser/
WORKDIR /tmp/parser
RUN npm install

WORKDIR /app
COPY . /app/

RUN cp -r /tmp/parser/node_modules /app/backend/parser/

# Set working directory to backend
WORKDIR /app/backend

ENV PYTHONPATH=/app:/app/backend

EXPOSE 8000

# Run from backend directory
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]