import json
from datetime import datetime, timezone as datetime_timezone
from unittest.mock import patch

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import News, NewsletterSubscriber, PushNotification, PushSubscription
from .notifications import create_push_notification, deliver_push_notification


@override_settings(DEBUG=True, EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
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

    @override_settings(TIME_ZONE='Africa/Kinshasa')
    def test_news_dates_use_kinshasa_local_time_in_public_pages(self):
        item = News.objects.create(title='Publication tardive', description='Date locale du test.')
        News.objects.filter(pk=item.pk).update(
            published_date=datetime(2026, 10, 8, 23, 30, tzinfo=datetime_timezone.utc),
        )

        with timezone.override('Africa/Kinshasa'):
            news_response = self.client.get(reverse('news:list'))
            home_response = self.client.get(reverse('home:index'))

        self.assertContains(news_response, '9 octobre 2026')
        self.assertContains(home_response, '9 octobre 2026')
        self.assertContains(news_response, 'datetime="2026-10-09T00:30:00+01:00"')

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

    def test_newsletter_requires_consent_and_double_opt_in(self):
        subscribe_url = reverse('news:newsletter_subscribe')
        response = self.client.post(subscribe_url, {
            'email': 'reader@example.com',
            'next': f"{reverse('news:list')}#newsletterFormCta",
        })
        self.assertRedirects(response, reverse('news:list'))
        self.assertFalse(NewsletterSubscriber.objects.exists())

        response = self.client.post(subscribe_url, {
            'email': 'reader@example.com',
            'consent': 'on',
            'next': f"{reverse('news:list')}#newsletterFormCta",
        })
        self.assertRedirects(response, reverse('news:list'))
        subscriber = NewsletterSubscriber.objects.get(email='reader@example.com')
        self.assertTrue(subscriber.is_active)
        self.assertFalse(subscriber.is_confirmed)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(str(subscriber.token), mail.outbox[0].body)

        response = self.client.get(reverse('news:newsletter_confirm', args=[subscriber.token]))
        self.assertEqual(response.status_code, 200)
        subscriber.refresh_from_db()
        self.assertTrue(subscriber.is_confirmed)

    def test_newsletter_unsubscribe_requires_confirmation_and_stops_future_mailings(self):
        subscriber = NewsletterSubscriber.objects.create(
            email='reader@example.com', is_active=True, is_confirmed=True,
        )
        unsubscribe_url = reverse('news:newsletter_unsubscribe', args=[subscriber.token])
        response = self.client.get(unsubscribe_url)
        self.assertEqual(response.status_code, 200)
        subscriber.refresh_from_db()
        self.assertTrue(subscriber.is_active)

        response = self.client.post(unsubscribe_url)
        self.assertEqual(response.status_code, 200)
        subscriber.refresh_from_db()
        self.assertFalse(subscriber.is_active)
        self.assertIsNotNone(subscriber.unsubscribed_at)

    def test_new_publication_notifies_confirmed_subscribers_after_commit(self):
        NewsletterSubscriber.objects.create(
            email='reader@example.com', is_active=True, is_confirmed=True,
        )
        with self.captureOnCommitCallbacks(execute=True):
            item = News.objects.create(title='Nouvelle annonce', description='À lire.')
        self.assertTrue(item.pk)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Nouvelle actualité Dunia', mail.outbox[0].subject)


@override_settings(DEBUG=True)
class PushNotificationsTests(TestCase):
    @override_settings(
        WEBPUSH_ENABLED=True,
        WEBPUSH_VAPID_PUBLIC_KEY='public-key-for-tests',
        WEBPUSH_VAPID_PRIVATE_KEY='private-key-for-tests',
    )
    def test_notification_settings_use_the_compact_app_navigation(self):
        response = self.client.get(reverse('news:notifications_settings'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="appBottomNav"')
        self.assertContains(response, 'Activer sur cet appareil')
        self.assertNotContains(response, '<footer')
        self.assertNotContains(response, 'id="mobileMenu"')

    @override_settings(
        WEBPUSH_ENABLED=True,
        WEBPUSH_VAPID_PUBLIC_KEY='public-key-for-tests',
        WEBPUSH_VAPID_PRIVATE_KEY='private-key-for-tests',
    )
    def test_subscriptions_are_saved_per_device_and_linked_to_the_signed_in_user(self):
        user = get_user_model().objects.create_user('pushlearner', 'push@example.com', 'test-password-123')
        self.client.force_login(user)
        payload = {
            'endpoint': 'https://push.example.test/send/device-one',
            'keys': {'p256dh': 'B' * 65, 'auth': 'a' * 22},
        }

        first_response = self.client.post(
            reverse('news:push_subscribe'), json.dumps(payload), content_type='application/json',
        )
        second_response = self.client.post(
            reverse('news:push_subscribe'), json.dumps(payload), content_type='application/json',
        )

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(PushSubscription.objects.count(), 1)
        subscription = PushSubscription.objects.get()
        self.assertEqual(subscription.user, user)
        self.assertTrue(subscription.is_active)

        payload['endpoint'] = 'https://push.example.test/send/device-two'
        self.client.post(reverse('news:push_subscribe'), json.dumps(payload), content_type='application/json')
        self.assertEqual(PushSubscription.objects.count(), 2)

    @override_settings(
        WEBPUSH_ENABLED=True,
        WEBPUSH_VAPID_PUBLIC_KEY='public-key-for-tests',
        WEBPUSH_VAPID_PRIVATE_KEY='private-key-for-tests',
    )
    def test_push_subscription_rejects_http_endpoints_and_invalid_keys(self):
        response = self.client.post(
            reverse('news:push_subscribe'),
            json.dumps({'endpoint': 'http://push.example.test/subscription', 'keys': {}}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(PushSubscription.objects.count(), 0)

    @override_settings(
        WEBPUSH_ENABLED=True,
        WEBPUSH_VAPID_PUBLIC_KEY='',
        WEBPUSH_VAPID_PRIVATE_KEY='',
    )
    def test_push_remains_disabled_when_vapid_keys_are_missing(self):
        settings_response = self.client.get(reverse('news:notifications_settings'))
        subscribe_response = self.client.post(
            reverse('news:push_subscribe'),
            json.dumps({
                'endpoint': 'https://push.example.test/send/device-one',
                'keys': {'p256dh': 'B' * 65, 'auth': 'a' * 22},
            }),
            content_type='application/json',
        )

        self.assertContains(settings_response, 'Les notifications du serveur ne sont pas encore configurées.')
        self.assertNotContains(settings_response, 'Activer sur cet appareil')
        self.assertEqual(subscribe_response.status_code, 503)
        self.assertFalse(PushSubscription.objects.exists())

    def test_device_can_disable_its_subscription(self):
        subscription = PushSubscription.objects.create(
            endpoint='https://push.example.test/send/device-to-disable',
            p256dh='B' * 65,
            auth='a' * 22,
        )

        response = self.client.post(
            reverse('news:push_unsubscribe'),
            json.dumps({'endpoint': subscription.endpoint}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        subscription.refresh_from_db()
        self.assertFalse(subscription.is_active)

    @override_settings(
        WEBPUSH_ENABLED=True,
        WEBPUSH_VAPID_PUBLIC_KEY='public-key-for-tests',
        WEBPUSH_VAPID_PRIVATE_KEY='private-key-for-tests',
    )
    @patch('news.notifications.webpush')
    def test_backend_sends_campaign_only_to_the_recipient_account_devices(self, mock_webpush):
        recipient = get_user_model().objects.create_user('pushrecipient', password='test-password-123')
        other_user = get_user_model().objects.create_user('pushother', password='test-password-123')
        recipient_subscription = PushSubscription.objects.create(
            endpoint='https://push.example.test/send/recipient',
            p256dh='B' * 65,
            auth='a' * 22,
            user=recipient,
        )
        PushSubscription.objects.create(
            endpoint='https://push.example.test/send/other',
            p256dh='C' * 65,
            auth='b' * 22,
            user=other_user,
        )
        notification = create_push_notification(
            'Cours disponible', 'La formation est prête.', '/formations/',
            recipient=recipient, send_now=False,
        )

        result = deliver_push_notification(notification.pk)

        self.assertEqual(result, {'sent': True, 'delivered': 1, 'failed': 0})
        self.assertEqual(mock_webpush.call_count, 1)
        sent_subscription = mock_webpush.call_args.kwargs['subscription_info']
        self.assertEqual(sent_subscription['endpoint'], recipient_subscription.endpoint)
        notification.refresh_from_db()
        self.assertIsNotNone(notification.sent_at)
        self.assertEqual(notification.delivered_count, 1)

    @override_settings(
        WEBPUSH_ENABLED=True,
        WEBPUSH_VAPID_PUBLIC_KEY='public-key-for-tests',
        WEBPUSH_VAPID_PRIVATE_KEY='private-key-for-tests',
    )
    @patch('news.notifications.webpush')
    def test_campaign_without_active_devices_remains_pending(self, mock_webpush):
        notification = create_push_notification(
            'Formation disponible', 'Une nouvelle formation est prête.', '/formations/', send_now=False,
        )

        result = deliver_push_notification(notification.pk)

        self.assertEqual(result, {'sent': False, 'delivered': 0, 'failed': 0})
        mock_webpush.assert_not_called()
        notification.refresh_from_db()
        self.assertIsNone(notification.sent_at)
        self.assertEqual(notification.delivered_count, 0)
        self.assertEqual(notification.failed_count, 0)

    @override_settings(
        WEBPUSH_ENABLED=True,
        WEBPUSH_VAPID_PUBLIC_KEY='public-key-for-tests',
        WEBPUSH_VAPID_PRIVATE_KEY='private-key-for-tests',
    )
    @patch('news.notifications.webpush')
    def test_fully_failed_campaign_can_be_retried(self, mock_webpush):
        PushSubscription.objects.create(
            endpoint='https://push.example.test/send/retry-device',
            p256dh='B' * 65,
            auth='a' * 22,
        )
        notification = create_push_notification(
            'Formation disponible', 'Une nouvelle formation est prête.', '/formations/', send_now=False,
        )
        mock_webpush.side_effect = OSError('Temporary push service failure')

        failed_result = deliver_push_notification(notification.pk)

        self.assertEqual(failed_result, {'sent': False, 'delivered': 0, 'failed': 1})
        notification.refresh_from_db()
        self.assertIsNone(notification.sent_at)
        self.assertEqual(notification.failed_count, 1)

        mock_webpush.side_effect = None
        retry_result = deliver_push_notification(notification.pk)

        self.assertEqual(retry_result, {'sent': True, 'delivered': 1, 'failed': 0})
        self.assertEqual(mock_webpush.call_count, 2)
        notification.refresh_from_db()
        self.assertIsNotNone(notification.sent_at)
        self.assertEqual(notification.delivered_count, 1)
        self.assertEqual(notification.failed_count, 0)

    @override_settings(
        WEBPUSH_ENABLED=True,
        WEBPUSH_VAPID_PUBLIC_KEY='public-key-for-tests',
        WEBPUSH_VAPID_PRIVATE_KEY='private-key-for-tests',
    )
    @patch('news.notifications.webpush')
    def test_new_news_is_sent_to_each_subscribed_device_after_commit(self, mock_webpush):
        PushSubscription.objects.create(
            endpoint='https://push.example.test/send/news-reader-one',
            p256dh='B' * 65,
            auth='a' * 22,
        )
        with self.captureOnCommitCallbacks(execute=True):
            item = News.objects.create(title='Nouvelle date', description='Une actualité à découvrir.')

        notification = PushNotification.objects.get(title__contains=item.title)
        notification.refresh_from_db()
        self.assertEqual(mock_webpush.call_count, 1)
        self.assertIsNotNone(notification.sent_at)
        self.assertEqual(notification.delivered_count, 1)
