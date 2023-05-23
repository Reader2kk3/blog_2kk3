from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse
from taggit.managers import TaggableManager

class PublishedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=Post.Status.PUBLISHED)


class Post(models.Model):

    class Status(models.TextChoices):
        DRAFT = 'DF', 'Draft'
        PUBLISHED = 'PB', 'Published'

    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор", related_name='home_post')
    title = models.CharField("Название", max_length=255)
    slug = models.SlugField("Слаг", max_length=255, unique_for_date='publish')
    body = models.TextField("Описание", max_length=2500)
    publish = models.DateTimeField("Дата публикации", default=timezone.now)
    created = models.DateTimeField("Дата создания", auto_now_add=True)
    updated = models.DateTimeField("Дата редактирования", auto_now=True)
    status = models.CharField("Статус", max_length=2, choices=Status.choices, default=Status.DRAFT)
    tags = TaggableManager()

    objects = models.Manager()
    published = PublishedManager()

    class Meta:
        ordering = ['-publish']
        indexes = [models.Index(fields=['-publish']),]

    def __str__(self):
        return str(self.title)

    def get_absolute_url(self):
        return reverse('home:post_detail', args=[self.publish.year,
                                                self.publish.month, 
                                                self.publish.day,
                                                self.slug])


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    name = models.CharField("Название", max_length=80)
    email = models.EmailField("Почта")
    body = models.TextField("Комментарий")
    created = models.DateTimeField("Дата создания", auto_now_add=True)
    updated = models.DateTimeField("Дата обновления", auto_now=True)
    active = models.BooleanField("Статус", default=True)

    class Meta:
        ordering = ['created']
        indexes = [models.Index(fields=['created']),]

    def __str__(self):
        return f'Comment by {self.name} on {self.post}'