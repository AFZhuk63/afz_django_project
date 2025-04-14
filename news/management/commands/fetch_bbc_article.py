from django.core.management.base import BaseCommand
from django.utils import timezone
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from news.models import Article, Category, Tag
from django.contrib.auth import get_user_model
import logging
import random
import time

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Парсинг новостей с РИА Новости с улучшенными селекторами'

    def handle(self, *args, **options):
        try:
            source = {
                'name': 'РИА Новости',
                'url': 'https://ria.ru',
                'category': 'Россия',
                'selectors': {
                    'articles': [
                        'a.list-item__title',  # Основной селектор
                        'div.list-item__content a',  # Альтернативный селектор
                        'a.cell-list__item-link'  # Для новых версий сайта
                    ],
                    'title': 'h1.article__title',
                    'content': 'div.article__text',
                    'date': 'div.article__info-date-time',
                    'image': 'div.article__photo img'
                },
                'delay': 3
            }

            self.stdout.write("🔍 Улучшенный парсинг РИА Новости...")

            # 1. Загрузка с ротацией User-Agent
            soup = self.fetch_page(source['url'])
            if not soup:
                return

            # 2. Поиск статей по нескольким селекторам
            article_links = self.find_articles(soup, source)
            if not article_links:
                self.stdout.write("ℹ Статьи не найдены. Возможные причины:")
                self.stdout.write("- Изменилась структура сайта")
                self.stdout.write("- Нужно обновить селекторы")
                with open('ria_debug.html', 'w', encoding='utf-8') as f:
                    f.write(soup.prettify())
                self.stdout.write("⚠ Сохранён HTML для анализа: ria_debug.html")
                return

            # 3. Выбор и парсинг случайной статьи
            article_url = urljoin(source['url'], random.choice(article_links)['href'])
            time.sleep(source['delay'])

            article_data = self.parse_article(article_url, source)
            if article_data:
                self.save_article(article_data, source)
                self.stdout.write(self.style.SUCCESS(
                    f"✅ Успешно: {article_data['title'][:60]}..."
                ))
                self.stdout.write(f"🔗 Ссылка: {article_url}")

        except Exception as e:
            logger.error(f"Ошибка: {str(e)}", exc_info=True)
            self.stdout.write(self.style.ERROR(
                f"❌ Ошибка: {str(e)}"
            ))

    def fetch_page(self, url):
        """Загрузка страницы с ротацией заголовков"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
            'Mozilla/5.0 (X11; Linux x86_64)'
        ]

        headers = {
            'User-Agent': random.choice(user_agents),
            'Accept-Language': 'ru-RU,ru;q=0.9',
            'Referer': 'https://www.google.com/',
            'DNT': '1'
        }

        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            if response.status_code != 200:
                raise ValueError(f"HTTP статус: {response.status_code}")

            return BeautifulSoup(response.text, 'html.parser')

        except Exception as e:
            logger.error(f"Ошибка загрузки {url}: {str(e)}")
            return None

    def find_articles(self, soup, source):
        """Поиск статей по нескольким альтернативным селекторам"""
        articles = []

        for selector in source['selectors']['articles']:
            found = soup.select(selector)
            if found:
                articles.extend(found)

        # Фильтрация запрещённых URL
        filtered = []
        for a in articles:
            href = a.get('href', '')
            if href and not any(d in href for d in ['/embed/', '-print.html', '/search/']):
                filtered.append(a)

        return filtered

    def parse_article(self, url, source):
        """Парсинг статьи с расширенными проверками"""
        soup = self.fetch_page(url)
        if not soup:
            return None

        try:
            # Заголовок
            title = soup.select_one(source['selectors']['title'])
            if not title:
                raise ValueError("Заголовок не найден")

            # Контент
            content_blocks = soup.select(source['selectors']['content'])
            if not content_blocks:
                raise ValueError("Контент не найден")

            # Дата (если есть)
            date = soup.select_one(source['selectors']['date'])
            pub_date = self.parse_date(date.text.strip()) if date else timezone.now()

            return {
                'title': title.text.strip(),
                'content': '\n\n'.join(p.text.strip() for p in content_blocks if p.text.strip()),
                'date': pub_date,
                'url': url,
                'image_url': self.get_image_url(soup, source)
            }

        except Exception as e:
            logger.error(f"Ошибка парсинга статьи: {str(e)}")
            return None

    def get_image_url(self, soup, source):
        """Получение URL главного изображения"""
        img = soup.select_one(source['selectors']['image'])
        return urljoin(source['url'], img['src']) if img and img.get('src') else None

    def parse_date(self, date_str):
        """Парсинг даты из строки"""
        try:
            # Пример: "02:30 17.10.2023"
            from datetime import datetime
            return datetime.strptime(date_str, '%H:%M %d.%m.%Y')
        except:
            return timezone.now()

    def save_article(self, data, source):
        """Сохранение статьи с проверкой дубликатов"""
        if Article.objects.filter(title=data['title'][:255]).exists():
            logger.info(f"Статья уже существует: {data['title'][:50]}...")
            return

        category, _ = Category.objects.get_or_create(
            name=source['category'],
            defaults={'name': source['category']}
        )

        article = Article.objects.create(
            title=data['title'][:255],
            content=data['content'][:10000],
            publication_date=data['date'],
            category=category,
            author=get_user_model().objects.first(),
            status=True,
            is_active=True,
            level=Article.Level.TOP,
            original_url=data['url']
        )

        tags = ["Новости", "РИА", source['category']]
        for tag_name in tags:
            tag, _ = Tag.objects.get_or_create(name=tag_name[:30])
            article.tags.add(tag)