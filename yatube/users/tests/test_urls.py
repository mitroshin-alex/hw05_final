from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client

User = get_user_model()


class UsersURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test',
                                            email='test@test.test',
                                            password='password')
        cls.urls_guest = {
            '/auth/signup/': 'users/signup.html',
            '/auth/password_reset/': 'users/password_reset_form.html',
            '/auth/password_reset/done/': 'users/password_reset_done.html',
            '/auth/reset/Mw/5yv-3d093067c3046ccf91fe/':
                'users/password_reset_confirm.html',
            '/auth/reset/done/': 'users/password_reset_complete.html',
            '/auth/login/': 'users/login.html',

        }
        cls.urls_authorized_client = {
            '/auth/password_change/': 'users/password_change_form.html',
            '/auth/password_change/done/': 'users/password_change_done.html',
            '/auth/logout/': 'users/logged_out.html',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(UsersURLTests.user)

    def test_url_available_to_everyone(self):
        """Проверяем, что доступны страница не требующие авторизацию."""

        for address in UsersURLTests.urls_guest:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code,
                                 HTTPStatus.OK,
                                 f'Страница {address} должна быть доступна '
                                 f'неавторизованному пользователю')

    def test_template_url_available_to_everyone(self):
        """Проверяем, что страницы не требующие авторизацию
        используют правильный шаблон."""

        for address, template in UsersURLTests.urls_guest.items():
            with self.subTest(address=address, template=template):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(
                    response,
                    template,
                    f'Страница {address} должна использовать '
                    f'шаблон "{template}"')

    def test_url_available_to_authorized_user(self):
        """Проверяем, что страницы требующие авторизацию доступны
        авторизованному пользователю."""

        for address in UsersURLTests.urls_authorized_client.keys():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code,
                                 HTTPStatus.OK,
                                 f'Страница {address} должна быть '
                                 'доступна авторизованному пользователю')

    def test_template_url_available_to_authorized_user(self):
        """Проверяем, что страницы требующие авторизацию
        используют правильные шаблоны.
        """

        for address, template in UsersURLTests.urls_authorized_client.items():
            with self.subTest(address=address, template=template):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(
                    response,
                    template,
                    f'Страница {address} должна использовать '
                    f'шаблон "{template}"')
