import time

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from parameterized import parameterized
from posts.models import Comment, Follow, Group, Post, User


class Test(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user("test_username_1")
        self.client.force_login(self.user)
        self.post_text_1, self.post_text_2 = "test_text", "test_text_2"
        self.post_group = Group.objects.create(slug="test_group")
        self.client.post(
            reverse("new_post"), {"text": self.post_text_1, "group": self.post_group.id}
        )
        cache.clear()

    @parameterized.expand([("1", "test_username_2", "test_password_2")])
    def test_signing_up_creates_profile(self, _, username, password):
        self.client.logout()
        signup_data = {
            "username": username,
            "password1": password,
            "password2": password,
        }
        self.client.post(reverse("signup"), signup_data)
        response = self.client.get(reverse("profile", args=[username]))
        self.assertTemplateUsed(response, "profile.html")
        self.assertContains(response, username)

    def test_logged_in_create_post(self):
        self.client.post(reverse("new_post"), {"text": self.post_text_2})
        self.assertEqual(Post.objects.count(), 2)
        self.assertTrue(Post.objects.filter(text=self.post_text_1).exists())

    def test_logged_out_create_post(self):
        self.client.logout()
        response = self.client.post(reverse("new_post"), {"text": self.post_text_2})
        with self.assertRaises(Post.DoesNotExist):
            Post.objects.get(text=self.post_text_2)
        self.assertRedirects(response, reverse("login") + "?next=/new")

    def _post_contents_match(self, contents, post_id=1):
        with self.subTest("index"):
            index = self.client.get(reverse("index"))
            self.assertContains(index, contents)
        with self.subTest("profile"):
            profile = self.client.get(
                reverse("profile", kwargs={"username": self.user.username})
            )
            self.assertContains(profile, contents)
        cache.clear()
        with self.subTest("post"):
            post = self.client.get(
                reverse(
                    "view_post",
                    kwargs={"username": self.user.username, "post_id": post_id},
                )
            )
            self.assertContains(post, contents)
        with self.subTest("group"):
            post = self.client.get(
                reverse("group", kwargs={"slug": self.post_group.slug})
            )
            self.assertContains(post, contents)

    def test_new_post_contents(self):
        self._post_contents_match(self.post_text_1)

    def test_edited_post_contents(self):
        self.client.post(
            reverse("edit_post", kwargs={"post_id": 1, "username": self.user.username}),
            {"text": self.post_text_2, "group": self.post_group.id},
        )
        self._post_contents_match(self.post_text_2)

    def test_404(self):
        response = self.client.get("/sadfasdfasdfasdfasf")
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "misc/404.html")
        self.assertContains(response, "Ошибка 404", status_code=404)

    def test_image(self):
        with open("media/1.JPG", "rb") as image:
            self.client.post(
                reverse("new_post"),
                {"text": self.post_text_2, "group": self.post_group.id, "image": image},
            )
        self._post_contents_match("<img", post_id=2)

    def test_image_invalid_format(self):
        image = SimpleUploadedFile("file.txt", b"", content_type="text/plain")
        response = self.client.post(
            reverse("new_post"),
            {"text": self.post_text_2, "group": self.post_group.id, "image": image},
        )
        self.assertEqual(response.status_code, 200)
        with self.assertRaises(Post.DoesNotExist):
            Post.objects.get(author=self.user, text=self.post_text_2)

    def test_cache(self):
        self.client.get(reverse("index"))
        # delete the post from the db
        Post.objects.get(text=self.post_text_1).delete()
        time.sleep(1)
        # the deleted post should still be cached
        index = self.client.get(reverse("index"))
        self.assertContains(index, self.post_text_1)
        time.sleep(2)
        # and now it should be gone
        index = self.client.get(reverse("index"))
        self.assertNotContains(index, self.post_text_1)


class TestFollowing(TestCase):
    def setUp(self):
        self.client_subscriber, self.client_non_subscriber = Client(), Client()
        self.author, self.post_by_author = (
            User.objects.create_user("author"),
            "post_by_author",
        )
        Post.objects.create(author=self.author, text=self.post_by_author)
        # the non subscriber will not be following the author
        self.user_non_subscriber = User.objects.create_user("user_non_subscriber")
        self.client_non_subscriber.force_login(self.user_non_subscriber)
        # the subscriber will be following the author
        self.user_subscriber = User.objects.create_user("user_subscriber")
        self.client_subscriber.force_login(self.user_subscriber)
        cache.clear()

    def test_subscribing_not_logged_in(self):
        response = self.client.post(
            reverse("follow", kwargs={"username": self.author.username})
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("login") + "?next=%2Fauthor%2Ffollow")

    def test_subscriber(self):
        # the subscriber should see the post in subscriptions
        self.client_subscriber.post(
            reverse("follow", kwargs={"username": self.author.username})
        )
        response = self.client_subscriber.get(reverse("follow_index"))
        self.assertContains(response, self.post_by_author)

    def test_non_subscriber(self):
        # the subscriber should not see the post in subscriptions
        response = self.client_subscriber.get(reverse("follow_index"))
        self.assertNotContains(response, self.post_by_author)


class TestComments(TestCase):
    def setUp(self):
        self.client = Client()
        self.author = User.objects.create_user("test_author")
        self.commenter = User.objects.create_user("test_commenter")
        self.post = Post.objects.create(author=self.author, text="test_post")
        self.comment = "test_comment"

    def test_commenting_not_logged_in(self):
        self.client.post(
            reverse(
                "new_comment",
                kwargs={"username": self.author.username, "post_id": self.post.id},
            ),
            {"text": self.comment},
        )
        with self.assertRaises(Comment.DoesNotExist):
            Comment.objects.get(text=self.comment)

    def test_commenting_logged_in(self):
        self.client.force_login(self.commenter)
        self.client.post(
            reverse(
                "new_comment",
                kwargs={"username": self.author.username, "post_id": self.post.id},
            ),
            {"text": self.comment},
        )
        response = self.client.get(
            reverse(
                "view_post", kwargs={"username": self.author, "post_id": self.post.id}
            )
        )
        self.assertTrue(Comment.objects.filter(text=self.comment).exists())
        self.assertContains(response, self.comment)
