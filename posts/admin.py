from django.contrib import admin

from .models import Comment, Follow, Group, Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("text", "date", "author")
    search_fields = ("text",)
    list_filter = ("date", "group", "author")
    empty_value_display = "-пусто-"


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("title", "slug")
    search_fields = ("title",)


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ("followee", "follower")
    search_fields = ("followee", "follower")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("author", "date", "post", "text")
    search_fields = ("author",)
