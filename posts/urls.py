from django.urls import path

from . import views


urlpatterns = [
    path("", views.IndexPosts.as_view(), name="index_posts"),
    path("post", views.NewPost.as_view(), name="new_post"),
    path("group/<slug>/posts", views.GroupPosts.as_view(), name="group_posts"),
    path("feed", views.SubscriptionsPosts.as_view(), name="subscriptions_posts"),
    path("<username>/posts", views.ProfilePosts.as_view(), name="profile_posts"),
    path("<username>/follow", views.follow, name="follow"),
    path("<username>/unfollow", views.unfollow, name="unfollow"),
    path("<username>/followers", views.Followers.as_view(), name="followers"),
    path("<username>/followees", views.Followees.as_view(), name="followees"),
    path(
        "<username>/posts/<int:post_id>", views.SinglePost.as_view(), name="single_post"
    ),
    path(
        "<username>/posts/<int:post_id>/comment",
        views.NewComment.as_view(),
        name="new_comment",
    ),
    path(
        "<username>/posts/<int:post_id>/edit",
        views.EditPost.as_view(),
        name="edit_post",
    ),
    path(
        "<username>/comments/<int:comment_id>",
        views.EditComment.as_view(),
        name="edit_comment",
    ),
]
