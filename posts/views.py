from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User


# Utilities ----------------------------------------------------------------------------


def _login_as_testuser(request):
    """
    Logs the user in as @testuser for demo purposes.
    """
    if not request.user.is_authenticated:
        user, _ = User.objects.get_or_create(username="testuser")
        login(request, user)


class SupplementContextMixin:
    """
    Mixin for CBVs to supplement context data with the
    output of ._supplement_context_data.
    """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self._supplement_context_data())
        return context


class FilterPosts(SupplementContextMixin):
    """
    Mixin for list views to filters posts based on the conditions in
    ._filter_posts and to add the conditions to context data.
    """

    paginate_by = 20

    def _filter_posts(self):
        return {}

    def get_queryset(self):
        return Post.objects.filter(**self._filter_posts()).order_by("-date")

    def _supplement_context_data(self):
        return self._filter_posts()


class IsOwnerMixin:
    """
    Mixin for modification views to redirect the user to the success url
    if the user is not the owner of the object to be modified. Requires
    .get_object and .get_success_url.
    """

    def _redirect_not_owner(self):
        self.object = self.get_object()
        if self.object.author != self.request.user:
            return redirect(self.get_success_url())

    def dispatch(self, request, *args, **kwargs):
        redirect = self._redirect_not_owner()
        if redirect:
            return redirect
        return super().dispatch(request, *args, **kwargs)


# Static views -------------------------------------------------------------------------


class IndexPosts(FilterPosts, ListView):
    template_name = "index.html"

    def render_to_response(self, *args, **kwargs):
        _login_as_testuser(self.request)
        return super().render_to_response(*args, **kwargs)


class GroupPosts(FilterPosts, ListView):
    template_name = "group.html"

    def _filter_posts(self):
        return {"group": get_object_or_404(Group, slug=self.kwargs["slug"])}


class ProfilePosts(FilterPosts, ListView):
    template_name = "profile_posts.html"

    def _filter_posts(self):
        return {"author": get_object_or_404(User, username=self.kwargs["username"])}


class SubscriptionsPosts(LoginRequiredMixin, FilterPosts, ListView):
    template_name = "subscriptions_posts.html"

    def _filter_posts(self):
        return {
            "author__in": User.objects.filter(
                followers__follower__username=self.request.user
            )
        }


class SinglePost(LoginRequiredMixin, FilterPosts, ListView):
    template_name = "profile_posts.html"

    def _filter_posts(self):
        self.post = get_object_or_404(Post, id=self.kwargs["post_id"])
        return {"id": self.kwargs["post_id"]}

    def _supplement_context_data(self):
        return {
            "author": get_object_or_404(User, username=self.kwargs["username"]),
            "comment_form": CommentForm(),
            "comments": Comment.objects.filter(post=self.post).order_by("date"),
        }


class Followers(SupplementContextMixin, ListView):
    paginate_by = 20
    template_name = "profile_follows.html"

    def get_queryset(self):
        return User.objects.filter(
            followees__followee__username=self.kwargs["username"]
        ).order_by("username")

    def _supplement_context_data(self):
        return {"author": get_object_or_404(User, username=self.kwargs["username"])}


class Followees(SupplementContextMixin, ListView):
    paginate_by = 20
    template_name = "profile_follows.html"

    def get_queryset(self):
        return User.objects.filter(
            followers__follower__username=self.kwargs["username"]
        ).order_by("username")

    def _supplement_context_data(self):
        return {"author": get_object_or_404(User, username=self.kwargs["username"])}


# Action views -------------------------------------------------------------------------


class NewPost(LoginRequiredMixin, CreateView):
    form_class = PostForm
    template_name = "new_post.html"
    success_url = reverse_lazy("index_posts")

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class NewComment(LoginRequiredMixin, CreateView):
    form_class = CommentForm

    def form_valid(self, form):
        self.post = get_object_or_404(Post, id=self.kwargs["post_id"])
        form.instance.post, form.instance.author = self.post, self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("single_post", kwargs=self.kwargs)


class EditPost(LoginRequiredMixin, IsOwnerMixin, UpdateView):
    model = Post
    form_class = PostForm
    pk_url_kwarg = "post_id"
    template_name = "edit_post.html"

    def get_success_url(self):
        return reverse("single_post", kwargs=self.kwargs)


class EditComment(LoginRequiredMixin, IsOwnerMixin, UpdateView):
    model = Comment
    form_class = CommentForm
    pk_url_kwarg = "comment_id"
    template_name = "edit_comment.html"

    def get_success_url(self):
        return reverse(
            "single_post", args=(self.object.post.author.username, self.object.post.id)
        )


@login_required
def follow(request, username):
    author = get_object_or_404(User, username=username)
    if (
        author == request.user
        or Follow.objects.filter(followee=author, follower=request.user).exists()
    ):
        return redirect("profile_posts", author)
    Follow.objects.create(followee=author, follower=request.user)
    return redirect("profile_posts", username)


@login_required
def unfollow(request, username):
    author = get_object_or_404(User, username=username)
    if Follow.objects.filter(followee=author, follower=request.user).exists():
        Follow.objects.get(followee=author, follower=request.user).delete()
    return redirect("profile_posts", username)


def _404(request, exception):
    return render(request, "misc/404.html", {"path": request.path}, status=404)


def _500(request):
    return render(request, "misc/500.html", status=500)
