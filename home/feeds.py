import markdown
from django.contrib.syndication.views import Feed
from django.template.defaultfilters import truncatewords_html
from django.urls import reverse_lazy
from .models import Post

# reverse_lazy() используется для того, чтобы генерировать URL-адрес для атрибута link.

class LatestPostsFeed(Feed):
    title = 'My blog'
    link = reverse_lazy('home:post_list')
    description = 'New posts of my blog.'


    '''
    Метод items() извлекает включаемые в новостную ленту объекты. Мы из-
    влекаем последние пять опубликованных постов, которые затем будут вклю-
    чены в новостную ленту
    '''
    def items(self):
        return Post.published.all()[:5]

    '''
    Методы item_title(), item_description() и item_pubdate() будут получать
    каждый возвращаемый методом items() объект и возвращать заголовок, опи-
    сание и дату публикации по каждому элементу.
    '''
    def item_title(self, item):
        return item.title

    '''
    В методе item_description() используется функция markdown() , чтобы кон-
    вертировать контент в формате Markdown в формат HTML, и функция шаб-
    лонного фильтра truncatewords_html(), чтобы сокращать описание постов
    после 30 слов, избегая незакрытых HTML-тегов.
    '''
    def item_description(self, item):
        return truncatewords_html(markdown.markdown(item.body), 30)

    def item_pubdate(self, item):
        return item.publish