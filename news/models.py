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
