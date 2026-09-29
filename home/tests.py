from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit

from django.contrib.staticfiles import finders
from django.test import TestCase, override_settings
from django.urls import resolve, reverse

from formations.models import Formation
from news.models import News


@override_settings(DEBUG=True)
class SitePagesTests(TestCase):
    def test_homepage_empty_states(self):
        response = self.client.get(reverse('home:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Aucune actualité pour le moment.')
        self.assertContains(response, 'Aucune formation disponible pour le moment.')

    def test_homepage_displays_recent_database_previews(self):
        formations = [Formation.objects.create(title=f'Cours {i}', description='Formation') for i in range(4)]
        news = [News.objects.create(title=f'Annonce {i}', description='Actualité') for i in range(6)]
        response = self.client.get(reverse('home:index'))
        self.assertEqual(list(response.context['formations']), list(reversed(formations[1:])))
        self.assertEqual(list(response.context['news']), list(reversed(news[1:])))
        self.assertContains(response, 'class="news-dot', count=6)
        self.assertContains(response, f'href="{reverse("formations:list")}#formation-{formations[-1].pk}"')
        self.assertNotContains(response, 'Cours 0')
        self.assertNotContains(response, 'Annonce 0')

    def test_navigation_and_local_assets_resolve_on_every_page(self):
        class AssetsAndLinks(HTMLParser):
            def __init__(self):
                super().__init__()
                self.links = []
                self.assets = []

            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if tag == 'a' and attrs.get('href'):
                    self.links.append(attrs['href'])
                for attribute in ('src', 'poster'):
                    if attrs.get(attribute):
                        self.assets.append(attrs[attribute])
                if tag == 'link' and attrs.get('href'):
                    self.assets.append(attrs['href'])

        for name in ('home:index', 'formations:list', 'news:list'):
            with self.subTest(page=name):
                response = self.client.get(reverse(name))
                parser = AssetsAndLinks()
                parser.feed(response.content.decode())
                for link in parser.links:
                    url = urlsplit(link)
                    if not url.scheme and not url.netloc and url.path:
                        self.assertTrue(url.path.startswith('/'), link)
                        resolve(url.path)
                for asset in parser.assets:
                    url = urlsplit(asset)
                    if not url.scheme and not url.netloc:
                        self.assertTrue(url.path.startswith('/static/'), asset)
                        self.assertIsNotNone(finders.find(unquote(url.path.removeprefix('/static/'))), asset)
                self.assertContains(response, f'href="{reverse("home:index")}#about"')
                self.assertContains(response, f'href="{reverse("home:index")}#contact"')
