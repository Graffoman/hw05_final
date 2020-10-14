from datetime import datetime

from django.core.cache import cache
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.test import Client, TestCase
from django.urls import reverse

from .models import Comment, Follow, Group, Post, User

#   python manage.py test posts.tests


class PostsAppTestKit(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='test_user', email='test@skynet.com', password='12345'
        )
        self.test_group = Group.objects.create(
            title='Тестовая группа', slug='test-link',
            description='Тестовое описание группы'
        )

        self.client = Client()
        self.client.force_login(self.user)
        self.no_auth_client = Client()

        with open('posts/tests/test_image.jpg', 'rb') as img:
            self.client.post(
                reverse('new_post'),
                {
                    'text': 'Тестовый текст',
                    'author': self.user,
                    'group': self.test_group.id,
                    'image': img
                }
            )

    def common_tests(self):
        resp_profile = self.client.get(
            reverse('profile', args=[self.user.username])
        )
        resp_index = self.client.get(reverse('index'))
        resp_group = self.client.get(
            reverse('group', args=[self.test_group.slug])
        )

        try:
            test_post = Post.objects.get(text='Тестовый текст')
        except Post.DoesNotExist:
            test_post = Post.objects.get(text='Edited')
            return test_post
        resp_test_post = self.client.get(
            reverse(
                'post', args=[test_post.author.username, test_post.id]
            )
        )
        self.assertEqual(resp_test_post.status_code, 200)
        self.assertIn(
            '<img class="card-img"', resp_test_post.content.decode('utf-8')
        )

        resps = [resp_profile, resp_index, resp_group]
        for resp in resps:
            post_list = resp.context['paginator'].page(1)
            self.assertIn(test_post, post_list)
            self.assertEqual(len(post_list.object_list), 1)
            self.assertIn(
                '<img class="card-img"', resp.content.decode('utf-8')
            )

    def test_profile(self):
        resp_profile = self.client.get(
            reverse('profile', args=[self.user.username])
        )
        self.assertEqual(resp_profile.status_code, 200)

    def test_newpost_no_auth(self):
        resp_newpost = self.no_auth_client.post(
            reverse('new_post'), {'text': 'Другой тестовый текст'}, follow=True
        )
        self.assertRedirects(
            resp_newpost, reverse('login')+'?next='+reverse('new_post'),
            status_code=302
        )
        with self.assertRaises(Http404):
            get_object_or_404(Post, text='Другой тестовый текст')

    def test_newpost_with_auth(self):
        self.common_tests()

    def test_post_edit(self):
        test_post = get_object_or_404(Post, text='Тестовый текст')
        resp_edit = self.client.post(
            reverse(
                'post_edit', args=[test_post.author.username, test_post.id]
            ),
            {
                'text': 'Edited',
                'group': test_post.group.id,
            },
            follow=True
        )
        edited_post = get_object_or_404(Post, text='Edited')
        url = reverse(
            'post', args=[edited_post.author.username, edited_post.id]
        )
        self.assertRedirects(resp_edit, url, status_code=302)

        with self.assertRaises(Http404):
            get_object_or_404(Post, text='Тестовый текст')

        with open('posts/tests/test_text.txt', 'rb') as txt:
            response = self.client.post(
                reverse(
                    'post_edit', args=[test_post.author.username, test_post.id]
                ),
                {
                    'text': 'Тестовый текст',
                    'group': test_post.group.id,
                    'image': txt
                }
            )
        self.assertFormError(
            response, 'form', 'image', (
                'Upload a valid image. '
                'The file you uploaded was either not an image '
                'or a corrupted image.'
            )
        )
        self.common_tests()

    def test_page_not_found(self):
        response = self.client.get('not_existing_page/')
        self.assertEqual(response.status_code, 404)

    def tearDown(self):
        cache.clear()


class TestCache(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='test_user', email='test@skynet.com', password='12345'
        )

    def test_cashed_index(self):
        Post.objects.create(
            text='Тестовый текст', author=self.user
            )
        cache.clear()
        start_time = datetime.now()
        self.client.get(reverse('index'))
        finish_time = datetime.now()
        duration_no_cache = finish_time - start_time

        start_time = datetime.now()
        self.client.get(reverse('index'))
        finish_time = datetime.now()
        duration_with_cache = finish_time - start_time

        self.assertTrue(duration_no_cache > duration_with_cache)

    def tearDown(self):
        cache.clear()


class FollowTestKit(TestCase):
    def setUp(self):
        self.follower = User.objects.create_user(
            username='test_user1', email='test@skynet.com', password='12345'
        )
        self.celebrity = User.objects.create_user(
            username='test_user2', email='test2@skynet.com', password='12345'
        )

        self.client_follower = Client()
        self.client_follower.force_login(self.follower)
        self.client_follower.get(
            reverse('profile_follow', args=[self.celebrity.username])
        )
        self.client_celebrity = Client()
        self.client_celebrity.force_login(self.celebrity)

    def get_follow(self):
        try:
            follow = get_object_or_404(
                Follow, user=self.follower, author=self.celebrity
            )
            follow = True
        except Http404:
            follow = False
        finally:
            return follow

    def test_auth_follow(self):
        self.assertEqual(self.get_follow(), True)
        self.client_follower.get(
            reverse('profile_unfollow', args=[self.celebrity.username])
        )
        self.assertEqual(self.get_follow(), False)

    def test_follow_index(self):
        post = Post.objects.create(
            text='Тестовый текст', author=self.celebrity
            )
        resp_fol = self.client_follower.get(reverse('follow_index'))
        post_list = resp_fol.context['paginator'].page(1)
        self.assertIn(post, post_list)

        resp_cel = self.client_celebrity.get(reverse('follow_index'))
        post_list = resp_cel.context['paginator'].page(1)
        self.assertNotIn(post, post_list)

    def tearDown(self):
        cache.clear()


class CommentTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='test_user', email='test@skynet.com', password='12345'
        )
        self.client = Client()
        self.client.force_login(self.user)
        self.no_auth_client = Client()
        self.post = Post.objects.create(
            text='Тестовый текст', author=self.user
            )

    def get_comment(self):
        try:
            comment = get_object_or_404(
                Comment, text='тестовый коммент'
            )
            comment = True
        except Http404:
            comment = False
        finally:
            return comment

    def test_comment_with_auth(self):
        self.client.post(
            reverse('add_comment', args=[self.user.username, self.post.id]),
            {'text': 'тестовый коммент'}
        )
        self.assertEqual(self.get_comment(), True)

    def tearDown(self):
        cache.clear()
