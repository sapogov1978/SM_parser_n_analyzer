const puppeteer = require('puppeteer');
const axios = require('axios');
const fs = require('fs');

const LOGS_DIR = '/logs';

async function delay(ms) {
  return new Promise(res => setTimeout(res, ms));
}

async function parseFollowers(page) {
  try {
    const text = await page.$eval('header li span', el => el.getAttribute('title') || el.innerText);
    const followers = text.replace(/[^0-9]/g, '');
    return parseInt(followers, 10);
  } catch {
    return 0;
  }
}

async function scrapeReelsPosts(page, followers, accountId, networkId) {
  const posts = [];

  const reelLinks = await page.$$eval('a', anchors =>
    anchors.map(a => a.href).filter(href => href.includes('/reel/'))
  );

  for (let url of reelLinks) {
    try {
      await page.goto(url, { waitUntil: 'networkidle2', timeout: 60000 });

      const data = await page.evaluate(() => {
        const script = [...document.scripts].find(s => s.textContent.includes('window._sharedData'));
        const match = script.textContent.match(/window\._sharedData\s*=\s*(\{.*\});/);
        const json = JSON.parse(match[1]);
        return json.entry_data.PostPage[0].graphql.shortcode_media;
      });

      const views = data.video_view_count || 0;
      const likes = data.edge_media_preview_like.count;
      const comments = data.edge_media_to_comment.count;
      const timestamp = data.taken_at_timestamp;
      const published_at = new Date(timestamp * 1000).toISOString();

      const engagement_rate = views ? (likes + comments) / views : 0;
      const score = (views / followers) * engagement_rate;

      const sevenDaysAgo = Date.now() - 7 * 24 * 60 * 60 * 1000;
      if (timestamp * 1000 < sevenDaysAgo) continue;

      posts.push({
        url,
        published_at,
        views,
        likes,
        comments,
        account_id: accountId,
        network_id: networkId,
        score: score,
      });

      await delay(2000);
    } catch (err) {
      console.error(`Error while get ${url}: ${err.message}`);
    }
  }

  return posts;
}

async function main() {
  const browser = await puppeteer.launch({ headless: true, args: ['--no-sandbox'] });
  const page = await browser.newPage();

  const { data: accounts } = await axios.get('http://backend:8000/accounts/for-parsing');

  for (let acc of accounts) {
    try {
      console.log(`Parsing: ${acc.url}`);
      await page.goto(acc.url, { waitUntil: 'networkidle2', timeout: 60000 });



      // --- Debug логирование ---
      const testPath = `${LOGS_DIR}/test-${Date.now()}.txt`;

      try {
        fs.writeFileSync(testPath, "test log");
        console.log(`✅ SUCCESSFULLY WROTE TO ${testPath}`);
      } catch (e) {
        console.error(`❌ FAILED TO WRITE TO ${testPath}: ${e.message}`);
      }
      
      const screenshotPath = `${LOGS_DIR}/page-${acc.id}.png`;
      const htmlPath = `${LOGS_DIR}/page-${acc.id}.html`;

      await page.screenshot({ path: screenshotPath, fullPage: true });

      const html = await page.content();
      fs.writeFileSync(htmlPath, html);

      // --- Парсинг ---
      const followers = await parseFollowers(page);
      await axios.post(`http://backend:8000/accounts/${acc.id}/followers`, { followers });

      const posts = await scrapeReelsPosts(page, followers, acc.id, acc.network_id);
      if (posts.length) {
        await axios.post('http://backend:8000/posts/save', { posts });
      }

      await axios.post(`http://backend:8000/accounts/${acc.id}/parsed`);

    } catch (err) {
      console.error(`Error with account ${acc.url}: ${err.message}`);
    }
  }

  await browser.close();
}

main();