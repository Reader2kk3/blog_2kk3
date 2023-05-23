from django import template
from ..models import Post
from django.db.models import Count

from django.utils.safestring import mark_safe
import markdown

register = template.Library()

'''
Django предоставляет следующие вспомогательные функции, которые по-
зволяют легко создавать шаблонные теги:
• simple_tag: обрабатывает предоставленные данные и возвращает стро-
ковый литерал;
• inclusion_tag: обрабатывает предоставленные данные и возвращает
прорисованный шаблон.
'''

'''
Для того чтобы быть допустимой библиотекой тегов, в каждом содержащем
шаблонные теги модуле должна быть определена переменная с именем re-
gister. Эта переменная является экземпляром класса template.Library, и она
используется для регистрации шаблонных тегов и фильтров приложения.
'''

# В функцию был добавлен декоратор @register.simple_tag, чтобы зарегистрировать ее как простой тег
@register.simple_tag
def total_posts():
    return Post.published.count()

@register.inclusion_tag('latest_posts.html')
def show_latest_posts(count=5):
    latest_posts = Post.published.order_by('-publish')[:count]
    return {'latest_posts': latest_posts}

'''
C помощью функции annotate() фор-
мируется набор запросов QuerySet, чтобы агрегировать общее число ком-
ментариев к каждому посту.
Функция агрегирования Count используется для
сохранения количества комментариев в вычисляемом поле total_comments по
каждому объекту Post. Набор запросов QuerySet упорядочивается по вычис-
ляемому полю в убывающем порядке. Также предоставляется опциональная
переменная count, чтобы ограничивать общее число возвращаемых объектов.
'''
@register.simple_tag
def get_most_commented_posts(count=5):
    return Post.published.annotate(total_comments=Count('comments')
    ).order_by('-total_comments')[:count]


@register.filter(name='markdown')
def markdown_format(text):
    # mark_safe - помечает результат как безопасный для прорисовки в шаблоне исходный код HTML
    return mark_safe(markdown.markdown(text))