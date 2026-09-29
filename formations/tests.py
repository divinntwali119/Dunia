from html.parser import HTMLParser
from urllib.parse import parse_qs, urlsplit

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Formation


@override_settings(DEBUG=True)
class FormationPagesTests(TestCase):
    def test_empty_catalog(self):
        response = self.client.get(reverse('formations:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Aucune formation trouvée')
        self.assertNotContains(response, 'id="formation-')

    def test_catalog_uses_database_fields_and_optional_images(self):
        first = Formation.objects.create(
            title='Design pratique', description='Apprendre les outils de design.',
            category=Formation.Category.DESIGN, duration='4 jours',
        )
        latest = Formation.objects.create(
            title='Python avancé', description='Construire une application.',
            category=Formation.Category.DEVELOPMENT, level=Formation.Level.ADVANCED,
            image='formation_images/python.png',
        )
        response = self.client.get(reverse('formations:list'))
        self.assertEqual(list(response.context['formations']), [latest, first])
        for text in [first.title, first.description, '4 jours', 'Avancé',
                     'data-category="design"', '/media/formation_images/python.png',
                     '/static/images/logo-dunia.png']:
            self.assertContains(response, text)

    def test_registration_link_encodes_the_formation_title(self):
        formation = Formation.objects.create(title='Design & UI + UX #1', description='Atelier')
        response = self.client.get(reverse('formations:list'))

        class Links(HTMLParser):
            def __init__(self):
                super().__init__()
                self.urls = []

            def handle_starttag(self, tag, attrs):
                if tag == 'a':
                    self.urls.append(dict(attrs).get('href', ''))

        parser = Links()
        parser.feed(response.content.decode())
        registration = next(url for url in parser.urls if '?text=' in url)
        self.assertTrue(parse_qs(urlsplit(registration).query)['text'][0].endswith(formation.title))

    def test_admin_can_create_a_formation_shown_in_catalog(self):
        self.assertTrue(admin.site.is_registered(Formation))
        user = get_user_model().objects.create_superuser('editor', 'editor@example.com', 'test-password')
        self.client.force_login(user)
        response = self.client.post(reverse('admin:formations_formation_add'), {
            'title': 'Nouvelle formation', 'description': 'Formation publiée depuis l’admin.',
            'category': Formation.Category.AI, 'duration': '2 jours',
            'level': Formation.Level.BEGINNER, '_save': 'Enregistrer',
        })
        self.assertEqual(response.status_code, 302)
        self.assertContains(self.client.get(reverse('formations:list')), 'Nouvelle formation')
