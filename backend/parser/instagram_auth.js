// auth.js
const logger = require('./comon_logger');

class InstagramAuth {
  constructor(page) {
    this.page = page;
  }

  async delay(ms) {
    return new Promise(res => setTimeout(res, ms));
  }

  async handlePopups() {
    try {
      // Закрываем уведомление о сохранении данных входа
      const notNowButton = await this.page.$x("//button[contains(text(), 'Not Now') or contains(text(), 'Не сейчас')]");
      if (notNowButton.length > 0) {
        await notNowButton[0].click();
        await this.delay(2000);
        logger.info('Закрыли всплывающее окно сохранения данных входа');
      }

      // Закрываем уведомление о push-уведомлениях
      await this.delay(1000);
      const notificationButton = await this.page.$x("//button[contains(text(), 'Not Now') or contains(text(), 'Не сейчас')]");
      if (notificationButton.length > 0) {
        await notificationButton[0].click();
        await this.delay(2000);
        logger.info('Закрыли уведомление о push-уведомлениях');
      }
    } catch (error) {
      logger.debug('Всплывающие окна не найдены или уже закрыты');
    }
  }

  async login(username, password) {
    try {
      logger.info(`Попытка входа в Instagram для пользователя: ${username}`);

      // Переходим на страницу входа
      await this.page.goto('https://www.instagram.com/accounts/login/', {
        waitUntil: 'networkidle2',
        timeout: 60000
      });

      // Ждем загрузки формы входа
      await this.page.waitForSelector('input[name="username"]', { timeout: 30000 });
      await this.delay(2000);

      // Заполняем форму
      await this.page.type('input[name="username"]', username, { delay: 100 });
      await this.page.type('input[name="password"]', password, { delay: 100 });

      // Нажимаем кнопку входа
      await this.page.click('button[type="submit"]');

      // Ждем перенаправления или появления главной страницы
      await this.page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 30000 });

      // Проверяем успешность входа
      const currentUrl = this.page.url();
      if (currentUrl.includes('/accounts/login/')) {
        throw new Error('Не удалось войти в аккаунт - неверные учетные данные или требуется 2FA');
      }

      if (currentUrl.includes('/challenge/')) {
        throw new Error('Instagram требует дополнительную верификацию');
      }

      logger.success('Успешно вошли в Instagram');

      // Обрабатываем возможные всплывающие окна
      await this.handlePopups();

      return true;
    } catch (error) {
      logger.error(`Ошибка входа в Instagram: ${error.message}`, {
        username: username,
        url: this.page.url()
      });
      return false;
    }
  }

  async isLoggedIn() {
    try {
      const currentUrl = this.page.url();
      if (currentUrl.includes('/accounts/login/')) {
        return false;
      }

      // Проверяем наличие элементов, характерных для авторизованного пользователя
      const profileIcon = await this.page.$('svg[aria-label*="Profile"], a[href*="/accounts/edit/"]');
      return !!profileIcon;
    } catch (error) {
      logger.debug('Ошибка при проверке статуса авторизации');
      return false;
    }
  }
}

module.exports = InstagramAuth;