from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from django.conf import settings

from .forms import PostForm, CommentForm
from .models import Post, Group, Follow

User = get_user_model()


def create_paginator(request, post_list):
    paginator = Paginator(post_list, settings.NUMBER_OF_POSTS_DISPLAYED)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


def index(request):
    template = 'posts/index.html'
    post_list = Post.objects.select_related('author', 'group')
    page_obj = create_paginator(request, post_list)
    context = {'page_obj': page_obj, 'index': True}
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('author')
    page_obj = create_paginator(request, post_list)
    context = {'group': group,
               'page_obj': page_obj}
    return render(request, template, context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.select_related('group')
    count = post_list.count()
    page_obj = create_paginator(request, post_list)

    following = Follow.objects.filter(
        user=request.user,
        author=author
    ).exists() and request.user.is_authenticated
    context = {'author': author,
               'page_obj': page_obj,
               'count': count,
               'following': following}
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    count = post.author.posts.count()
    comments_list = post.comments.select_related('author')
    context = {'post': post,
               'count': count,
               'comments': comments_list,
               'form': CommentForm(None)}
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None,
                    files=request.FILES or None)
    if form.is_valid():
        new_post = form.save(commit=False)
        new_post.author = request.user
        new_post.save()
        return redirect('posts:profile', username=request.user.username)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid() and request.method == 'POST':
        post.save()
        return redirect('posts:post_detail', post_id=post_id)
    return render(request,
                  'posts/create_post.html',
                  {'form': form, 'is_edit': True, 'post_id': post_id})


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    template = 'posts/follow.html'
    post_list = Post.objects.filter(
        author__following__user=request.user
    ).select_related('author', 'group')
    page_obj = create_paginator(request, post_list)
    context = {'page_obj': page_obj, 'follow': True}
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(
            user=request.user,
            author=author
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', username=username)
