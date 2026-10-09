import uuid
from decimal import Decimal
from urllib.parse import parse_qs, urlparse

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from .storage import PrivateMediaStorage

class Formation(models.Model):
    class Category(models.TextChoices):
        DEVELOPMENT = 'developpement', 'Développement'
        AI = 'ia', 'Intelligence artificielle'
        DESIGN = 'design', 'Design'
        OTHER = 'autres', 'Autres'

    class Level(models.TextChoices):
        BEGINNER = 'debutant', 'Débutant'
        INTERMEDIATE = 'intermediaire', 'Intermédiaire'
        ADVANCED = 'avance', 'Avancé'
        ALL = 'tous', 'Tous niveaux'

    class DeliveryMode(models.TextChoices):
        ONLINE = 'en_ligne', 'En ligne'
        IN_PERSON = 'presentiel', 'En présentiel'
        HYBRID = 'hybride', 'Hybride'

    class Currency(models.TextChoices):
        USD = 'USD', 'USD'
        CDF = 'CDF', 'CDF'

    title = models.CharField('titre', max_length=300)
    description = models.TextField('description')
    image = models.ImageField('image', upload_to='formation_images/', blank=True)
    category = models.CharField('catégorie', max_length=20, choices=Category.choices, default=Category.OTHER)
    duration = models.CharField('durée', max_length=100, blank=True)
    level = models.CharField('niveau', max_length=20, choices=Level.choices, default=Level.BEGINNER)
    delivery_mode = models.CharField('format', max_length=20, choices=DeliveryMode.choices,
                                     default=DeliveryMode.ONLINE)
    instructor = models.CharField('formateur', max_length=200, blank=True)
    start_date = models.DateField('date de début', null=True, blank=True)
    end_date = models.DateField('date de fin', null=True, blank=True)
    location = models.CharField('lieu ou lien de formation', max_length=300, blank=True)
    price = models.DecimalField('prix', max_digits=10, decimal_places=2, default=Decimal('0.00'),
                                validators=[MinValueValidator(Decimal('0.00'))])
    currency = models.CharField('devise', max_length=3, choices=Currency.choices, default=Currency.USD)
    capacity = models.PositiveIntegerField('nombre de places', null=True, blank=True,
                                           help_text='Laisser vide pour un nombre de places illimité.')
    created_at = models.DateTimeField('date de création', auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-pk']
        verbose_name = 'formation'
        verbose_name_plural = 'formations'

    def __str__(self):
        return self.title


class Lesson(models.Model):
    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name='lessons',
                                  verbose_name='formation')
    title = models.CharField('titre', max_length=200)
    summary = models.CharField('résumé', max_length=300, blank=True)
    content = models.TextField('contenu', blank=True)
    video_url = models.URLField('lien vidéo', blank=True)
    order = models.PositiveIntegerField('ordre', default=0)
    is_published = models.BooleanField('publiée', default=True)
    created_at = models.DateTimeField('date de création', auto_now_add=True)

    class Meta:
        ordering = ['order', 'pk']
        verbose_name = 'leçon'
        verbose_name_plural = 'leçons'

    def __str__(self):
        return f'{self.formation}: {self.title}'

    @property
    def video_embed_url(self):
        if not self.video_url:
            return ''
        parsed = urlparse(self.video_url)
        host = (parsed.hostname or '').lower()
        video_id = ''
        if host in {'youtube.com', 'www.youtube.com', 'm.youtube.com', 'youtube-nocookie.com'}:
            if parsed.path == '/watch':
                video_id = parse_qs(parsed.query).get('v', [''])[0]
            elif parsed.path.startswith(('/embed/', '/shorts/')):
                parts = [part for part in parsed.path.split('/') if part]
                video_id = parts[1] if len(parts) > 1 else ''
            if video_id and all(char.isalnum() or char in '_-' for char in video_id):
                return f'https://www.youtube-nocookie.com/embed/{video_id}'
        elif host in {'youtu.be', 'www.youtu.be'}:
            video_id = parsed.path.strip('/').split('/')[0]
            if video_id and all(char.isalnum() or char in '_-' for char in video_id):
                return f'https://www.youtube-nocookie.com/embed/{video_id}'
        elif host in {'vimeo.com', 'www.vimeo.com', 'player.vimeo.com'}:
            segments = [segment for segment in parsed.path.split('/') if segment]
            video_id = segments[-1] if segments else ''
            if video_id.isdigit():
                return f'https://player.vimeo.com/video/{video_id}'
        return ''


class LessonResource(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='resources',
                               verbose_name='leçon')
    title = models.CharField('titre', max_length=200)
    file = models.FileField('fichier', upload_to='protected_resources/', blank=True,
                            storage=PrivateMediaStorage())
    external_url = models.URLField('lien externe', blank=True)

    class Meta:
        verbose_name = 'ressource de leçon'
        verbose_name_plural = 'ressources de leçon'

    def __str__(self):
        return self.title


