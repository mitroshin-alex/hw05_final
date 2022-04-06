import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from ..models import Group, Post, Follow

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
TEST_CACHE_SETTING = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

User = get_user_model()


@override_settings(CACHES=TEST_CACHE_SETTING)
@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test',
                                            email='test@test.test',
                                            password='password')
        cls.group_1 = Group.objects.create(
            title='Тестовая группа 1',
            slug='test_slug1',
            description='Тестовое описание 1',
        )
        cls.group_2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test_slug2',
            description='Тестовое описание 2',
        )
        cls.group_3 = Group.objects.create(
            title='Тестовая группа 3',
            slug='test_slug3',
            description='Тестовое описание 3',
        )
        cls.post_1 = Post.objects.create(
            author=cls.user,
            text='Тестовая пост 1',
        )
        cls.post_2 = Post.objects.create(
            author=cls.user,
            text='Тестовая пост 2',
            group=cls.group_1
        )
        cls.post_3 = Post.objects.create(
            author=cls.user,
            text='Тестовая пост 3',
            group=cls.group_2
        )
        cls.templates_pages_names = {
            reverse('posts:index'):
                'posts/index.html',
            reverse('posts:group_detail',
                    kwargs={'slug': cls.group_1.slug}):
                'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': cls.user.username}):
                'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': cls.post_1.id}):
                'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': cls.post_1.id}):
                'posts/create_post.html',
            reverse('posts:post_create'):
                'posts/create_post.html'
        }
        cls.urls = (
            reverse('posts:index'),
            reverse('posts:group_detail',
                    kwargs={'slug': cls.group_3.slug}),
            reverse('posts:profile',
                    kwargs={'username': cls.user.username}),
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)

    def test_pages_template(self):
        """Проверяем, что страницы по namespase:name
        используют правильный шаблон."""
        urls_templates = PostPagesTests.templates_pages_names.items()
        for address, template in urls_templates:
            with self.subTest(address=address, template=template):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(
                    response,
                    template,
                    f'Страница {address} должна использовать '
                    f'шаблон "{template}"')

    def test_context_index_page(self):
        """Проверяем, что контекст главной страницы содержит все посты."""

        posts = Post.objects.all()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertSequenceEqual(
            posts,
            response.context.get('page_obj').object_list,
            'Контекст страницы posts:index должен содержать все посты')

    def test_context_group_page(self):
        """Проверяем, что контекст страницы группы содержит правильную группу
        и все посты группы."""

        groups = (
            PostPagesTests.group_1,
            PostPagesTests.group_2,
        )
        for group in groups:
            group_post = Post.objects.filter(group=group)
            with self.subTest(group=group):
                response = self.authorized_client.get(
                    reverse('posts:group_detail',
                            kwargs={'slug': group.slug})
                )
                self.assertEqual(group.id,
                                 response.context.get('group').id,
                                 'Контекст страницы posts:group_detail группы '
                                 f'"{group.title}" содержит правильную группу')
                self.assertSequenceEqual(
                    group_post,
                    response.context.get('page_obj').object_list,
                    'Контекст страницы posts:group_detail группы '
                    f'"{group.title}" содержит все посты')

    def test_context_profile_page(self):
        """Проверяем, что контекст страницы профиля содержит правильные
        посты, счетчик постов автора и автора."""

        author = PostPagesTests.user
        posts = Post.objects.filter(author=author)
        count = posts.count()
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': author.username})
        )
        self.assertEqual(author.id,
                         response.context.get('author').id,
                         'Контекст страницы posts:profile '
                         f'пользователя "{author.username}" '
                         'содержит правильного пользователя')
        self.assertEqual(count,
                         response.context.get('count'),
                         'Контекст страницы posts:profile '
                         f'пользователя "{author.username}" '
                         'содержит правильное количество постов')
        self.assertSequenceEqual(posts,
                                 response.context.get('page_obj').object_list,
                                 'Контекст страницы posts:profile '
                                 f'пользователя "{author.username}" '
                                 'содержит все посты пользователя')

    def test_context_post_detail_page(self):
        """Проверяем, что контекст страницы поста содержит правильный
        пост и счетчик постов автора."""

        count = Post.objects.filter(author=PostPagesTests.user).count()
        post = PostPagesTests.post_1
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': post.id})
        )
        self.assertEqual(count,
                         response.context.get('count'),
                         'Контекст страницы posts:post_detail '
                         f'поста №{post.id} '
                         f'пользователя "{PostPagesTests.user.username}" '
                         'содержит правильное количество постов автора')
        self.assertEqual(post.text,
                         response.context.get('post').text,
                         'Контекст страницы posts:post_detail '
                         f'поста №{post.id} '
                         'содержит правильный пост')

    def test_context_post_create_page(self):
        """Проверяем, что контекст страницы создания поста содержит правильную
        форму."""

        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        response = self.authorized_client.get(reverse('posts:post_create'))
        for field, expected in form_fields.items():
            with self.subTest(field=field):
                form_field = response.context.get('form').fields.get(field)
                self.assertIsInstance(
                    form_field,
                    expected,
                    'Контекст страницы posts:post_create '
                    f'содержит правильный тип поля "{field}"')

    def test_context_post_edit_page(self):
        """Проверяем, что контекст страницы редактирования поста содержит
        правильную форму, пост и признак редактирования."""

        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        post = PostPagesTests.post_2
        response = self.authorized_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': post.id}))
        self.assertTrue(response.context.get('is_edit'),
                        'Контекст страницы posts:post_edit '
                        'содержит признак редактирования поста')
        for field, expected in form_fields.items():
            with self.subTest(field=field):
                instance = response.context.get('form').instance
                form_field = response.context.get('form').fields.get(field)
                self.assertIsInstance(
                    form_field,
                    expected,
                    'Контекст страницы posts:post_edit '
                    f'содержит правильный тип поля "{field}"')
                self.assertEqual(getattr(instance, field),
                                 getattr(post, field),
                                 'Контекст страницы posts:post_edit '
                                 'содержит правильно пред заполненное '
                                 f'поле"{field}"')

    def test_new_post_existing(self):
        """Проверяем, что новый пост с группой отображается где надо
        и содержит картинку."""

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        post = Post.objects.create(
            author=PostPagesTests.user,
            text='Новый тестовый пост',
            group=PostPagesTests.group_3,
            image=uploaded
        )
        for url in PostPagesTests.urls:
            response = self.authorized_client.get(url)
            with self.subTest(url=url):
                self.assertIn(post,
                              response.context.get('page_obj').object_list,
                              'Пост должен быть доступен на странице')
                self.assertEqual(
                    post.image,
                    response.context.get('page_obj').object_list[0].image,
                    'Пост должен содержать правильную картинку')

        response_post_detail = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': post.id})
        )
        self.assertEqual(
            post.image,
            response_post_detail.context.get('post').image,
            'Пост должен содержать правильную картинку')

        response_group_1 = self.authorized_client.get(
            reverse('posts:group_detail',
                    kwargs={'slug': PostPagesTests.group_1.slug})
        )
        self.assertNotIn(post,
                         response_group_1.context.get('page_obj').object_list,
                         'Пост должен отсутствовать на странице '
                         f'"{PostPagesTests.group_1.slug}"')


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test',
                                            email='test@test.test',
                                            password='password')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.additional_post_number = settings.NUMBER_OF_POSTS_DISPLAYED // 2
        Post.objects.bulk_create(
            (
                Post(author=cls.user,
                     text=f'Новый тестовый пост {i}',
                     group=cls.group)
                for i in range(settings.NUMBER_OF_POSTS_DISPLAYED
                               + cls.additional_post_number)
            )
        )
        cls.urls = (
            reverse('posts:index'),
            reverse('posts:group_detail',
                    kwargs={'slug': cls.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': cls.user.username}),
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorViewsTest.user)

    def test_first_page_records(self):
        """Проверяем, что на первой странице нужное количество постов."""

        for url in PaginatorViewsTest.urls:
            response = self.authorized_client.get(url)
            with self.subTest(url=url):
                self.assertEqual(
                    len(response.context.get('page_obj')),
                    settings.NUMBER_OF_POSTS_DISPLAYED,
                    f'На первой странице {url} '
                    'количество постов должно быть = '
                    f'{settings.NUMBER_OF_POSTS_DISPLAYED}')

    def test_second_page_contains_three_records(self):
        """Проверяем, что на второй странице нужное количество постов."""

        for url in PaginatorViewsTest.urls:
            response = self.authorized_client.get(url + '?page=2')
            with self.subTest(url=url):
                self.assertEqual(
                    len(response.context.get('page_obj')),
                    PaginatorViewsTest.additional_post_number,
                    f'На второй странице {url} '
                    'количество постов должно быть = '
                    f'{PaginatorViewsTest.additional_post_number}')


class CachePagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test',
                                            email='test@test.test',
                                            password='password')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая пост',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(CachePagesTests.user)

    def test_cache_index_page(self):
        """Проверяем, что главная страница кэшируется."""

        post = Post.objects.create(
            author=CachePagesTests.user,
            text='Тестовая пост до кэширования',
        )
        url = reverse('posts:index')
        response_before = self.authorized_client.get(url)
        self.assertIn(
            post,
            response_before.context.get('page_obj').object_list,
            'Пост должен быть на главной странице до кэширования')
        post.delete()
        response_after = self.authorized_client.get(url)
        self.assertEqual(response_before.content,
                         response_after.content,
                         'Содержимое страницы после удаления поста '
                         'должно не измениться')
        cache.clear()
        response_clear = self.authorized_client.get(url)
        self.assertNotEqual(response_after.content,
                            response_clear.content,
                            'Содержимое страницы после удаления поста '
                            'и очистки кэша должно измениться')


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_1 = User.objects.create_user(username='test_1',
                                              email='test_1@test.test',
                                              password='password')
        cls.user_2 = User.objects.create_user(username='test_2',
                                              email='test_2@test.test',
                                              password='password')
        cls.user_3 = User.objects.create_user(username='test_3',
                                              email='test_3@test.test',
                                              password='password')
        cls.post_1 = Post.objects.create(
            author=cls.user_1,
            text='Тестовая пост 1',
        )
        cls.post_2 = Post.objects.create(
            author=cls.user_2,
            text='Тестовая пост 2',
        )
        cls.post_3 = Post.objects.create(
            author=cls.user_3,
            text='Тестовая пост 3',
        )
        cls.url_follow_index = reverse('posts:follow_index')
        cls.url_profile = reverse(
            'posts:profile',
            kwargs={
                'username': FollowTests.user_2.username})
        cls.url_follow = reverse(
            'posts:profile_follow',
            kwargs={
                'username': FollowTests.user_2.username})
        cls.url_unfollow = reverse(
            'posts:profile_unfollow',
            kwargs={
                'username': FollowTests.user_2.username})

        Follow.objects.create(user=cls.user_3, author=cls.user_2)

    def setUp(self):
        self.authorized_client_1 = Client()
        self.authorized_client_2 = Client()
        self.authorized_client_3 = Client()
        self.authorized_client_1.force_login(FollowTests.user_1)
        self.authorized_client_2.force_login(FollowTests.user_2)
        self.authorized_client_3.force_login(FollowTests.user_3)

    def test_following_and_unfollowing(self):
        """Проверяем, что пользователь может подписаться и отписаться."""

        self.assertFalse(
            Follow.objects.filter(
                user=FollowTests.user_1,
                author=FollowTests.user_2
            ).exists(),
            'Пользователь 1 не должен быть подписан на пользователя 2'
        )
        response_follow = self.authorized_client_1.get(
            FollowTests.url_follow,
            follow=True
        )
        self.assertRedirects(
            response_follow,
            FollowTests.url_profile,
            msg_prefix='После подписывания на автора должен '
                       'быть осуществлен редирект на страницу автора'
        )
        self.assertTrue(
            Follow.objects.filter(
                user=FollowTests.user_1,
                author=FollowTests.user_2
            ).exists(),
            'Подписка должна быть в базе данных'
        )
        response_unfollow = self.authorized_client_1.get(
            FollowTests.url_unfollow,
            follow=True
        )
        self.assertRedirects(
            response_unfollow,
            FollowTests.url_profile,
            msg_prefix='После отписывания от автора должен '
                       'быть осуществлен редирект на страницу автора'
        )
        self.assertFalse(
            Follow.objects.filter(
                user=FollowTests.user_1,
                author=FollowTests.user_2
            ).exists(),
            'Пользователь 1 не должен быть подписан на пользователя 2'
        )

    def test_follow_index(self):
        """Проверяем, что новый пост по подписке появляется у подписанта
        и не появляется у не подписанного пользователя."""

        post = Post.objects.create(
            text='Тестовый пост для подписки',
            author=FollowTests.user_2
        )
        response_follow_index = self.authorized_client_3.get(
            FollowTests.url_follow_index
        )
        self.assertIn(
            post,
            response_follow_index.context.get('page_obj').object_list,
            'Пост должен быть в ленте подписанного пользователя'
        )
        response_follow_index_not_following = self.authorized_client_1.get(
            FollowTests.url_follow_index
        )
        self.assertNotIn(
            post,
            response_follow_index_not_following.context.get(
                'page_obj'
            ).object_list,
            'Пост должен отсутствовать в ленте подписанного пользователя'
        )
