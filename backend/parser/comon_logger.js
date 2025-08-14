// logger.js
const fs = require('fs');
const path = require('path');

class Logger {
  constructor(logDir = '/app/logs') {
    this.logDir = logDir;
    this.ensureLogDir();
  }

  ensureLogDir() {
    if (!fs.existsSync(this.logDir)) {
      fs.mkdirSync(this.logDir, { recursive: true });
    }
  }

  formatMessage(level, message, extra = {}) {
    const timestamp = new Date().toISOString();
    const logEntry = {
      timestamp,
      level,
      message,
      service: 'instagram-parser',
      ...extra
    };
    return JSON.stringify(logEntry);
  }

  writeToFile(level, message, extra = {}) {
    const logFile = path.join(this.logDir, 'parser.log');
    const formattedMessage = this.formatMessage(level, message, extra);

    try {
      fs.appendFileSync(logFile, formattedMessage + '\n');
    } catch (error) {
      console.error('Failed to write to log file:', error.message);
    }
  }

  info(message, extra = {}) {
    const logMessage = `ℹ️ ${message}`;
    console.log(logMessage);
    this.writeToFile('INFO', message, extra);
  }

  error(message, extra = {}) {
    const logMessage = `❌ ${message}`;
    console.error(logMessage);
    this.writeToFile('ERROR', message, extra);
  }

  warn(message, extra = {}) {
    const logMessage = `⚠️ ${message}`;
    console.warn(logMessage);
    this.writeToFile('WARN', message, extra);
  }

  success(message, extra = {}) {
    const logMessage = `✅ ${message}`;
    console.log(logMessage);
    this.writeToFile('SUCCESS', message, extra);
  }

  debug(message, extra = {}) {
    if (process.env.DEBUG === 'true') {
      const logMessage = `🐛 ${message}`;
      console.log(logMessage);
      this.writeToFile('DEBUG', message, extra);
    }
  }
}

module.exports = new Logger();