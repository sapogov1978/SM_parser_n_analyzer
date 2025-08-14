// postsParser.js
const logger = require('./comon_logger');
const axios = require('axios');

class PostsParser {
  constructor(page) {
    this.page = page;
  }

  async delay(ms) {
    return new Promise(res => setTimeout(res, ms));
  }

  async getReelLinks() {
    try {
      logger.info('Ищем ссылки на reels и посты');

      const links = await this.page.evaluate(() => {
        const foundLinks = [];
        const anchors = document.querySelectorAll('a[href*="/reel/"], a[href*="/p/"]');

        anchors.forEach(anchor => {
          const href = anchor.href;
          if (href && (href.includes('/reel/') || href.includes('/p/'))) {
            foundLinks.push(href);
          }
        });

        return [...new Set(foundLinks)]; // Убираем дубликаты
      });

      logger.success(`Найдено ${links.length} ссылок на посты/reels`);
      return links;
    } catch (error) {
      logger.error(`Ошибка при поиске ссылок на посты: ${error.message}`);
      return [];
    }
  }

  async parsePostData(url) {
    try {
      logger.info(`Парсим данные поста: ${url}`);

      await this.page.goto(url, { waitUntil: 'networkidle2', timeout: 60000 });
      await this.delay(3000);

      // Современный способ получения данных
      const postData = await this.page.evaluate(() => {
        let data = null;

        // Попытка 1: window.__additionalDataLoaded
        if (window.__additionalDataLoaded) {
          const keys = Object.keys(window.__additionalDataLoaded);
          for (let key of keys) {
            if (key.includes('media')) {
              data = window.__additionalDataLoaded[key];
              break;
            }
          }
        }

        // Попытка 2: в script тегах
        if (!data) {
          const scripts = document.querySelectorAll('script[type="application/json"]');
          for (let script of scripts) {
            try {
              const json = JSON.parse(script.textContent);
              if (json.require && json.require[0] && json.require[0][3]) {
                const modules = json.require[0][3];
                for (let module of modules) {
                  if (module.__bbox && module.__bbox.result && module.__bbox.result.data) {
                    data = module.__bbox.result.data;
                    break;
                  }
                }
                if (data) break;
              }
            } catch (e) {
              continue;
            }
          }
        }

        // Попытка 3: извлечение из DOM элементов
        if (!data) {
          const viewsElement = document.querySelector('span[title*="views"], span:contains("views")');
          const likesElement = document.querySelector('button span[title*="likes"], button span:contains("likes")');
          const commentsElement = document.querySelector('button span:contains("comments")');

          data = {
            video_view_count: viewsElement ? parseInt(viewsElement.textContent.replace(/[^\d]/g, '')) : 0,
            edge_media_preview_like: { count: likesElement ? parseInt(likesElement.textContent.replace(/[^\d]/g, '')) : 0 },
            edge_media_to_comment: { count: commentsElement ? parseInt(commentsElement.textContent.replace(/[^\d]/g, '')) : 0 },
            taken_at_timestamp: Math.floor(Date.now() / 1000) // Используем текущее время как fallback
          };
        }

        return data;
      });

      if (!postData) {
        logger.warn(`Не удалось получить данные поста: ${url}`);
        return null;
      }

      // Извлекаем метрики из полученных данных
      const views = postData.video_view_count || postData.view_count || 0;
      const likes = postData.edge_media_preview_like?.count ||
                   postData.like_count || 0;
      const comments = postData.edge_media_to_comment?.count ||
                      postData.comment_count || 0;
      const timestamp = postData.taken_at_timestamp ||
                       postData.taken_at ||
                       Math.floor(Date.now() / 1000);

      const published_at = new Date(timestamp * 1000).toISOString();

      // Проверяем, что пост не старше 7 дней
      const sevenDaysAgo = Date.now() - 7 * 24 * 60 * 60 * 1000;
      if (timestamp * 1000 < sevenDaysAgo) {
        logger.info(`Пост ${url} старше 7 дней, пропускаем`);
        return null;
      }

      logger.success(`Обработан пост: views=${views}, likes=${likes}, comments=${comments}`);

      return {
        url,
        published_at,
        views,
        likes,
        comments,
        timestamp
      };

    } catch (error) {
      logger.error(`Ошибка при парсинге поста ${url}: ${error.message}`);
      return null;
    }
  }

  async scrapeAccountPosts(followers, accountId, networkId, maxPosts = 10) {
    const posts = [];

    try {
      logger.info(`Начинаем парсинг постов для аккаунта ${accountId} (followers: ${followers})`);

      const reelLinks = await this.getReelLinks();

      if (reelLinks.length === 0) {
        logger.warn('Не найдено ссылок на посты/reels');
        return posts;
      }

      const linksToProcess = reelLinks.slice(0, maxPosts);
      logger.info(`Обрабатываем ${linksToProcess.length} постов`);

      for (let url of linksToProcess) {
        const postData = await this.parsePostData(url);

        if (postData) {
          const engagement_rate = postData.views ? (postData.likes + postData.comments) / postData.views : 0;
          const score = followers > 0 ? (postData.views / followers) * engagement_rate : 0;

          posts.push({
            ...postData,
            account_id: accountId,
            network_id: networkId,
            score: score,
          });
        }

        await this.delay(3000); // Задержка между постами
      }

      logger.success(`Успешно обработано ${posts.length} постов для аккаунта ${accountId}`);
      return posts;

    } catch (error) {
      logger.error(`Общая ошибка при парсинге постов для аккаунта ${accountId}: ${error.message}`);
      return posts;
    }
  }

  async savePosts(posts, networkId) {
    try {
      if (!posts || posts.length === 0) {
        logger.info('Нет постов для сохранения');
        return;
      }

      const backendUrl = process.env.BACKEND_URL || 'http://backend:8000';

      logger.info(`Сохраняем ${posts.length} постов в базу данных`);

      const response = await axios.post(`${backendUrl}/posts/bulk-create/`, {
        posts: posts,
        network_id: networkId
      });

      logger.success(`Успешно сохранено ${posts.length} постов`);
      return response.data;

    } catch (error) {
      logger.error(`Ошибка при сохранении постов: ${error.message}`, {
        postsCount: posts?.length || 0,
        networkId,
        error: error.response?.data || error.message
      });
      throw error;
    }
  }
}

module.exports = PostsParser;