class Enrollment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'en_attente', 'En attente de paiement'
        CONFIRMED = 'confirmee', 'Confirmée'
        WAITLISTED = 'liste_attente', "Liste d'attente"
        CANCELLED = 'annulee', 'Annulée'
        COMPLETED = 'terminee', 'Terminée'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrollments',
                             verbose_name='apprenant')
    formation = models.ForeignKey(Formation, on_delete=models.PROTECT, related_name='enrollments',
                                  verbose_name='formation')
    phone = models.CharField('téléphone / WhatsApp', max_length=32)
    status = models.CharField('statut', max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField('date de demande', auto_now_add=True)
    updated_at = models.DateTimeField('dernière mise à jour', auto_now=True)

    class Meta:
        ordering = ['-created_at', '-pk']
        verbose_name = 'inscription'
        verbose_name_plural = 'inscriptions'
        constraints = [
            models.UniqueConstraint(fields=['user', 'formation'], name='unique_student_formation'),
        ]

    def __str__(self):
        return f'{self.user} — {self.formation}'

    @property
    def progress_percent(self):
        lessons = self.formation.lessons.filter(is_published=True)
        total = lessons.count()
        if total == 0:
            return 0
        completed = LessonProgress.objects.filter(user=self.user, lesson__in=lessons, completed=True).count()
        return round(completed * 100 / total)

    @property
    def pending_payment(self):
        return next(
            (payment for payment in self.payments.all() if payment.status == Payment.Status.PENDING),
            None,
        )


class Payment(models.Model):
    class Provider(models.TextChoices):
        AIRTEL = 'airtel_money', 'Airtel Money'
        ORANGE = 'orange_money', 'Orange Money'
        MPESA = 'mpesa', 'M-Pesa'
        AFRIMONEY = 'afrimoney', 'Afrimoney'
        OTHER = 'autre', 'Autre'

    class Status(models.TextChoices):
        PENDING = 'en_attente', 'À vérifier'
        APPROVED = 'approuve', 'Approuvé'
        REJECTED = 'rejete', 'Rejeté'
        CANCELLED = 'annule', 'Annulé'

    enrollment = models.ForeignKey(Enrollment, on_delete=models.PROTECT, related_name='payments',
                                   verbose_name='inscription')
    amount = models.DecimalField('montant', max_digits=10, decimal_places=2,
                                 validators=[MinValueValidator(Decimal('0.01'))])
    currency = models.CharField('devise', max_length=3, choices=Formation.Currency.choices)
    provider = models.CharField('opérateur', max_length=20, choices=Provider.choices)
    transaction_reference = models.CharField('référence de transaction', max_length=128)
    proof = models.ImageField('preuve de paiement', upload_to='payment_proofs/', blank=True,
                              storage=PrivateMediaStorage())
    status = models.CharField('statut', max_length=12, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField('date de soumission', auto_now_add=True)
    reviewed_at = models.DateTimeField('date de vérification', null=True, blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='reviewed_payments', verbose_name='vérifié par')

    class Meta:
        ordering = ['-created_at', '-pk']
        verbose_name = 'paiement Mobile Money'
        verbose_name_plural = 'paiements Mobile Money'
        constraints = [
            models.UniqueConstraint(fields=['transaction_reference'],
                                    condition=~Q(transaction_reference=''),
                                    name='unique_mobile_money_reference'),
        ]

    def __str__(self):
        return f'{self.transaction_reference} — {self.get_status_display()}'


class LessonProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='lesson_progress',
                             verbose_name='apprenant')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='progresses', verbose_name='leçon')
    completed = models.BooleanField('terminée', default=False)
    completed_at = models.DateTimeField('terminée le', null=True, blank=True)

    class Meta:
        verbose_name = 'progression de leçon'
        verbose_name_plural = 'progressions de leçon'
        constraints = [
            models.UniqueConstraint(fields=['user', 'lesson'], name='unique_student_lesson_progress'),
        ]

    def __str__(self):
        return f'{self.user} — {self.lesson}'


class Certificate(models.Model):
    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE, related_name='certificate',
                                      verbose_name='inscription')
    certificate_number = models.UUIDField('numéro de vérification', default=uuid.uuid4, unique=True, editable=False)
    issued_at = models.DateTimeField('date de délivrance', auto_now_add=True)

    class Meta:
        ordering = ['-issued_at']
        verbose_name = 'attestation'
        verbose_name_plural = 'attestations'

    def __str__(self):
        return f'Attestation {self.certificate_number}'
