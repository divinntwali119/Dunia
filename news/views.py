import json
import re
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.db import IntegrityError
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from .forms import NewsletterSubscribeForm
from .models import News, NewsletterSubscriber, PushSubscription
from .notifications import absolute_url, webpush_is_configured


PUSH_KEY_PATTERN = re.compile(r'^[A-Za-z0-9_-]{8,255}$')


def news(request: HttpRequest) -> HttpResponse:
    return render(request, 'news/news.html', {'news': News.objects.all()})


@ensure_csrf_cookie
def notifications_settings(request: HttpRequest) -> HttpResponse:
    push_enabled = webpush_is_configured()
    return render(request, 'news/notifications.html', {
        'push_enabled': push_enabled,
        'push_public_key': settings.WEBPUSH_VAPID_PUBLIC_KEY if push_enabled else '',
    })


def _push_payload(request):
    try:
        return json.loads(request.body or b'{}')
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


@require_POST
def push_subscribe(request: HttpRequest) -> JsonResponse:
    if not webpush_is_configured():
        return JsonResponse({'ok': False, 'error': 'Les notifications push ne sont pas encore configurées.'}, status=503)

    payload = _push_payload(request)
    if not isinstance(payload, dict):
        return JsonResponse({'ok': False, 'error': 'Données d’abonnement invalides.'}, status=400)
    endpoint = payload.get('endpoint', '')
    keys = payload.get('keys') or {}
    parsed_endpoint = urlsplit(endpoint) if isinstance(endpoint, str) else None
    p256dh = keys.get('p256dh', '') if isinstance(keys, dict) else ''
    auth = keys.get('auth', '') if isinstance(keys, dict) else ''
    if (
        not parsed_endpoint
        or parsed_endpoint.scheme != 'https'
        or not parsed_endpoint.netloc
        or len(endpoint) > 2048
        or not isinstance(p256dh, str)
        or not isinstance(auth, str)
        or not PUSH_KEY_PATTERN.fullmatch(p256dh)
        or not PUSH_KEY_PATTERN.fullmatch(auth)
    ):
        return JsonResponse({'ok': False, 'error': 'Le navigateur a envoyé un abonnement incomplet.'}, status=400)

    subscription, _ = PushSubscription.objects.update_or_create(
        endpoint=endpoint,
        defaults={
            'p256dh': p256dh,
            'auth': auth,
            'user': request.user if request.user.is_authenticated else None,
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500],
            'is_active': True,
        },
    )
    return JsonResponse({'ok': True, 'subscription_id': subscription.pk})


@require_POST
def push_unsubscribe(request: HttpRequest) -> JsonResponse:
    payload = _push_payload(request)
    endpoint = payload.get('endpoint', '') if isinstance(payload, dict) else ''
    if not isinstance(endpoint, str) or not endpoint:
        return JsonResponse({'ok': False, 'error': 'Abonnement manquant.'}, status=400)
    PushSubscription.objects.filter(endpoint=endpoint, is_active=True).update(is_active=False)
    return JsonResponse({'ok': True})


def _newsletter_return_url(request):
    target = request.POST.get('next', '')
    if target and url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}):
        parsed = urlsplit(target)
        return parsed.path or reverse('home:index')
    return reverse('home:index')


@require_POST
def newsletter_subscribe(request):
    form = NewsletterSubscribeForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Vérifiez votre adresse e-mail et cochez la case de consentement.')
        return redirect(_newsletter_return_url(request))

    email = form.cleaned_data['email'].strip().lower()
    try:
        subscriber, created = NewsletterSubscriber.objects.get_or_create(email=email)
    except IntegrityError:
        subscriber = NewsletterSubscriber.objects.get(email=email)
        created = False
    if subscriber.is_active and subscriber.is_confirmed:
        messages.info(request, 'Cette adresse est déjà abonnée aux actualités Dunia.')
        return redirect(_newsletter_return_url(request))

    if not created:
        subscriber.is_active = True
        subscriber.is_confirmed = False
        subscriber.consented_at = timezone.now()
        subscriber.unsubscribed_at = None
        subscriber.save(update_fields=('is_active', 'is_confirmed', 'consented_at', 'unsubscribed_at'))

    confirmation_url = absolute_url(reverse('news:newsletter_confirm', args=[subscriber.token]))
    try:
        send_mail(
            'Confirmez votre inscription à la newsletter Dunia',
            f"Pour confirmer votre adresse et recevoir les actualités Dunia, ouvrez ce lien :\n\n"
            f"{confirmation_url}\n\nSi vous n'êtes pas à l'origine de cette demande, ignorez ce message.",
            settings.DEFAULT_FROM_EMAIL,
            [subscriber.email],
            fail_silently=False,
        )
    except Exception:
        messages.warning(
            request,
            "Votre demande est enregistrée, mais l'envoi du message de confirmation a échoué. "
            'Réessayez plus tard ou contactez Dunia.',
        )
    else:
        messages.success(request, 'Un e-mail vous a été envoyé : confirmez votre adresse pour finaliser l’abonnement.')
    return redirect(_newsletter_return_url(request))


def newsletter_confirm(request, token):
    subscriber = get_object_or_404(NewsletterSubscriber, token=token, is_active=True)
    if not subscriber.is_confirmed:
        subscriber.is_confirmed = True
        subscriber.confirmed_at = timezone.now()
        subscriber.save(update_fields=('is_confirmed', 'confirmed_at'))
    return render(request, 'news/newsletter_confirmed.html', {'subscriber': subscriber})


def newsletter_unsubscribe(request, token):
    subscriber = get_object_or_404(NewsletterSubscriber, token=token)
    if request.method == 'POST':
        if subscriber.is_active:
            subscriber.is_active = False
            subscriber.unsubscribed_at = timezone.now()
            subscriber.save(update_fields=('is_active', 'unsubscribed_at'))
        return render(request, 'news/newsletter_unsubscribed.html', {'subscriber': subscriber})
    return render(request, 'news/newsletter_unsubscribe.html', {'subscriber': subscriber})
