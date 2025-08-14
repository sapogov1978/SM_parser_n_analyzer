// accountParser.js
const logger = require('./comon_logger');
const axios = require('axios');

class AccountParser {
  constructor(page) {
    this.page = page;
  }

  async delay(ms) {
    return new Promise(res => setTimeout(res, ms));
  }

  async parseFollowers() {
    try {
      logger.info('Начинаем парсинг количества подписчиков');

      // Множественные селекторы для поиска количества подписчиков
      const selectors = [
        'header section ul li:nth-child(2) a span',
        'header section ul li:nth-child(2) span',
        'a[href$="/followers/"] span',
        'span[title*="follower"]',
        'span[title*="подписчик"]',
        'header section div a:nth-child(2) span'
      ];

      let followers = 0;

      for (let selector of selectors) {
        try {
          const element = await this.page.$(selector);
          if (element) {
            const text = await element.evaluate(el =>
              el.getAttribute('title') || el.innerText || el.textContent
            );

            if (text) {
              // Обрабатываем форматы: "1,234", "1.2k", "1.2m"
              const cleanText = text.toLowerCase().replace(/[^\d.,km]/g, '');
              if (cleanText.includes('k')) {
                followers = Math.round(parseFloat(cleanText.replace('k', '')) * 1000);
              } else if (cleanText.includes('m')) {
                followers = Math.round(parseFloat(cleanText.replace('m', '')) * 1000000);
              } else {
                followers = parseInt(cleanText.replace(/[^\d]/g, ''), 10);
              }

              if (followers > 0) {
                logger.success(`Найдено подписчиков: ${followers} (селектор: ${selector})`);
                break;
              }
            }
          }
        } catch (e) {
          logger.debug(`Селектор ${selector} не сработал: ${e.message}`);
          continue;
        }
      }

      if (followers === 0) {
        logger.warn('Не удалось найти количество подписчиков');
      }

      return followers;
    } catch (error) {
      logger.error(`Ошибка при парсинге подписчиков: ${error.message}`);
      return 0;
    }
  }

  async saveFollowers(accountId, networkId, followers) {
    try {
      const backendUrl = process.env.BACKEND_URL || 'http://backend:8000';

      logger.info(`Сохраняем количество подписчиков: ${followers} для аккаунта ${accountId}`);

      const response = await axios.patch(`${backendUrl}/accounts/${accountId}/`, {
        followers: followers,
        network_id: networkId
      });

      logger.success(`Подписчики сохранены для аккаунта ${accountId}`);
      return response.data;
    } catch (error) {
      logger.error(`Ошибка при сохранении подписчиков для аккаунта ${accountId}: ${error.message}`, {
        accountId,
        networkId,
        followers,
        error: error.response?.data || error.message
      });
      throw error;
    }
  }

  async markAccountAsParsed(accountId, networkId) {
    try {
      const backendUrl = process.env.BACKEND_URL || 'http://backend:8000';

      logger.info(`Отмечаем аккаунт ${accountId} как обработанный`);

      const response = await axios.patch(`${backendUrl}/accounts/${accountId}/`, {
        is_parsed: true,
        parsed_at: new Date().toISOString(),
        network_id: networkId
      });

      logger.success(`Аккаунт ${accountId} отмечен как обработанный`);
      return response.data;
    } catch (error) {
      logger.error(`Ошибка при отметке аккаунта ${accountId} как обработанного: ${error.message}`, {
        accountId,
        networkId,
        error: error.response?.data || error.message
      });
      throw error;
    }
  }

  async navigateToAccount(accountUrl) {
    try {
      logger.info(`Переходим на аккаунт: ${accountUrl}`);

      await this.page.goto(accountUrl, {
        waitUntil: 'networkidle2',
        timeout: 60000
      });

      await this.delay(5000); // Даем время на загрузку

      // Проверяем, не заблокирован ли аккаунт
      const isPrivate = await this.page.$('h2:has-text("This Account is Private")');
      if (isPrivate) {
        logger.warn(`Аккаунт ${accountUrl} является приватным`);
        return { success: false, reason: 'private' };
      }

      const notFound = await this.page.$('h2:has-text("Sorry, this page isn\'t available")');
      if (notFound) {
        logger.warn(`Аккаунт ${accountUrl} не найден`);
        return { success: false, reason: 'not_found' };
      }

      logger.success(`Успешно перешли на аккаунт: ${accountUrl}`);
      return { success: true };
    } catch (error) {
      logger.error(`Ошибка при переходе на аккаунт ${accountUrl}: ${error.message}`);
      return { success: false, reason: 'navigation_error', error: error.message };
    }
  }

  async saveDebugInfo(accountId, accountUrl) {
    try {
      const timestamp = Date.now();
      const screenshotPath = `/app/logs/account-${accountId}-${timestamp}.png`;
      const htmlPath = `/app/logs/account-${accountId}-${timestamp}.html`;

      await this.page.screenshot({ path: screenshotPath, fullPage: true });
      const html = await this.page.content();
      require('fs').writeFileSync(htmlPath, html);

      logger.info(`Отладочные файлы сохранены для аккаунта ${accountId}`, {
        screenshot: screenshotPath,
        html: htmlPath,
        url: accountUrl
      });

      return { screenshotPath, htmlPath };
    } catch (error) {
      logger.error(`Ошибка при сохранении отладочных файлов для аккаунта ${accountId}: ${error.message}`);
      return null;
    }
  }
}

module.exports = AccountParser;