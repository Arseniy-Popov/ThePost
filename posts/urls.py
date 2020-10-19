from django.urls import path

from . import views

urlpatterns = [
    path("", views.IndexPostsView.as_view(), name="index"),
    path("new", views.NewPostView.as_view(), name="new_post"),
    path("group/<slug>", views.GroupPostsView.as_view(), name="group"),
    path("follow", views.SubscriptionsPostsView.as_view(), name="follow_index"),
    path("<username>", views.ProfilePostsView.as_view(), name="profile"),
    path("<username>/follow", views.follow, name="follow"),
    path("<username>/unfollow", views.unfollow, name="unfollow"),
    path("<username>/followers", views.followers, name="followers"),
    path("<username>/following", views.following, name="following"),
    path("<username>/<int:post_id>", views.SinglePostView.as_view(), name="view_post"),
    path("<username>/<int:post_id>/comment", views.new_comment, name="new_comment"),
    path("<username>/<int:post_id>/edit", views.edit_post, name="edit_post"),
    path(
        "<username>/comments/<int:comment_id>", views.edit_comment, name="edit_comment"
    ),
]
