from django.db import models

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

    title = models.CharField('titre', max_length=300)
    description = models.TextField('description')
    image = models.ImageField('image', upload_to='formation_images/', blank=True)
    category = models.CharField('catégorie', max_length=20, choices=Category.choices, default=Category.OTHER)
    duration = models.CharField('durée', max_length=100, blank=True)
    level = models.CharField('niveau', max_length=20, choices=Level.choices, default=Level.BEGINNER)
    created_at = models.DateTimeField('date de création', auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-pk']
        verbose_name = 'formation'
        verbose_name_plural = 'formations'

    def __str__(self):
        return self.title
