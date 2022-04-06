from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='author',
                                                   email='author@test.test',
                                                   password='password')
        cls.user = User.objects.create_user(username='test',
                                            email='test@test.test',
                                            password='password')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user_author,
            text='Тестовая пост',
        )
        cls.url_available_to_everyone = {
            '/': ('posts/index.html',
                  'base.html',
                  'includes/header.html',
                  'includes/footer.html'),
            f'/group/{cls.group.slug}/': (
                'posts/group_list.html',
                'base.html',
                'includes/header.html',
                'includes/footer.html'),
            f'/profile/{cls.user_author.username}/': (
                'posts/profile.html',
                'base.html',
                'includes/header.html',
                'includes/footer.html'),
            f'/posts/{cls.post.id}/': (
                'posts/post_detail.html',
                'base.html',
                'includes/header.html',
                'includes/footer.html'),
        }
        cls.url_available_to_author = (f'/posts/{cls.post.id}/edit/',)
        cls.url_available_to_authorized_user = {
            '/create/': ('posts/create_post.html',
                         'base.html',
                         'includes/header.html',
                         'includes/footer.html'),
            f'/posts/{cls.post.id}/edit/': (
                'posts/create_post.html',
                'base.html',
                'includes/header.html',
                'includes/footer.html')
        }
        cls.url_non_existing_page = ('/non_existing_page/',)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.author_client = Client()
        self.authorized_client.force_login(PostURLTests.user)
        self.author_client.force_login(PostURLTests.user_author)

    def test_url_available_to_everyone(self):
        """Проверяем, что доступны страница не требующие авторизацию."""

        for address in PostURLTests.url_available_to_everyone:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code,
                                 HTTPStatus.OK,
                                 f'Страница {address} должна быть доступна '
                                 f'не авторизованному пользователю')

    def test_template_url_available_to_everyone(self):
        """Проверяем, что страницы не требующие авторизацию
        используют правильный шаблон."""

        urls_templates_tuple = PostURLTests.url_available_to_everyone.items()
        for address, templates in urls_templates_tuple:
            for template in templates:
                with self.subTest(address=address, template=template):
                    response = self.guest_client.get(address)
                    self.assertTemplateUsed(
                        response,
                        template,
                        f'Страница {address} должна использовать '
                        f'шаблон "{template}"')

    def test_redirect_to_authorization(self):
        """Проверяем, что страницы требующие авторизацию перенаправляют
        на страницу авторизации."""

        urls = tuple(PostURLTests.url_available_to_authorized_user.keys())
        for address in urls:
            with self.subTest(address=address):
                response = self.guest_client.get(address, follow=True)
                self.assertRedirects(
                    response,
                    f'/auth/login/?next={address}',
                    msg_prefix=f'Страница {address} должна перенаправлять '
                               'не авторизованного пользователя на страницу '
                               f'авторизации /auth/login/?next={address}')

    def test_url_available_to_authorized_user(self):
        """Проверяем, что страницы требующие авторизацию доступны
        авторизованному пользователю."""

        urls = PostURLTests.url_available_to_authorized_user.keys()
        for address in urls:
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertEqual(response.status_code,
                                 HTTPStatus.OK,
                                 f'Страница {address} должна быть '
                                 'доступна авторизованному пользователю')

    def test_template_url_available_to_authorized_user(self):
        """Проверяем, что страницы требующие авторизацию
        используют правильные шаблоны.
        """

        urls = PostURLTests.url_available_to_authorized_user.items()
        for address, templates in urls:
            for template in templates:
                with self.subTest(address=address, template=template):
                    response = self.author_client.get(address)
                    self.assertTemplateUsed(
                        response,
                        template,
                        f'Страница {address} должна использовать '
                        f'шаблон "{template}"')

    def test_url_not_own_post_edit_redirect(self):
        """Проверяем, что страницы редактирования чужого поста
        перенаправляет на просмотр поста."""

        address = PostURLTests.url_available_to_author[0]
        response = self.authorized_client.get(address)
        redirect_url = address.rstrip('edit/') + '/'
        self.assertRedirects(
            response,
            redirect_url,
            msg_prefix=f'Страница {address} должна '
                       'перенаправлять не автора поста на страницу '
                       f'просмотра поста "{redirect_url}"')

    def test_url_edit_own_post(self):
        """Проверяем, что страница редактирования собственного поста доступна.
        """

        address = PostURLTests.url_available_to_author[0]
        response = self.author_client.get(address)
        self.assertEqual(response.status_code,
                         HTTPStatus.OK,
                         f'Страница {address} должна быть доступна '
                         'автору поста')

    def test_url_not_found(self):
        """Проверяем, что не существующая страница возвращает код 404."""

        address = PostURLTests.url_non_existing_page[0]
        response = self.guest_client.get(address)
        self.assertEqual(response.status_code,
                         HTTPStatus.NOT_FOUND,
                         f'Страница {address} должна возвращать '
                         'код 404')
