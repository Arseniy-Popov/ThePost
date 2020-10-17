from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User


def _filter_posts(request, template, add_context={}, **filters):
    posts = Post.objects.filter(**filters).order_by("-date")
    paginator, page = _paginate(request, posts)
    return render(
        request,
        template,
        {**filters, **add_context, "page": page, "paginator": paginator},
    )


def _paginate(request, items, items_per_page=20):
    paginator = Paginator(items, items_per_page)
    page = paginator.get_page(request.GET.get("page"))
    return paginator, page  # TODO: return dict and rename


def _login_as_testuser(request):
    if not request.user.is_authenticated:
        user, _ = User.objects.get_or_create(username="testuser")
        login(request, user)


def _edit_object(request, object, form, redirect, template):
    if object.author != request.user:
        return redirect
    if request.method == "POST":
        form = form(request.POST, request.FILES or None, instance=object)
        if form.is_valid():
            form.save()
            return redirect
    form = form(instance=object)
    return render(request, template, {"form": form})


def index(request):
    _login_as_testuser(request)
    return _filter_posts(request, "index.html")


def group(request, slug):
    filters = {"group": get_object_or_404(Group, slug=slug)}
    return _filter_posts(request, "group.html", **filters)


def profile(request, username):
    filters = {"author": get_object_or_404(User, username=username)}
    return _filter_posts(request, "profile_posts.html", **filters)


@login_required
def view_post(request, username, post_id):
    post = get_object_or_404(Post, id=post_id)
    filters = {"id": post.id}
    add_context = {
        "author": get_object_or_404(User, username=username),
        "comment_form": CommentForm(),
        "comments": Comment.objects.filter(post=post).order_by("date"),
    }
    return _filter_posts(
        request, "profile_posts.html", add_context=add_context, **filters
    )


@login_required
def new_post(request):
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES or None)
        if form.is_valid():
            Post(author=request.user, **form.cleaned_data).save()
            return redirect("index")
    form = PostForm()
    return render(request, "new_post.html", {"form": form})


@login_required
def edit_post(request, username, post_id):
    post = get_object_or_404(Post, id=post_id)
    return _edit_object(
        request=request,
        object=post,
        form=PostForm,
        redirect=redirect("view_post", post.author.username, post.id),
        template="edit_post.html",
    )


@login_required
def new_comment(request, username, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        Comment.objects.create(author=request.user, post=post, **form.cleaned_data)
    return redirect("view_post", post.author.username, post_id)


@login_required
def edit_comment(request, username, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    return _edit_object(
        request=request,
        object=comment,
        form=CommentForm,
        redirect=redirect("view_post", comment.post.author.username, comment.post.id),
        template="edit_post.html",
    )


def _404(request, exception):
    return render(request, "misc/404.html", {"path": request.path}, status=404)


def _500(request):
    return render(request, "misc/500.html", status=500)


@login_required
def follow_index(request):
    authors_followed = (
        i.followee for i in Follow.objects.filter(follower=request.user)
    )
    filters = {"author__in": authors_followed}
    add_context = {"follow_index": True}
    return _filter_posts(request, "follow.html", add_context=add_context, **filters)


@login_required
def follow(request, username):
    author = get_object_or_404(User, username=username)
    if (
        author == request.user
        or Follow.objects.filter(followee=author, follower=request.user).exists()
    ):
        return redirect("profile", author)
    Follow.objects.create(followee=author, follower=request.user)
    return redirect("profile", username)


@login_required
def unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.get(followee=author, follower=request.user).delete()
    return redirect("profile", username)


@login_required
def followers(request, username):
    followers = User.objects.filter(followees__followee__username=username).order_by(
        "username"
    )
    paginator, page = _paginate(request, followers, items_per_page=15)
    add_context = {
        "author": get_object_or_404(User, username=username),
        "page": page,
        "paginator": paginator,
    }
    return render(request, "profile_follows.html", add_context)


@login_required
def following(request, username):
    followers = User.objects.filter(followers__follower__username=username).order_by(
        "username"
    )
    paginator, page = _paginate(request, followers, items_per_page=15)
    add_context = {
        "author": get_object_or_404(User, username=username),
        "page": page,
        "paginator": paginator,
    }
    return render(request, "profile_follows.html", add_context)
