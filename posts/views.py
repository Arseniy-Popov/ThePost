from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page
from django.views.generic import CreateView, ListView, UpdateView
from django.views.generic.edit import FormView
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User


# Utilities ----------------------------------------------------------------------------


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


class FilterPosts:
    paginate_by = 20

    def filter_posts(self):
        return {}

    def get_queryset(self):
        return Post.objects.filter(**self.filter_posts()).order_by("-date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.filter_posts())
        return context


class IsOwnerMixin:
    def _redirect_not_owner(self):
        self.object = self.get_object()
        if self.object.author != self.request.user:
            return redirect(self.get_success_url())

    def get(self, request, *args, **kwargs):
        redirect = self._redirect_not_owner()
        if redirect:
            return redirect
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        redirect = self._redirect_not_owner()
        if redirect:
            return redirect
        return super().post(request, *args, **kwargs)


# Static -------------------------------------------------------------------------------


class IndexPostsView(FilterPosts, ListView):
    template_name = "index.html"

    def render_to_response(self, *args, **kwargs):
        _login_as_testuser(self.request)
        return super().render_to_response(*args, **kwargs)


class GroupPostsView(FilterPosts, ListView):
    template_name = "group.html"

    def filter_posts(self):
        return {"group": get_object_or_404(Group, slug=self.kwargs["slug"])}


class ProfilePostsView(FilterPosts, ListView):
    template_name = "profile_posts.html"

    def filter_posts(self):
        return {"author": get_object_or_404(User, username=self.kwargs["username"])}


class SubscriptionsPostsView(LoginRequiredMixin, FilterPosts, ListView):
    template_name = "subscriptions_posts.html"

    def filter_posts(self):
        authors_followed = (
            i.followee for i in Follow.objects.filter(follower=self.request.user)
        )
        return {"author__in": authors_followed}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"follow_index": True})
        return context


class SinglePostView(LoginRequiredMixin, FilterPosts, ListView):
    template_name = "profile_posts.html"

    def filter_posts(self):
        self.post = get_object_or_404(Post, id=self.kwargs["post_id"])
        return {"id": self.kwargs["post_id"]}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "author": get_object_or_404(User, username=self.kwargs["username"]),
                "comment_form": CommentForm(),
                "comments": Comment.objects.filter(post=self.post).order_by("date"),
            }
        )
        return context


class FollowersView(ListView):
    paginate_by = 20
    template_name = "profile_follows.html"

    def get_queryset(self):
        return User.objects.filter(
            followees__followee__username=self.kwargs["username"]
        ).order_by("username")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {"author": get_object_or_404(User, username=self.kwargs["username"])}
        )
        return context


class FollowingView(ListView):
    paginate_by = 20
    template_name = "profile_follows.html"

    def get_queryset(self):
        return User.objects.filter(
            followers__follower__username=self.kwargs["username"]
        ).order_by("username")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {"author": get_object_or_404(User, username=self.kwargs["username"])}
        )
        return context


# Actions ------------------------------------------------------------------------------


class NewPostView(LoginRequiredMixin, FormView):
    form_class = PostForm
    template_name = "new_post.html"
    success_url = reverse_lazy("index")

    def form_valid(self, form):
        Post(author=self.request.user, **form.cleaned_data).save()
        return super().form_valid(form)


class EditPostView(LoginRequiredMixin, IsOwnerMixin, UpdateView):
    model = Post
    form_class = PostForm
    pk_url_kwarg = "post_id"
    template_name = "edit_post.html"

    def get_success_url(self):
        return reverse("view_post", args=(self.object.author.username, self.object.id))


class NewCommentView(LoginRequiredMixin, FormView):
    form_class = CommentForm

    def form_valid(self, form):
        post = get_object_or_404(Post, id=self.kwargs["post_id"])
        Comment(author=self.request.user, post=post, **form.cleaned_data).save()
        return redirect("view_post", post.author.username, self.kwargs["post_id"])


class EditCommentView(LoginRequiredMixin, UpdateView):
    model = Comment
    form_class = CommentForm
    pk_url_kwarg = "comment_id"
    template_name = "edit_post.html"

    def form_valid(self, form):
        form.save()
        return redirect(
            "view_post", self.object.post.author.username, self.object.post.id
        )


def _404(request, exception):
    return render(request, "misc/404.html", {"path": request.path}, status=404)


def _500(request):
    return render(request, "misc/500.html", status=500)


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
