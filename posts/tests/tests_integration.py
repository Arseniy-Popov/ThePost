import pytest

from posts.models import User


@pytest.fixture
def user_1(client):
    user = User.objects.create_user(username="user_1")
    client.force_login(user)
    return client


@pytest.mark.django_db(transaction=True)
def test_new_post(user_1, post_text="user 1 new post text"):
    user_1.post("/new", {"text": post_text})
    assert post_text in user_1.get("").content