from django.forms import ModelForm

from . import models


class PostForm(ModelForm):
    class Meta:
        model = models.Post
        fields = ["text", "group", "image"]
        help_texts = {"image": "Будет кадрировано в пропорции 960x339."}


class CommentForm(ModelForm):
    class Meta:
        model = models.Comment
        fields = ["text"]
