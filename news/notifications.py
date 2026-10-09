import json
import logging
from urllib.parse import urlsplit

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from pywebpush import WebPushException, webpush

from .models import NewsletterSubscriber, PushNotification, PushSubscription


logger = logging.getLogger(__name__)


def absolute_url(path):
    return f'{settings.SITE_URL.rstrip("/")}{path}'


def _safe_target_url(path):
    parsed = urlsplit(path or '/')
    site = urlsplit(settings.SITE_URL)
    if parsed.scheme or parsed.netloc:
        if parsed.scheme != site.scheme or parsed.netloc != site.netloc:
            return '/'
        path = parsed.path or '/'
        if parsed.query:
            path += f'?{parsed.query}'
        if parsed.fragment:
            path += f'#{parsed.fragment}'
    elif not path.startswith('/') or path.startswith('//'):
        return '/'
    return path


def create_push_notification(title, message, path='/', recipient=None, created_by=None, send_now=True):
    notification = PushNotification.objects.create(
        title=(title or 'Dunia')[:160],
        body=(message or '')[:500],
        target_url=_safe_target_url(path),
        recipient=recipient,
        created_by=created_by,
    )
    if send_now:
        transaction.on_commit(lambda notification_id=notification.pk: deliver_push_notification(notification_id))
    return notification


def send_push_notification(title, message, path, recipient=None):
    """Persist a Web Push campaign and deliver it to every matching device."""
    return create_push_notification(title, message, path, recipient=recipient)


def deliver_push_notification(notification_id):
    notification = PushNotification.objects.filter(pk=notification_id).first()
    if notification is None or notification.sent_at:
        return {'sent': False, 'delivered': 0, 'failed': 0}
    if not settings.WEBPUSH_ENABLED or not settings.WEBPUSH_VAPID_PUBLIC_KEY or not settings.WEBPUSH_VAPID_PRIVATE_KEY:
        logger.info('Web Push non configuré : notification %s conservée comme brouillon.', notification_id)
        return {'sent': False, 'delivered': 0, 'failed': 0}

    subscriptions = PushSubscription.objects.filter(is_active=True)
    if notification.recipient_id:
        subscriptions = subscriptions.filter(user_id=notification.recipient_id)

    payload = json.dumps({
        'title': notification.title,
        'body': notification.body,
        'url': absolute_url(notification.target_url),
        'tag': f'dunia-{notification.pk}',
    })
    delivered = 0
    failed = 0
    for subscription in subscriptions.iterator():
        try:
            webpush(
                subscription_info={
                    'endpoint': subscription.endpoint,
                    'keys': {'p256dh': subscription.p256dh, 'auth': subscription.auth},
                },
                data=payload,
                vapid_private_key=settings.WEBPUSH_VAPID_PRIVATE_KEY,
                vapid_claims={'sub': f'mailto:{settings.WEBPUSH_CONTACT_EMAIL}'},
                ttl=60 * 60,
                timeout=8,
            )
            delivered += 1
        except WebPushException as error:
            failed += 1
            response = getattr(error, 'response', None)
            status_code = getattr(response, 'status_code', None)
            if status_code in (404, 410):
                subscription.is_active = False
                subscription.save(update_fields=('is_active', 'updated_at'))
            logger.warning('Web Push refusé pour l’appareil %s (HTTP %s).', subscription.pk, status_code or 'inconnu')
        except Exception:
            failed += 1
            logger.exception('Erreur Web Push pour l’appareil %s.', subscription.pk)

    PushNotification.objects.filter(pk=notification.pk, sent_at__isnull=True).update(
        sent_at=timezone.now(),
        delivered_count=delivered,
        failed_count=failed,
    )
    return {'sent': True, 'delivered': delivered, 'failed': failed}


def notify_newsletter_subscribers(title, summary, path):
    subscribers = NewsletterSubscriber.objects.filter(is_active=True, is_confirmed=True)
    for subscriber in subscribers.iterator():
        unsubscribe_url = absolute_url(reverse('news:newsletter_unsubscribe', args=[subscriber.token]))
        message = (
            f'{summary}\n\nConsulter : {absolute_url(path)}\n\n'
            f"Pour ne plus recevoir ces messages, désinscrivez-vous : {unsubscribe_url}"
        )
        try:
            send_mail(title, message, settings.DEFAULT_FROM_EMAIL, [subscriber.email], fail_silently=True)
        except Exception:
            logger.exception('E-mail newsletter impossible pour un abonné Dunia.')
    send_push_notification(title, summary, path)