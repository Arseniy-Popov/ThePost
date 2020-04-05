from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from . import forms
from .models import Comment, Follow, Group, Post, User


def _filter_posts(request, template, add_context={}, **filters):
    posts = Post.objects.filter(**filters).order_by("-pub_date").all()
    paginator, page = _paginate(request, posts)
    return render(
        request,
        template,
        {**filters, **add_context, "page": page, "paginator": paginator},
    )


def _paginate(request, items, items_per_page=10):
    paginator = Paginator(items, items_per_page)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return paginator, page


def index(request):
    return _filter_posts(request, "index.html")


def group(request, slug):
    filters = {"group": get_object_or_404(Group, slug=slug)}
    return _filter_posts(request, "group.html", **filters)


def profile(request, username):
    filters = {"author": get_object_or_404(User, username=username)}
    return _filter_posts(request, "profile.html", **filters)


@login_required
def view_post(request, username, post_id):
    post = get_object_or_404(Post, id=post_id)
    filters = {"id": post.id}
    add_context = {
        "author": get_object_or_404(User, username=username),
        "comment_form": forms.CommentForm(),
        "comments": Comment.objects.filter(post=post),
    }
    return _filter_posts(request, "profile.html", add_context=add_context, **filters)


@login_required
def new_post(request):
    if request.method == "POST":
        form = forms.PostForm(request.POST, request.FILES or None)
        if form.is_valid():
            Post(author=request.user, **form.cleaned_data).save()
            return redirect("index")
    form = forms.PostForm()
    return render(request, "new_post.html", {"form": form})


@login_required
def edit_post(request, username, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect("view_post", username, post_id)
    if request.method == "POST":
        form = forms.PostForm(request.POST, request.FILES or None, instance=post)
        if form.is_valid():
            form.save()
            return redirect("view_post", username, post_id)
    form = forms.PostForm(instance=post)
    return render(request, "edit_post.html", {"form": form})


@login_required
def new_comment(request, username, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = forms.CommentForm(request.POST)
    if form.is_valid():
        Comment.objects.create(author=request.user, post=post, **form.cleaned_data)
    return redirect("view_post", post.author.username, post_id)


def _404(request, exception):
    return render(request, "misc/404.html", {"path": request.path}, status=404)


def _500(request):
    return render(request, "misc/500.html", status=500)


@login_required
def follow_index(request):
    authors_followed = [i.author for i in Follow.objects.filter(user=request.user)]
    authors_followed.append(User.objects.get(username="admin"))
    filters = {"author__in": authors_followed}
    add_context = {"follow_index": True}
    return _filter_posts(request, "follow.html", add_context=add_context, **filters)


@login_required
def follow(request, username):
    author = get_object_or_404(User, username=username)
    if (
        author == request.user
        or Follow.objects.filter(author=author, user=request.user).exists()
    ):
        return redirect("profile", author)
    Follow.objects.create(author=author, user=request.user)
    return redirect("profile", username)


@login_required
def unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.get(author=author, user=request.user).delete()
    return redirect("profile", username)
