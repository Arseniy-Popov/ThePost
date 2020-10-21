from django import template

from posts.models import Comment, Follow, Post


register = template.Library()


@register.filter
def author_number_posts(author):
    return len(Post.objects.filter(author=author))


@register.filter
def user_is_author(user, post):
    return post.author == user


@register.filter
def is_followed(author, user):
    try:
        return Follow.objects.get(follower=user, followee=author)
    except:
        return False


@register.filter
def comment_count(post):
    return Comment.objects.filter(post=post).count()


@register.filter
def follower_count(user):
    return Follow.objects.filter(followee=user).count()


@register.filter
def followee_count(user):
    return Follow.objects.filter(follower=user).count()
