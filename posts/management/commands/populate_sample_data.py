import os
import lorem
import random
import names

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from posts.models import Post, Comment, Group, Follow


User = get_user_model()


class Command(BaseCommand):
    def handle(self, *args, **options):
        users = []
        for n_users in range(50):
            first_name, last_name = names.get_first_name(), names.get_last_name()
            username = first_name + "_" + last_name
            users.append(
                User.objects.create_user(
                    first_name=first_name, last_name=last_name, username=username
                )
            )
        groups = [
            Group.objects.get_or_create(
                title="Cats", slug="cats", description="We like cats."
            )[0],
            Group.objects.get_or_create(
                title="Dogs", slug="dogs", description="We like dogs."
            )[0],
            Group.objects.get_or_create(
                title="Birds", slug="birds", description="We like birds."
            )[0],
        ]
        for times in range(50):
            post = Post.objects.create(
                text=lorem.get_paragraph(count=random.randint(1, 3)).replace(
                    os.linesep, os.linesep + os.linesep
                ),
                author=random.choice(users),
                group=random.choice(groups),
            )
        for post in Post.objects.all():
            for num_comments in range(random.randint(0, 10)):
                Comment.objects.create(
                    post=post,
                    author=random.choice(users),
                    text=lorem.get_sentence(count=random.randint(1, 5)),
                )
