from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("new", views.new_post, name="new_post"),
    path("group/<slug>", views.group, name="group"),
    path("follow", views.follow_index, name="follow_index"),
    path("<username>", views.profile, name="profile"),
    path("<username>/follow", views.follow, name="follow"),
    path("<username>/unfollow", views.unfollow, name="unfollow"),
    path("<username>/followers", views.followers, name="followers"),
    path("<username>/following", views.following, name="following"),
    path(
        "<username>/comments/<int:comment_id>", views.edit_comment, name="edit_comment"
    ),
    path("<username>/<int:post_id>", views.view_post, name="view_post"),
    path("<username>/<int:post_id>/comment/", views.new_comment, name="new_comment"),
    path("<username>/<int:post_id>/edit/", views.edit_post, name="edit_post"),
]
