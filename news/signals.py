from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

from formations.models import Formation

from .models import News
from .notifications import notify_newsletter_subscribers


@receiver(post_save, sender=News)
def announce_new_news(sender, instance, created, **kwargs):
    if not created:
        return
    path = reverse('news:list')
    title = f"Nouvelle actualité Dunia : {instance.title}"
    summary = instance.description[:240]
    transaction.on_commit(lambda: notify_newsletter_subscribers(title, summary, path))


@receiver(post_save, sender=Formation)
def announce_new_formation(sender, instance, created, **kwargs):
    if not created:
        return
    path = reverse('formations:detail', args=[instance.pk])
    title = f"Nouvelle formation Dunia : {instance.title}"
    summary = instance.description[:240]
    transaction.on_commit(lambda: notify_newsletter_subscribers(title, summary, path))