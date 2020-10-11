import os
import lorem
import random
import names
import datetime as dt

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from posts.models import Post, Comment, Group, Follow


User = get_user_model()


class Command(BaseCommand):
    def handle(self, *args, **options):
        # users
        users = []
        for _ in range(50):
            first_name, last_name = names.get_first_name(), names.get_last_name()
            username = first_name.lower() + "_" + last_name.lower()
            users.append(
                User.objects.create_user(
                    first_name=first_name, last_name=last_name, username=username
                )
            )
        # test user
        try:
            user = User.objects.get(username="testuser")
            user.first_name = "John"
            user.last_name = "Doe"
            user.save()
        except User.DoesNotExist:
            User.objects.create(username="testuser", first_name="John", last_name="Doe")
        users.append(User.objects.get(username="testuser"))
        # follows
        for follower in users:
            for followee in random.sample(users, random.randint(0, 50)):
                Follow.objects.create(follower=follower, followee=followee)
        # groups
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
            None,
        ]
        # posts
        start_date, end_date = (
            dt.datetime(year=2020, month=10, day=2).timestamp(),
            dt.datetime(year=2020, month=10, day=10).timestamp(),
        )
        for user in users:
            for post in range(random.randint(0, 7)):
                post = Post.objects.create(
                    text=lorem.get_paragraph(count=random.randint(1, 3)).replace(
                        os.linesep, os.linesep + os.linesep
                    ),
                    author=user,
                    group=random.choice(groups),
                )
                post.date = dt.datetime.fromtimestamp(
                    random.uniform(start_date, end_date),
                    tz=dt.timezone(dt.timedelta(hours=0)),
                )
                post.save()
        # comments
        for post in Post.objects.all():
            start_date, end_date = (
                post.date.timestamp(), 
                dt.datetime(year=2020, month=10, day=10).timestamp(),
            )
            for _ in range(random.randint(0, 10)):
                comment = Comment.objects.create(
                    post=post,
                    author=random.choice(users),
                    text=lorem.get_sentence(count=random.randint(1, 5)),
                )
                comment.date = dt.datetime.fromtimestamp(
                    random.uniform(start_date, end_date),
                    tz=dt.timezone(dt.timedelta(hours=0)),
                )
                comment.save()
