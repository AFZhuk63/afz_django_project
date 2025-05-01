import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from django.core.management.base import BaseCommand
from django.utils import timezone
from news.models import Article, Category, Tag
from django.contrib.auth import get_user_model
import logging
import random
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fake_useragent import UserAgent
from datetime import datetime
import feedparser
chrome_options = Options()
chrome_options.add_argument("--headless")  # если вам нужно работать без GUI

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# Настройка логирования
logging.basicConfig(
    filename='news_parser.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UniversalNewsParser:
    SOURCES_CONFIG = {
        'bbc': {
            'name': 'BBC News',
            'base_url': 'https://www.bbc.com',
            'news_url': 'https://www.bbc.com/news',
            'rss_url': 'https://feeds.bbci.co.uk/news/rss.xml',
            'mobile_url': 'https://m.bbc.com/news',
            'uk_url': 'https://www.bbc.co.uk/news',
            'category': 'International',
            'selectors': {
                'articles': [
                    'a[data-testid="internal-link"]',
                    'div.gs-c-promo a.gs-c-promo-heading',  # Найденный тобой селектор
                    'a.ssrcss-1mrs5ns-PromoLink'  # Еще один корректный селектор
                ],
                'title': 'h2[data-testid="card-headline"]',
                'content': [
                    'article[role="article"] p',
                    'div.ssrcss-11r1m41-RichTextContainer p'
                ],
                'date': 'time[data-testid="timestamp"]',
                'image': 'div[data-component="image-block"] img'
            },
            'use_selenium': True,
            'delay': (10, 15),
            'anti_bot': True,
            'fallback_order': ['rss', 'mobile', 'uk', 'main']
        },
        'cnn': {
            'name': 'CNN',
            'base_url': 'https://edition.cnn.com',
            'news_url': 'https://edition.cnn.com/world',
            'category': 'World',
            'selectors': {
                'articles': [
                    'div.container__item a.container__link',
                    'h3.container__headline a',
                    'a.container_lead-plus-headlines__link'
                ],
                'title': 'h1.article__title',
                'content': [
                    'section.article__content p.paragraph',
                    'div.article__content p'
                ],
                'date': 'div.article__timestamp',
                'image': 'img.image__dam-img'
            },
            'use_selenium': True,
            'delay': (15, 20),
            'anti_bot': True,
            'pre_actions': [
                {'type': 'wait', 'timeout': 10}
            ]
        },
        'ria': {
            'name': 'RIA Novosti',
            'base_url': 'https://ria.ru',
            'news_url': 'https://ria.ru',
            'rss_url': 'https://ria.ru/export/rss2/archive/index.xml',
            'category': 'Russia',
            'selectors': {
                'articles': 'a.cell-list__item-link',
                'title': 'h1.article__title',
                'content': 'div.article__text',
                'date': 'div.article__info-date-time',
                'image': 'div.article__photo img'
            },
            'use_selenium': False,
            'delay': (3, 5)
        },
        'novayagazeta': {
            'name': 'Novaya Gazeta',
            'base_url': 'https://novayagazeta.ru',
            'news_url': 'https://novayagazeta.ru',
            'rss_url': 'https://novayagazeta.ru/rss/all.xml',
            'category': 'Russia',
            'selectors': {
                'articles': [
                    'a.story__title-link',
                    'div.story__title a',
                    'a.story__link'
                ],
                'title': 'h1.story__head',
                'content': 'div.story__content p',
                'date': 'time.story__date',
                'image': 'div.story__image img'
            },
            'use_selenium': False,
            'delay': (3, 5),
            'fallback_order': ['rss', 'main']
        }
    }

    def __init__(self):
        self.ua = UserAgent()
        self.driver = None
        self.session = requests.Session()
        self.session.headers.update({
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.google.com/',
            'DNT': '1'
        })
        self.init_selenium()

    def init_selenium(self):
        """Инициализация Selenium"""
        try:
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")  # Отключение GPU для избежания ошибки GpuControl
            options.add_argument(f"user-agent={self.ua.random}")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)

            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)

            # Обход детектирования бота
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                            Object.defineProperty(navigator, 'webdriver', { get: () => undefined })
                            window.navigator.chrome = { runtime: {}, }
                        """
            })
            return True
        except Exception as e:
            logger.error(f"Selenium init error: {str(e)}")
            return False

    def get_page(self, url, source_name, max_retries=3):
        """Обновленный метод загрузки страницы с корректировками"""
        source = self.SOURCES_CONFIG[source_name]

        for attempt in range(max_retries):
            try:
                if source['use_selenium'] and self.driver:
                    soup = self.get_with_selenium(url, source)
                else:
                    soup = self.get_with_requests(url, source)

                if soup and not self.check_banned(soup):
                    return soup

                logger.warning(f"Attempt {attempt + 1} failed for {url}")
                time.sleep((attempt + 1) * 5)

            except Exception as e:
                logger.error(f"Error loading page: {str(e)}")
                if attempt == max_retries - 1:
                    raise

        return None

    def get_with_selenium(self, url, source):
        """Загрузка через Selenium с ожиданием контента"""
        try:
            self.driver.get(url)

            # Ожидание появления контента перед парсингом
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.gs-c-promo'))
            )

            if 'pre_actions' in source:
                for action in source['pre_actions']:
                    if action['type'] == 'wait':
                        time.sleep(action.get('timeout', 5))
                    elif action['type'] == 'scroll':
                        time.sleep(random.uniform(2, 5))  # ⏳ Пауза перед прокруткой
                        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                        time.sleep(random.uniform(2, 5))  # ⏳ Пауза после прокрутки

            if "challenge" in self.driver.page_source.lower():
                raise ValueError("Bot challenge detected")

            return BeautifulSoup(self.driver.page_source, 'html.parser')

        except Exception as e:
            logger.error(f"Selenium error: {str(e)}")
            return None  # Возвращаем None, если произошла ошибка

    def get_with_requests(self, url, source):
        """Загрузка через requests"""
        try:
            headers = {
                'User-Agent': self.ua.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }

            time.sleep(random.uniform(*source['delay']))
            response = self.session.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            if self.check_banned(soup):
                raise ValueError("Bot detection triggered")

            return soup
        except Exception as e:
            logger.error(f"Requests error: {str(e)}")
            return None

    def check_banned(self, soup):
        """Проверка блокировки"""
        ban_phrases = [
            'captcha', 'cloudflare', 'access denied',
            'bot', '403', 'неавторизованный доступ'
        ]
        text = soup.get_text().lower() if soup else ''
        return any(phrase in text for phrase in ban_phrases)

    def parse_news_source(self, source_name, max_articles=3):
        """Основной метод парсинга"""
        source = self.SOURCES_CONFIG[source_name]
        logger.info(f"Starting {source['name']} parsing...")

        # Сначала пробуем RSS
        if 'rss_url' in source:
            articles = self.parse_rss(source['rss_url'], source)
            if articles:
                return self.process_articles(articles[:max_articles], 'rss')

        # Затем другие методы из fallback_order
        if 'fallback_order' in source:
            for method in source['fallback_order']:
                if method == 'rss':
                    continue

                try:
                    if method == 'mobile':
                        url = source.get('mobile_url', source['news_url'])
                    elif method == 'uk':
                        url = source.get('uk_url', source['news_url'])
                    else:
                        url = source['news_url']

                    soup = self.get_page(url, source_name)
                    if soup:
                        articles = self.parse_articles_from_soup(soup, source)
                        if articles:
                            return self.process_articles(articles[:max_articles], method)

                except Exception as e:
                    logger.warning(f"Method {method} failed: {str(e)}")
        else:
            soup = self.get_page(source['news_url'], source_name)
            if soup:
                articles = self.parse_articles_from_soup(soup, source)
                if articles:
                    return self.process_articles(articles[:max_articles], 'main')

        logger.error(f"All methods failed for {source_name}")
        return [], 'failed'

    def parse_rss(self, rss_url, source):
        """Парсинг RSS"""
        try:
            feed = feedparser.parse(rss_url)
            articles = []
            for entry in feed.entries:
                articles.append({
                    'title': entry.title,
                    'content': entry.description,
                    'date': datetime(*entry.published_parsed[:6]) if hasattr(entry,
                                                                             'published_parsed') else timezone.now(),
                    'url': entry.link,
                    'image_url': None,
                    'source': source['name'],
                    'category': source['category']
                })
            return articles
        except Exception as e:
            logger.error(f"RSS parsing error: {str(e)}")
            return None

    def parse_articles_from_soup(self, soup, source):
        """Парсинг статей из HTML"""
        article_links = []
        for selector in source['selectors']['articles']:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href and not href.startswith(('#', 'javascript:')):
                    full_url = urljoin(source['base_url'], href)
                    if full_url not in article_links:
                        article_links.append(full_url)

        if not article_links:
            return None

        articles = []
        for url in article_links:
            article = self.parse_article(url, source)
            if article:
                articles.append(article)

        return articles if articles else None

    def parse_article(self, url, source):
        """Обновленный парсинг статьи с защитой от ошибок"""
        soup = self.get_page(url, source['name'])
        if not soup:
            logger.warning(f"⚠ Ошибка загрузки страницы: {url}")
            return None

        try:
            title = self.get_element_text(soup, source['selectors']['title'])
            content = self.get_element_text(soup, source['selectors']['content'], join=True)
            date_text = self.get_element_text(soup, source['selectors']['date'])
            image_url = self.get_element_attr(soup, source['selectors']['image'], 'src')

            if not title:
                logger.warning(f"⚠ Заголовок не найден: {url}")
                return None
            if not content:
                logger.warning(f"⚠ Контент отсутствует: {url}")
                return None

            pub_date = self.parse_date(date_text, source['name']) if date_text else timezone.now()

            return {
                'title': title,
                'content': content,
                'date': pub_date,
                'url': url,
                'image_url': image_url,
                'source': source['name'],
                'category': source['category']
            }
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга статьи: {str(e)}")
            return None

    def get_element_text(self, soup, selector, join=False):
        """Получение текста элемента"""
        if isinstance(selector, list):
            for sel in selector:
                elements = soup.select(sel)
                if elements:
                    if join:
                        return '\n\n'.join(e.text.strip() for e in elements if e.text.strip())
                    return elements[0].text.strip()
            return None
        else:
            elements = soup.select(selector)
            if elements:
                if join:
                    return '\n\n'.join(e.text.strip() for e in elements if e.text.strip())
                return elements[0].text.strip()
            return None

    def get_element_attr(self, soup, selector, attr):
        """Получение атрибута элемента"""
        if isinstance(selector, list):
            for sel in selector:
                element = soup.select_one(sel)
                if element and element.get(attr):
                    return urljoin(self.SOURCES_CONFIG['base_url'], element[attr])
            return None
        else:
            element = soup.select_one(selector)
            return urljoin(self.SOURCES_CONFIG['base_url'], element[attr]) if element and element.get(attr) else None

    def parse_date(self, date_str, source_name):
        """Парсинг даты"""
        try:
            if source_name == 'bbc':
                date_str = date_str.split('•')[-1].strip()
                for fmt in ['%d %B %Y', '%d %b %Y']:
                    try:
                        return datetime.strptime(date_str, fmt)
                    except ValueError:
                        continue
            elif source_name == 'cnn':
                date_str = date_str.replace('Updated', '').split('ET,')[-1].strip()
                for fmt in ['%a %B %d, %Y', '%a %b %d, %Y']:
                    try:
                        return datetime.strptime(date_str, fmt)
                    except ValueError:
                        continue
            elif source_name == 'ria':
                return datetime.strptime(date_str, '%H:%M %d.%m.%Y')
            elif source_name == 'novayagazeta':
                return datetime.strptime(date_str, '%d.%m.%Y')
        except Exception as e:
            logger.warning(f"Date parsing failed: {str(e)}")

        return timezone.now()

    def process_articles(self, articles, method):
        """Обновленное сохранение статей"""
        results = []
        user = get_user_model().objects.first()

        if not user:
            logger.warning("⚠ Нет зарегистрированных пользователей, создаётся системный автор")
            user, _ = get_user_model().objects.get_or_create(username="system",
                                                             defaults={"email": "system@example.com"})

        for article in articles:
            try:
                if Article.objects.filter(title=article['title'][:255]).exists():
                    logger.info(f"📌 Статья уже существует: {article['title'][:50]}...")
                    continue

                category, _ = Category.objects.get_or_create(
                    name=article['category'],
                    defaults={'name': article['category']}
                )

                article_obj = Article.objects.create(
                    title=article['title'][:255],
                    content=article['content'][:10000],
                    publication_date=article['date'],
                    category=category,
                    author=user,
                    status=True,
                    is_active=True,
                    level=Article.Level.TOP,
                    original_url=article['url'],
                    image_url=article.get('image_url', '')[:500]
                )

                tags = ["News", article['source'], article['category']]
                for tag_name in tags:
                    tag, _ = Tag.objects.get_or_create(name=tag_name[:30])
                    article_obj.tags.add(tag)

                results.append(article)
                logger.info(f"✅ Сохранено через {method}: {article['title'][:50]}...")
            except Exception as e:
                logger.error(f"❌ Ошибка сохранения статьи: {str(e)}")

        return results

    def close(self):
        """Закрытие ресурсов"""
        try:
            if self.driver:
                self.driver.quit()
            self.session.close()
        except Exception as e:
            logger.error(f"Cleanup error: {str(e)}")


class Command(BaseCommand):
    help = 'Advanced news parser with multiple fallback strategies'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            type=str,
            choices=['bbc', 'cnn', 'ria', 'novayagazeta', 'all'],
            default='all',
            help='Source to parse (bbc/cnn/ria/novayagazeta/all)'
        )
        parser.add_argument(
            '--max-articles',
            type=int,
            default=3,
            help='Maximum articles to parse per source'
        )
        parser.add_argument(
            '--no-selenium',
            action='store_true',
            help='Disable Selenium even if configured'
        )

    def handle(self, *args, **options):
        parser = UniversalNewsParser()
        sources = ['bbc', 'cnn', 'ria', 'novayagazeta'] if options['source'] == 'all' else [options['source']]

        if options['no_selenium']:
            for source in sources:
                parser.SOURCES_CONFIG[source]['use_selenium'] = False

        for source_name in sources:
            try:
                self.stdout.write(f"🔄 Processing {source_name.upper()}...")
                articles, method = parser.parse_news_source(source_name, options['max_articles'])

                if articles:
                    for article in articles:
                        self.stdout.write(self.style.SUCCESS(
                            f"✅ [{method.upper()}] {article['title'][:60]}..."
                        ))
                        self.stdout.write(f"🔗 URL: {article['url']}")
                else:
                    self.stdout.write(self.style.WARNING(
                        f"⚠ No articles from {source_name.upper()}"
                    ))
            except Exception as e:
                logger.error(f"Critical error: {str(e)}", exc_info=True)
                self.stdout.write(self.style.ERROR(
                    f"❌ {source_name.upper()} error: {str(e)}"
                ))
        parser.close()