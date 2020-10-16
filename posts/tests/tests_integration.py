from collections import namedtuple

import pytest

from posts.models import Comment, Group, User, Post, Follow


pytestmark = pytest.mark.django_db


# Fixtures and utilities ---------------------------------------------------------------


USERNAME_1, USERNAME_2 = "user_1", "user_2"


@pytest.fixture
def user_1():
    user = User.objects.create_user(username=USERNAME_1)
    return user


@pytest.fixture
def user_2():
    user = User.objects.create_user(username=USERNAME_2)
    return user


USER_1_INIT_POST_TEXT = "user 1 init post text"
USER_2_INIT_POST_TEXT = "user 2 init post text"
USER_2_GROUP_POST_TEXT = "user 2 init group post text"
USER_1_COMMENT_TEXT = "user 1 comment text"
USER_2_COMMENT_TEXT = "user 2 comment text"
GROUP_SLUG, GROUP_DESC = "cats", "we like cats"


@pytest.fixture
def prepopulated_data(user_1, user_2):
    group = Group.objects.create(title="cats", slug=GROUP_SLUG, description=GROUP_DESC)
    post_1 = Post.objects.create(author=user_1, text=USER_1_INIT_POST_TEXT)
    post_2 = Post.objects.create(author=user_2, text=USER_2_INIT_POST_TEXT)
    post_3 = Post.objects.create(
        author=user_2, group=group, text=USER_2_GROUP_POST_TEXT
    )
    comment_1 = Comment.objects.create(
        author=user_1, text=USER_1_COMMENT_TEXT, post=post_1
    )
    comment_2 = Comment.objects.create(
        author=user_2, text=USER_2_COMMENT_TEXT, post=post_1
    )
    Follow.objects.create(follower=user_1, followee=user_2)
    return post_1, post_2, post_3


def user_client(client, user):
    client.force_login(user)
    return client


def assert_contains(contains, url, client, *users, _not_contains=False):
    """
    Assert `contains` is contained in the response from a
    get request to `url` by the `user`.
    """
    client.logout()
    for user in users:
        if user:
            client.force_login(user)
        if _not_contains:
            assert contains not in str(client.get(url).content)
        else:
            assert contains in str(client.get(url).content)
        client.logout()


def assert_not_contains(contains, url, client, *users):
    """
    Assert `contains` is not contained in the response from a
    get request to `url` by the `user`.
    """
    assert_contains(contains, url, client, *users, _not_contains=True)


# Tests --------------------------------------------------------------------------------


def test_index(client, user_1, user_2, prepopulated_data):
    assert_contains(USER_1_INIT_POST_TEXT, "", client, user_1, user_2, None)
    assert_contains(USER_2_INIT_POST_TEXT, "", client, user_1, user_2, None)


def test_group(client, user_1, user_2, prepopulated_data):
    assert_not_contains(
        USER_1_INIT_POST_TEXT, f"group/{GROUP_SLUG}", client, user_1, user_2, None
    )
    assert_contains(
        USER_2_GROUP_POST_TEXT, f"/group/{GROUP_SLUG}", client, user_1, user_2, None
    )


def test_new_post(
    client, user_1, user_2, prepopulated_data, post_text="user 2 new post text"
):
    user_client(client, user_2).post("/new", {"text": post_text})
    assert_contains(post_text, "", client, user_1, user_2, None)
    assert_contains(post_text, f"/{USERNAME_2}", client, user_1, user_2, None)
    assert_contains(post_text, "/follow", client, user_1)


def test_follow_index(client, user_1, user_2, prepopulated_data):
    assert_contains(USER_2_INIT_POST_TEXT, "/follow", client, user_1)
    assert_not_contains(USER_1_INIT_POST_TEXT, "/follow", client, user_2)


def test_profile(client, user_1, user_2, prepopulated_data):
    assert_contains(
        USER_1_INIT_POST_TEXT, f"/{USERNAME_1}", client, user_1, user_2, None
    )
    assert_not_contains(
        USER_2_INIT_POST_TEXT, f"/{USERNAME_1}", client, user_1, user_2, None
    )


def test_follow(client, user_1, user_2, prepopulated_data):
    user_client(client, user_2).get(f"/{USERNAME_1}/follow")
    assert Follow.objects.filter(follower=user_2, followee=user_1).exists() is True
    assert_contains(USER_1_INIT_POST_TEXT, "/follow", client, user_2)
    assert_contains(f"@{USERNAME_2}", f"/{USERNAME_1}/followers", client, user_1)
    assert_contains(f"@{USERNAME_1}", f"/{USERNAME_2}/following", client, user_2)


def test_unfollow(client, user_1, user_2, prepopulated_data):
    user_client(client, user_1).get(f"/{USERNAME_2}/unfollow")
    assert Follow.objects.filter(follower=user_1, followee=user_2).exists() is False
    assert_not_contains(USER_2_INIT_POST_TEXT, "/follow", client, user_1)
    assert_not_contains(f"@{USERNAME_1}", f"/{USERNAME_2}/followers", client, user_2)
    assert_not_contains(f"@{USERNAME_2}", f"/{USERNAME_1}/following", client, user_1)


def test_followers(client, user_1, user_2, prepopulated_data):
    assert_contains(f"@{USERNAME_1}", f"/{USERNAME_2}/followers", client, user_2)


def test_following(client, user_1, user_2, prepopulated_data):
    assert_contains(f"@{USERNAME_2}", f"/{USERNAME_1}/following", client, user_1)


def test_view_post(client, user_1, user_2, prepopulated_data):
    post_1, post_2, post_3 = prepopulated_data
    assert_contains(
        USER_1_INIT_POST_TEXT, f"/{USERNAME_1}/{post_1.id}", client, user_1, user_2
    )
    assert_contains(
        USER_1_COMMENT_TEXT, f"/{USERNAME_1}/{post_1.id}", client, user_1, user_2
    )
    assert_contains(
        USER_2_COMMENT_TEXT, f"/{USERNAME_1}/{post_1.id}", client, user_1, user_2
    )
    assert_contains(
        USER_2_INIT_POST_TEXT, f"/{USERNAME_2}/{post_2.id}", client, user_1, user_2
    )


def test_new_comment(client, user_1, user_2, prepopulated_data):
    post_1, post_2, post_3 = prepopulated_data
    user_1_new_comment_text, user_2_new_comment_text = (
        "user 1 new comment text",
        "user 2 new comment text",
    )
    response = user_client(client, user_1).post(
        f"/{USERNAME_2}/{post_2.id}/comment", {"text": user_1_new_comment_text}
    )
    user_client(client, user_2).post(
        f"/{USERNAME_2}/{post_2.id}/comment", {"text": user_2_new_comment_text}
    )
    assert (
        Comment.objects.filter(author=user_1, text=user_1_new_comment_text).exists()
        is True
    )
    assert_contains(
        user_1_new_comment_text, f"/{USERNAME_2}/{post_2.id}", client, user_1, user_2
    )
    assert_contains(
        user_2_new_comment_text, f"/{USERNAME_2}/{post_2.id}", client, user_1, user_2
    )
