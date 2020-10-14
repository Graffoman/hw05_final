from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse, Http404
from django.views.decorators.cache import cache_page
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


@cache_page(20, key_prefix='index_page')
def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request, 'index.html',
        {'page': page, 'paginator': paginator}
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request, 'group.html',
        {'group': group, 'posts': posts,
            'page': page, 'paginator': paginator}
    )


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            new_post = form.save(commit=False)
            new_post.author = request.user
            new_post.save()
            return redirect('index')
    return render(request, 'new_post.html', {'form': form})


def profile(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    following = False
    if user.is_authenticated:
        try:
            get_object_or_404(Follow, user=user, author=author)
            following = True
        except Http404:
            following = False

    post_list = Post.objects.filter(author=author)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request, 'profile.html', {
            'page': page, 'paginator': paginator,
            'author': author, 'following': following
        }
    )


def post_view(request, username, post_id):
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.all()
    form = CommentForm()
    return render(
        request, 'post.html',
        {'author': author, 'post': post, 'comments': comments, 'form': form}
        )


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('post', username=username, post_id=post_id)
    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=post
    )
    if request.method == 'POST':
        if form.is_valid():
            edited_post = form.save(commit=False)
            edited_post.save()
            return redirect('post', username=username, post_id=post_id)
    return render(request, 'new_post.html', {'form': form, 'post': post})


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
            return redirect('post', username=username, post_id=post_id)
    return render(request, 'comments.html', {'form': form, 'post': post})


def page_not_found(request, exception):
    return render(
        request,
        'misc/404.html',
        {'path': request.path},
        status=404
    )


def server_error(request):
    return render(request, 'misc/500.html', status=500)


@login_required
def follow_index(request):
    user = request.user
    authors = [follow.author for follow in user.follower.all()]
    post_list = Post.objects.filter(author__in=authors)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request, 'follow.html',
        {'page': page, 'paginator': paginator}
    )


@login_required
def profile_follow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    try:
        get_object_or_404(Follow, user=user, author=author)
        follow = True
    except Http404:
        follow = False
    if user != author and follow is False:
        Follow.objects.create(user=request.user, author=author)
        return redirect('follow_index')
    return redirect('follow_index')


@login_required
def profile_unfollow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    try:
        follow = Follow.objects.get(user=user, author=author)
    except follow.DoesNotExist:
        return redirect('follow_index')
    follow.delete()
    return redirect('follow_index')
