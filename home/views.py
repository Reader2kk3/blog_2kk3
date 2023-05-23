from django.shortcuts import render, get_object_or_404
from .models import Post, Comment
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.views.generic import ListView
from .forms import EmailPostForm, CommentForm, SearchForm
from django.core.mail import send_mail

from django.views.decorators.http import require_POST
from taggit.models import Tag
from django.db.models import Count

from django.contrib.postgres.search import SearchVector, SearchQuery
from django.contrib.postgres.search import TrigramSimilarity

@require_POST
def post_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    comment = None

    # Комментарий был отправлен
    form = CommentForm(data=request.POST)

    if form.is_valid():
        # Создать объект класс Comment, не сохраняя его в БД
        comment = form.save(commit=False)
        # Назначить пост комментарию
        comment.post = post
        # Сохранить комментарий в БД
        comment.save()

    context = {'post': post, 'form': form, 'comment': comment}
    return render(request, 'home/comment.html', context)


def post_share(request, post_id):
    # Извлечь пост по идентификатору id
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    sent = False

    if request.method == 'POST':
        # Форма была передана на обработку
        form = EmailPostForm(request.POST)

        if form.is_valid():
            # Поля успешно прошли валидацию
            cd = form.cleaned_data
            # ... отправить электронное письмо
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{cd['name']} recommends you read {post.title}"
            message = f"Read {post.title} at {post_url}\n\n" \
                      f"{cd['name']}\'s comments: {cd['comments']}"
            # to -> forms.py
            send_mail(subject, message, cd['email'], [cd['to']])
            sent = True

    else:
        form = EmailPostForm()

    context = {'post': post, 'form': form, 'sent': sent}
    return render(request, 'home/share.html', context)


class PostListViews(ListView):
    queryset = post_list = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 2
    template_name = 'home/list.html'


def post_list(request, tag_slug=None):
    post_list = Post.published.all()

    tag = None
    # извлекающий все опубликованные посты, и если имеется слаг данного тега
    if tag_slug:
        # то берется объект Tag с данным слагом
        tag = get_object_or_404(Tag, slug=tag_slug)
        # операция __in - поиск по полю
        post_list = post_list.filter(tags__in=[tag])

    # Постраничная разбивка с 2 постами на страницу
    paginator = Paginator(post_list, 2)
    page_number = request.GET.get('page')

    try: 
        posts = paginator.page(page_number)

    except PageNotAnInteger:
        # Если page_number не целое число, то выдать первую страницу
        posts = paginator.page(1)

    except EmptyPage:
        # Если page_number находится вне диапазоне, то выдать последнюю страницу 
        posts = paginator.page(paginator.num_pages)
    
    context = {'posts': posts, 'tag': tag}
    return render(request, 'home/list.html', context)

def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post,
                            status=Post.Status.PUBLISHED,
                            slug=post,
                            publish__year=year,
                            publish__month=month, 
                            publish__day=day)

    # Список активных комментариев к этому посту | comments -> models.py
    comments = post.comments.filter(active=True)
    # Форма для комментирования пользователями
    form = CommentForm()
    
    # Список схожих постов
    ''' 
    Извлекается список идентификаторов тегов текущего поста
    Набор запросов QuerySet values_list() возвращает кортежи со
    значениями заданных полей. Ему передается параметр flat=True, чтобы
    получить одиночные значения, такие как [1, 2, 3, ...], а не одноэле-
    ментые кортежи, такие как [(1,), (2,), (3,) ...]
    '''
    post_tags_ids = post.tags.values_list('id', flat=True)

    ''' 
    Берутся все посты, содержащие любой из этих тегов, за исключением текущего поста 
    '''
    similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)

    '''
    Применяется функция агрегирования Count. Ее работа – генерировать
    вычисляемое поле – same_tags, – которое содержит число тегов, общих
    со всеми запрошенными тегами

    Результат упорядочивается по числу общих тегов (в убывающем по-
    рядке) и по publish, чтобы сначала отображать последние посты для
    постов с одинаковым числом общих тегов. Результат нарезается, чтобы
    получить только первые четыре поста
    '''
    similar_posts = similar_posts.annotate(same_tags=Count('tags'))\
                            .order_by('-same_tags','-publish')[:4]

    context = {'post': post, 'comments': comments, 'form': form, 'similar_posts': similar_posts}
    return render(request, 'home/detail.html', context) 

# Поисковик
def post_search(request):
    # Создается экземпляр формы SearchForm
    form = SearchForm()
    # Поиск по умолчанию
    query = None
    # Возврат списка (поиска)
    results = []

    # Для проверки того, что форма была передана на обработку,
    # в словаре request.GET отыскивается параметр query
    if 'query' in request.GET:
        # Форма отправляется методом GET, чтобы результирующий URL-адрес содержал 
        # параметр query и им было легко делиться.
        form = SearchForm(request.GET)

        # Если форма валидна, то 
        if form.is_valid():
            # cleaned_data - валидация пользовательского ввода
            query = form.cleaned_data['query']

            
            # Если форма валидна, то с помощью конкретно-прикладного экземпляра SearchVector, 
            # сформированного с использованием полей title и body,
            # выполняется поиск опубликованных постов.
            search_vector = SearchVector('title', weight='A') + \
                            SearchVector('body', weight='B')   # , config='spanish'
            # SearchQuery - фильтрация результатов
            search_query = SearchQuery(query)       # , config='spanish' - для исп.языка

            # Для упорядочивания результатов по релевантности используется TrigramSimilarity
            # Результаты фильтруются, чтобы отображать только те, у которых ранг выше 0.1.
            results = Post.published.annotate(similarity=TrigramSimilarity('title', query),
                ).filter(similarity__gt=0.1).order_by('-similarity')

    context = {'form': form, 'query': query, 'results': results}
    return render(request,'home/search.html', context)
