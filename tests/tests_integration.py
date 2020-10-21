import pytest
from django.test import Client

from posts.models import Comment, Follow, Group, Post, User


USERNAME_1, USERNAME_2 = "user_1", "user_2"
USER_1_INIT_POST_TEXT = "user 1 init post text"
USER_2_INIT_POST_TEXT = "user 2 init post text"
USER_2_GROUP_POST_TEXT = "user 2 init group post text"
USER_1_COMMENT_TEXT = "user 1 comment text"
USER_2_COMMENT_TEXT = "user 2 comment text"
GROUP_SLUG, GROUP_DESC = "cats", "we like cats"


@pytest.mark.django_db
class Tests:
    """
    Tests are grouped by url paths.
    """

    # Fixtures and utilities -----------------------------------------------------------

    @pytest.fixture(autouse=True)
    def prepopulated_data(self):
        self.user_1 = User.objects.create_user(username=USERNAME_1)
        self.user_2 = User.objects.create_user(username=USERNAME_2)
        self.group_1 = Group.objects.create(
            title="cats", slug=GROUP_SLUG, description=GROUP_DESC
        )
        self.post_1 = Post.objects.create(
            author=self.user_1, text=USER_1_INIT_POST_TEXT
        )
        self.post_2 = Post.objects.create(
            author=self.user_2, text=USER_2_INIT_POST_TEXT
        )
        self.post_3 = Post.objects.create(
            author=self.user_2, group=self.group_1, text=USER_2_GROUP_POST_TEXT
        )
        self.comment_1 = Comment.objects.create(
            author=self.user_2, text=USER_2_COMMENT_TEXT, post=self.post_1
        )
        self.comment_2 = Comment.objects.create(
            author=self.user_1, text=USER_1_COMMENT_TEXT, post=self.post_1
        )
        Follow.objects.create(follower=self.user_1, followee=self.user_2)

    def user_client(self, user):
        client = Client()
        client.force_login(user)
        return client

    def assert_contains(self, contains, url, *users, _not_contains=False):
        """
        Assert that for every user in `users`, `contains` is contained
        in the response from a get request to the `url` by the user.
        """
        for user in users:
            client = Client()
            if user:
                client.force_login(user)
            if _not_contains:
                assert contains not in str(client.get(url).content)
            else:
                assert contains in str(client.get(url).content)

    def assert_not_contains(self, contains, url, *users):
        """
        Assert that for every user in `users`, `contains` is not contained
        in the response from a get request to the `url` by the user.
        """
        self.assert_contains(contains, url, *users, _not_contains=True)

    # Test static ----------------------------------------------------------------------

    def test_index_posts(self):
        self.assert_contains(USER_1_INIT_POST_TEXT, "", self.user_1, self.user_2, None)
        self.assert_contains(USER_2_INIT_POST_TEXT, "", self.user_1, self.user_2, None)

    def test_group_posts(self):
        self.assert_not_contains(
            USER_1_INIT_POST_TEXT,
            f"group/{GROUP_SLUG}/posts",
            self.user_1,
            self.user_2,
            None,
        )
        self.assert_contains(
            USER_2_GROUP_POST_TEXT,
            f"/group/{GROUP_SLUG}/posts",
            self.user_1,
            self.user_2,
            None,
        )

    def test_subscriptions_posts(self):
        self.assert_contains(USER_2_INIT_POST_TEXT, "/feed", self.user_1)
        self.assert_not_contains(USER_1_INIT_POST_TEXT, "/feed", self.user_2)

    def test_profile_posts(self):
        self.assert_contains(
            USER_1_INIT_POST_TEXT,
            f"/{USERNAME_1}/posts",
            self.user_1,
            self.user_2,
            None,
        )
        self.assert_not_contains(
            USER_2_INIT_POST_TEXT,
            f"/{USERNAME_1}/posts",
            self.user_1,
            self.user_2,
            None,
        )

    def test_followers(self):
        self.assert_contains(f"@{USERNAME_1}", f"/{USERNAME_2}/followers", self.user_2)
        assert (
            self.user_1
            in self.user_client(self.user_2)
            .get(f"/{USERNAME_2}/followers")
            .context["page"]
        )
        assert (
            self.user_2
            not in self.user_client(self.user_2)
            .get(f"/{USERNAME_2}/followers")
            .context["page"]
        )

    def test_followees(self):
        self.assert_contains(f"@{USERNAME_2}", f"/{USERNAME_1}/followees", self.user_1)
        assert (
            self.user_2
            in self.user_client(self.user_1)
            .get(f"/{USERNAME_1}/followees")
            .context["page"]
        )
        assert (
            self.user_1
            not in self.user_client(self.user_1)
            .get(f"/{USERNAME_1}/followees")
            .context["page"]
        )

    def test_single_post(self):
        self.assert_contains(
            USER_1_INIT_POST_TEXT,
            f"/{USERNAME_1}/posts/{self.post_1.id}",
            self.user_1,
            self.user_2,
        )
        self.assert_contains(
            USER_1_COMMENT_TEXT,
            f"/{USERNAME_1}/posts/{self.post_1.id}",
            self.user_1,
            self.user_2,
        )
        self.assert_contains(
            USER_2_COMMENT_TEXT,
            f"/{USERNAME_1}/posts/{self.post_1.id}",
            self.user_1,
            self.user_2,
        )
        self.assert_contains(
            USER_2_INIT_POST_TEXT,
            f"/{USERNAME_2}/posts/{self.post_2.id}",
            self.user_1,
            self.user_2,
        )

    # Test actions ---------------------------------------------------------------------

    def test_new_post(self):
        post_text = "user 2 new post text"
        response = self.user_client(self.user_2).post(
            "/post", {"text": post_text}, follow=True
        )
        assert response.redirect_chain[-1][0] == "/"
        assert Post.objects.filter(author=self.user_2, text=post_text).exists() is True
        self.assert_contains(post_text, "", self.user_1, self.user_2, None)
        self.assert_contains(
            post_text, f"/{USERNAME_2}/posts", self.user_1, self.user_2, None
        )
        self.assert_contains(post_text, "/feed", self.user_1)

    def test_follow(self):
        response = self.user_client(self.user_2).get(
            f"/{USERNAME_1}/follow", follow=True
        )
        assert response.redirect_chain[-1][0] == f"/{USERNAME_1}/posts"
        assert (
            Follow.objects.filter(follower=self.user_2, followee=self.user_1).exists()
            is True
        )
        self.assert_contains(USER_1_INIT_POST_TEXT, "/feed", self.user_2)
        self.assert_contains(f"@{USERNAME_2}", f"/{USERNAME_1}/followers", self.user_1)
        self.assert_contains(f"@{USERNAME_1}", f"/{USERNAME_2}/followees", self.user_2)

    def test_unfollow(self):
        response = self.user_client(self.user_1).get(
            f"/{USERNAME_2}/unfollow", follow=True
        )
        assert response.redirect_chain[-1][0] == f"/{USERNAME_2}/posts"
        assert (
            Follow.objects.filter(follower=self.user_1, followee=self.user_2).exists()
            is False
        )
        self.assert_not_contains(USER_2_INIT_POST_TEXT, "/feed", self.user_1)
        self.assert_not_contains(
            f"@{USERNAME_1}", f"/{USERNAME_2}/followers", self.user_2
        )
        self.assert_not_contains(
            f"@{USERNAME_2}", f"/{USERNAME_1}/followees", self.user_1
        )

    def test_new_comment(self):
        user_1_new_comment_text, user_2_new_comment_text = (
            "user 1 new comment text",
            "user 2 new comment text",
        )
        response = self.user_client(self.user_1).post(
            f"/{USERNAME_2}/posts/{self.post_2.id}/comment",
            {"text": user_1_new_comment_text},
            follow=True,
        )
        assert response.redirect_chain[-1][0] == f"/{USERNAME_2}/posts/{self.post_2.id}"
        self.user_client(self.user_2).post(
            f"/{USERNAME_2}/posts/{self.post_2.id}/comment",
            {"text": user_2_new_comment_text},
        )
        assert (
            Comment.objects.filter(
                author=self.user_1, text=user_1_new_comment_text, post=self.post_2
            ).exists()
            is True
        )
        assert (
            Comment.objects.filter(
                author=self.user_2, text=user_2_new_comment_text, post=self.post_2
            ).exists()
            is True
        )
        self.assert_contains(
            user_1_new_comment_text,
            f"/{USERNAME_2}/posts/{self.post_2.id}",
            self.user_1,
            self.user_2,
        )
        self.assert_contains(
            user_2_new_comment_text,
            f"/{USERNAME_2}/posts/{self.post_2.id}",
            self.user_1,
            self.user_2,
        )

    def test_edit_post(self):
        user_2_new_text = "user 2 updated post text"
        response = self.user_client(self.user_2).post(
            f"/{USERNAME_2}/posts/{self.post_2.id}/edit",
            {"text": user_2_new_text},
            follow=True,
        )
        assert response.redirect_chain[-1][0] == f"/{USERNAME_2}/posts/{self.post_2.id}"
        assert Post.objects.get(id=self.post_2.id).text == user_2_new_text
        self.assert_contains(
            user_2_new_text,
            f"/{USERNAME_2}/posts/{self.post_2.id}",
            self.user_1,
            self.user_2,
        )
        self.assert_contains(user_2_new_text, "/feed", self.user_1)
        self.assert_contains(user_2_new_text, "", self.user_1, self.user_2, None)

    def test_edit_comment(self):
        new_comment_text = "user 2 updated comment text"
        response = self.user_client(self.user_2).post(
            f"/{USERNAME_2}/comments/{self.comment_1.id}",
            {"text": new_comment_text},
            follow=True,
        )
        assert response.redirect_chain[-1][0] == f"/{USERNAME_1}/posts/{self.post_1.id}"
        self.assert_contains(
            new_comment_text,
            f"/{USERNAME_1}/posts/{self.post_1.id}",
            self.user_1,
            self.user_2,
        )
