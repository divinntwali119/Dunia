import json
from html.parser import HTMLParser
from urllib.parse import unquote, urljoin, urlsplit

from django.contrib.auth import get_user_model
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
        self.assertContains(response, 'id="appBottomNav"')
        self.assertNotContains(response, '<footer')

    def test_homepage_displays_recent_database_previews(self):
        formations = [Formation.objects.create(title=f'Cours {i}', description='Formation') for i in range(4)]
        news = [News.objects.create(title=f'Annonce {i}', description='Actualité') for i in range(6)]
        response = self.client.get(reverse('home:index'))
        self.assertEqual(list(response.context['formations']), list(reversed(formations[1:])))
        self.assertEqual(list(response.context['news']), list(reversed(news[1:])))
        self.assertContains(response, 'class="news-dot', count=6)
        self.assertContains(response, f'href="{reverse("formations:detail", args=[formations[-1].pk])}"')
        self.assertNotContains(response, 'Cours 0')
        self.assertNotContains(response, 'Annonce 0')

    def test_navigation_and_local_assets_resolve_on_every_page(self):
        class AssetsAndLinks(HTMLParser):
            def __init__(self):
                super().__init__()
                self.links = []
                self.assets = []
                self.app_nav_links = []
                self.in_app_nav = False

            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if tag == 'nav' and attrs.get('id') == 'appBottomNav':
                    self.in_app_nav = True
                if tag == 'a' and attrs.get('href'):
                    self.links.append(attrs['href'])
                    if self.in_app_nav:
                        self.app_nav_links.append(attrs['href'])
                for attribute in ('src', 'poster'):
                    if attrs.get(attribute):
                        self.assets.append(attrs[attribute])
                if tag == 'link' and attrs.get('href'):
                    self.assets.append(attrs['href'])

            def handle_endtag(self, tag):
                if tag == 'nav' and self.in_app_nav:
                    self.in_app_nav = False

        page_names = (
            'home:index', 'formations:list', 'news:list',
            'formations:login', 'formations:signup',
        )
        for name in page_names:
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
                self.assertEqual(len(parser.app_nav_links), 4)
                self.assertEqual(parser.app_nav_links[0], reverse('home:index'))
                self.assertEqual(parser.app_nav_links[1], reverse('formations:list'))
                self.assertEqual(parser.app_nav_links[2], reverse('news:notifications_settings'))
                expected_account_url = reverse(
                    'formations:login' if name == 'formations:login' else 'formations:signup',
                )
                self.assertEqual(parser.app_nav_links[3], expected_account_url)
                self.assertContains(response, 'id="appContent" class="app-content"')
                self.assertContains(response, 'class="app-topbar"')
                self.assertContains(response, 'body.app-mode')
                self.assertNotContains(response, '<footer')
                self.assertNotContains(response, 'id="mobileMenu"')
                if name == 'formations:login':
                    self.assertContains(response, 'Me connecter')
                else:
                    self.assertContains(response, 'M’inscrire')

    def test_authenticated_home_navigation_links_to_the_learner_space(self):
        user = get_user_model().objects.create_user('nav-learner', password='test-password-123')
        self.client.force_login(user)

        response = self.client.get(reverse('home:index'))

        self.assertContains(response, 'Mon espace')
        self.assertContains(response, f'href="{reverse("formations:student_dashboard")}"')

    def test_logout_returns_to_the_login_button(self):
        user = get_user_model().objects.create_user('nav-returning', password='test-password-123')
        self.client.force_login(user)

        response = self.client.post(reverse('formations:logout'))

        self.assertRedirects(response, reverse('formations:login'))
        self.assertContains(self.client.get(reverse('formations:login')), 'Me connecter')

    def test_service_worker_is_served_at_the_site_root_with_allowed_scope(self):
        response = self.client.get(reverse('home:service_worker'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Service-Worker-Allowed'], '/')
        content = b''.join(response.streaming_content).decode()
        self.assertIn('self.addEventListener', content)

    def test_pwa_manifest_icons_resolve_from_the_manifest_directory(self):
        manifest_path = finders.find('documents/manifest.json')
        with open(manifest_path, encoding='utf-8') as manifest_file:
            manifest = json.load(manifest_file)

        icons = list(manifest.get('icons', []))
        for shortcut in manifest.get('shortcuts', []):
            icons.extend(shortcut.get('icons', []))

        manifest_url = 'https://dunia.example/static/documents/manifest.json'
        for icon in icons:
            with self.subTest(icon=icon['src']):
                icon_path = urlsplit(urljoin(manifest_url, icon['src'])).path
                self.assertTrue(icon_path.startswith('/static/'), icon_path)
                self.assertIsNotNone(
                    finders.find(unquote(icon_path.removeprefix('/static/'))),
                    icon_path,
                )
