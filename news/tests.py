from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import News


@override_settings(DEBUG=True)
class NewsPagesTests(TestCase):
    def test_empty_news_page(self):
        response = self.client.get(reverse('news:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Aucune actualité trouvée')
        self.assertNotContains(response, 'class="news-card')

    def test_news_are_newest_first_with_existing_card_structure(self):
        older = News.objects.create(title='Partenariat', description='Une nouvelle collaboration.',
                                    category=News.Category.ADVERTISEMENT)
        latest = News.objects.create(title='Atelier Python', description='Une session pratique.',
                                     category=News.Category.EVENT, image='news_images/atelier.png')
        response = self.client.get(reverse('news:list'))
        self.assertEqual(list(response.context['news']), [latest, older])
        for text in [latest.title, older.description, 'md:col-span-2 lg:col-span-2',
                     'class="news-overlay"', 'data-category="evenement"',
                     '/media/news_images/atelier.png', 'from-blue-600 to-blue-800']:
            self.assertContains(response, text)

    def test_missing_image_uses_static_fallback_and_content_is_escaped(self):
        News.objects.create(title='<script>alert(1)</script>', description='News without an image')
        response = self.client.get(reverse('news:list'))
        self.assertContains(response, '/static/images/hero-section.jpeg')
        self.assertContains(response, '&lt;script&gt;alert(1)&lt;/script&gt;')
        self.assertNotContains(response, '<script>alert(1)</script>')

    def test_admin_can_publish_and_search_news(self):
        self.assertTrue(admin.site.is_registered(News))
        user = get_user_model().objects.create_superuser('editor', 'editor@example.com', 'test-password')
        self.client.force_login(user)
        response = self.client.post(reverse('admin:news_news_add'), {
            'title': 'Annonce publiée', 'description': 'Contenu recherchable unique',
            'category': News.Category.ANNOUNCEMENT, '_save': 'Enregistrer',
        })
        self.assertEqual(response.status_code, 302)
        self.assertContains(self.client.get(reverse('news:list')), 'Annonce publiée')
        response = self.client.get(reverse('admin:news_news_changelist'), {'q': 'recherchable'})
        self.assertContains(response, 'Annonce publiée')
