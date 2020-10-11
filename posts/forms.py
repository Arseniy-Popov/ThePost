from django.forms import ModelForm

from . import models


class PostForm(ModelForm):
    class Meta:
        model = models.Post
        fields = ["text", "group"]


class CommentForm(ModelForm):
    class Meta:
        model = models.Comment
        fields = ["text"]
