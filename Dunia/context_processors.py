from django.conf import settings

from news.notifications import webpush_is_configured


def site_features(request):
    push_enabled = webpush_is_configured()
    return {
        'APP_SHELL': True,
        'WEBPUSH_ENABLED': push_enabled,
        'WEBPUSH_PUBLIC_KEY': settings.WEBPUSH_VAPID_PUBLIC_KEY if push_enabled else '',
        'MOBILE_MONEY_INSTRUCTIONS': settings.MOBILE_MONEY_INSTRUCTIONS,
    }
