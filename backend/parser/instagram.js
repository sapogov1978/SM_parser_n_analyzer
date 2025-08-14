// main.js - Главный файл парсера
const puppeteer = require('puppeteer');
const axios = require('axios');

// Модули
const logger = require('./comon_logger');
const InstagramAuth = require('./instagram_auth');
const AccountParser = require('./instagram_account_parser');
const PostsParser = require('./instagram_post_parser');

// Учетные данные Instagram (обязательные переменные окружения)
const INSTAGRAM_USERNAME = process.env.INSTAGRAM_USERNAME;
const INSTAGRAM_PASSWORD = process.env.INSTAGRAM_PASSWORD;

if (!INSTAGRAM_USERNAME || !INSTAGRAM_PASSWORD) {
  logger.error('Ошибка: не заданы INSTAGRAM_USERNAME и/или INSTAGRAM_PASSWORD');
  logger.error('Убедитесь, что переменные окружения настроены правильно');
  process.exit(1);
}

class InstagramParser {
  constructor() {
    this.browser = null;
    this.page = null;
    this.auth = null;
    this.accountParser = null;
    this.postsParser = null;
  }

  async init() {
    try {
      logger.info('Инициализация парсера Instagram...');

      this.browser = await puppeteer.launch({
        headless: true,
        args: [
          '--no-sandbox',
          '--disable-setuid-sandbox',
          '--disable-dev-shm-usage',
          '--disable-web-security',
          '--disable-features=VizDisplayCompositor'
        ]
      });

      this.page = await this.browser.newPage();

      // Устанавливаем User-Agent
      await this.page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36');

      // Инициализируем модули
      this.auth = new InstagramAuth(this.page);
      this.accountParser = new AccountParser(this.page);
      this.postsParser = new PostsParser(this.page);

      logger.success('Парсер успешно инициализирован');
      return true;
    } catch (error) {
      logger.error(`Ошибка инициализации парсера: ${error.message}`);
      return false;
    }
  }

  async getAccountsForParsing(networkId) {
    try {
      const backendUrl = process.env.BACKEND_URL || 'http://backend:8000';

      let url = `${backendUrl}/accounts/for-parsing/`;
      if (networkId) {
        url += `?network_id=${networkId}`;
      }

      logger.info(`Получаем список аккаунтов для парсинга из: ${url}`);

      const { data: accounts } = await axios.get(url);

      logger.success(`Получено ${accounts.length} аккаунтов для обработки`);
      return accounts;
    } catch (error) {
      logger.error(`Ошибка получения списка аккаунтов: ${error.message}`, {
        networkId,
        error: error.response?.data || error.message
      });
      throw error;
    }
  }

  async processAccount(account) {
    try {
      logger.info(`Начинаем обработку аккаунта: ${account.url} (ID: ${account.id})`);

      // Переходим на аккаунт
      const navigationResult = await this.accountParser.navigateToAccount(account.url);
      if (!navigationResult.success) {
        logger.warn(`Пропускаем аккаунт ${account.url}: ${navigationResult.reason}`);
        return { success: false, reason: navigationResult.reason };
      }

      // Сохраняем отладочную информацию
      await this.accountParser.saveDebugInfo(account.id, account.url);

      // Парсим количество подписчиков
      const followers = await this.accountParser.parseFollowers();

      if (followers > 0) {
        await this.accountParser.saveFollowers(account.id, account.network_id, followers);
      }

      // Парсим посты
      const posts = await this.postsParser.scrapeAccountPosts(
        followers,
        account.id,
        account.network_id,
        10 // максимум 10 постов
      );

      if (posts.length > 0) {
        await this.postsParser.savePosts(posts, account.network_id);
      }

      // Отмечаем аккаунт как обработанный
      await this.accountParser.markAccountAsParsed(account.id, account.network_id);

      logger.success(`Аккаунт ${account.url} успешно обработан (${posts.length} постов)`);

      // Пауза между аккаунтами
      await this.delay(10000);

      return {
        success: true,
        followers,
        postsCount: posts.length
      };

    } catch (error) {
      logger.error(`Ошибка обработки аккаунта ${account.url}: ${error.message}`, {
        accountId: account.id,
        accountUrl: account.url,
        networkId: account.network_id,
        error: error.message
      });

      // Сохраняем скриншот ошибки
      try {
        const errorScreenshot = `/app/logs/error-${account.id}-${Date.now()}.png`;
        await this.page.screenshot({ path: errorScreenshot });
        logger.info(`Скриншот ошибки сохранен: ${errorScreenshot}`);
      } catch (e) {
        logger.error('Не удалось сделать скриншот ошибки');
      }

      return { success: false, error: error.message };
    }
  }

  async delay(ms) {
    return new Promise(res => setTimeout(res, ms));
  }

  async run(networkId = null) {
    try {
      logger.info('Запуск парсера Instagram', { networkId });

      // Инициализация
      const initSuccess = await this.init();
      if (!initSuccess) {
        throw new Error('Не удалось инициализировать парсер');
      }

      // Авторизация
      const loginSuccess = await this.auth.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD);
      if (!loginSuccess) {
        throw new Error('Не удалось авторизоваться в Instagram');
      }

      // Получаем список аккаунтов
      const accounts = await this.getAccountsForParsing(networkId);

      if (accounts.length === 0) {
        logger.warn('Нет аккаунтов для обработки');
        return;
      }

      // Обрабатываем каждый аккаунт
      const results = {
        total: accounts.length,
        processed: 0,
        failed: 0,
        totalPosts: 0
      };

      for (let account of accounts) {
        const result = await this.processAccount(account);

        if (result.success) {
          results.processed++;
          results.totalPosts += result.postsCount || 0;
        } else {
          results.failed++;
        }
      }

      logger.success('Парсинг завершен', results);

    } catch (error) {
      logger.error(`Критическая ошибка парсера: ${error.message}`, {
        error: error.message,
        stack: error.stack
      });
    } finally {
      await this.cleanup();
    }
  }

  async cleanup() {
    try {
      if (this.browser) {
        await this.browser.close();
        logger.info('Браузер закрыт');
      }
    } catch (error) {
      logger.error(`Ошибка при закрытии браузера: ${error.message}`);
    }
  }
}

// Запуск парсера
async function main() {
  const parser = new InstagramParser();

  // Получаем network_id из аргументов командной строки или переменных окружения
  const networkId = process.argv[2] || process.env.NETWORK_ID || null;

  if (networkId) {
    logger.info(`Парсер запускается для сети: ${networkId}`);
  } else {
    logger.info('Парсер запускается для всех сетей');
  }

  await parser.run(networkId);
}

// Обработка сигналов для graceful shutdown
process.on('SIGINT', () => {
  logger.info('Получен сигнал SIGINT, завершаем работу...');
  process.exit(0);
});

process.on('SIGTERM', () => {
  logger.info('Получен сигнал SIGTERM, завершаем работу...');
  process.exit(0);
});

main().catch(error => {
  logger.error(`Необработанная ошибка: ${error.message}`, {
    error: error.message,
    stack: error.stack
  });
  process.exit(1);
});