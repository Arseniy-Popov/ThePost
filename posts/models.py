from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Post(models.Model):
    text = models.TextField()
    date = models.DateTimeField("date published", auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    group = models.ForeignKey(
        "Group", on_delete=models.SET_NULL, null=True, blank=True, related_name="posts"
    )
    image = models.ImageField(upload_to="posts/", blank=True, null=True)

    def __str__(self):
        return f"Post by {self.author}, {self.date}"


class Comment(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    text = models.TextField()
    date = models.DateTimeField("date published", auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author} on {self.post}, {self.date}"


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title


class Follow(models.Model):
    followee = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="followers"
    )
    follower = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="followees"
    )

    def __str__(self):
        return f"Follow: {self.follower} following {self.followee}"
