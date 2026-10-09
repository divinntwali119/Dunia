import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

class News(models.Model):
    class Category(models.TextChoices):
        ANNOUNCEMENT = 'annonce', 'Annonce'
        FORMATION = 'formation', 'Formation'
        EVENT = 'evenement', 'Événement'
        ADVERTISEMENT = 'publicite', 'Publicité'

    title = models.CharField('titre', max_length=300)
    description = models.TextField('description')
    published_date = models.DateTimeField('date de publication', auto_now_add=True)
    image = models.ImageField('image', upload_to='news_images/', blank=True, null=True)
    category = models.CharField('catégorie', max_length=20, choices=Category.choices, default=Category.ANNOUNCEMENT)
    
    class Meta:
        ordering = ['-published_date', '-pk']
        verbose_name = "actualité"
        verbose_name_plural = "actualités"
    def __str__(self):
        return self.title


class PushSubscription(models.Model):
    endpoint = models.URLField('point de livraison push', max_length=2048, unique=True)
    p256dh = models.CharField('clé publique de chiffrement', max_length=255)
    auth = models.CharField('secret de chiffrement', max_length=255)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='push_subscriptions',
        verbose_name='utilisateur',
    )
    user_agent = models.CharField('navigateur et appareil', max_length=500, blank=True)
    is_active = models.BooleanField('actif', default=True, db_index=True)
    created_at = models.DateTimeField('inscrit le', auto_now_add=True)
    updated_at = models.DateTimeField('mis à jour le', auto_now=True)

    class Meta:
        ordering = ['-updated_at', '-pk']
        verbose_name = 'appareil avec notifications push'
        verbose_name_plural = 'appareils avec notifications push'

    def __str__(self):
        return f'{self.user or "Appareil anonyme"} — {self.endpoint[:64]}'


class PushNotification(models.Model):
    title = models.CharField('titre', max_length=160)
    body = models.CharField('message', max_length=500)
    target_url = models.CharField('page à ouvrir', max_length=2048, default='/')
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='push_notifications',
        verbose_name='destinataire (vide : tous les appareils)',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_push_notifications',
        verbose_name='créée par',
    )
    created_at = models.DateTimeField('créée le', auto_now_add=True)
    sent_at = models.DateTimeField('envoyée le', null=True, blank=True)
    delivered_count = models.PositiveIntegerField('envois acceptés', default=0)
    failed_count = models.PositiveIntegerField('échecs', default=0)

    class Meta:
        ordering = ['-created_at', '-pk']
        verbose_name = 'notification push'
        verbose_name_plural = 'notifications push'

    def clean(self):
        if not self.target_url.startswith('/') or self.target_url.startswith(('//', '/\\')):
            raise ValidationError({'target_url': 'Choisissez un chemin interne commençant par /.'})

    def __str__(self):
        return self.title


class NewsletterSubscriber(models.Model):
    email = models.EmailField('adresse e-mail', unique=True)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    is_active = models.BooleanField('abonné', default=True)
    is_confirmed = models.BooleanField('adresse confirmée', default=False)
    consented_at = models.DateTimeField('consentement donné le', auto_now_add=True)
    confirmed_at = models.DateTimeField('adresse confirmée le', null=True, blank=True)
    unsubscribed_at = models.DateTimeField('désinscrit le', null=True, blank=True)

    class Meta:
        ordering = ['-consented_at', '-pk']
        verbose_name = 'abonné à la newsletter'
        verbose_name_plural = 'abonnés à la newsletter'

    def __str__(self):
        return self.email
