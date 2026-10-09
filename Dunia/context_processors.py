from django.conf import settings


def site_features(request):
    return {
        'APP_SHELL': True,
        'WEBPUSH_ENABLED': settings.WEBPUSH_ENABLED,
        'WEBPUSH_PUBLIC_KEY': settings.WEBPUSH_VAPID_PUBLIC_KEY if settings.WEBPUSH_ENABLED else '',
        'MOBILE_MONEY_INSTRUCTIONS': settings.MOBILE_MONEY_INSTRUCTIONS,
    }
