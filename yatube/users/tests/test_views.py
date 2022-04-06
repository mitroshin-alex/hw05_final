from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django import forms

User = get_user_model()


class UsersPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test',
                                            email='test@test.test',
                                            password='password')

        cls.urls_guest = {
            reverse('users:signup'): 'users/signup.html',
            reverse('users:password_reset'): 'users/password_reset_form.html',
            reverse('users:password_reset_done'):
                'users/password_reset_done.html',
            reverse('users:password_reset_confirm',
                    kwargs={'uidb64': 'Mw',
                            'token': '5yv-3d093067c3046ccf91fe'}):
                'users/password_reset_confirm.html',
            reverse('users:password_reset_complete'):
                'users/password_reset_complete.html',
            reverse('users:login'): 'users/login.html',

        }
        cls.urls_authorized_client = {
            reverse('users:password_change'):
                'users/password_change_form.html',
            reverse('users:password_change_done'):
                'users/password_change_done.html',
            reverse('users:logout'): 'users/logged_out.html',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(UsersPagesTests.user)

    def test_page_available_to_everyone(self):
        """Проверяем, что доступны страница не требующие авторизацию
        по namespase:name."""

        for address in UsersPagesTests.urls_guest:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code,
                                 HTTPStatus.OK,
                                 f'Страница {address} должна быть доступна '
                                 f'не авторизованному пользователю')

    def test_template_page_available_to_everyone(self):
        """Проверяем, что страницы не требующие авторизацию
        используют правильный шаблон по namespase:name."""

        for address, template in UsersPagesTests.urls_guest.items():
            with self.subTest(address=address, template=template):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(
                    response,
                    template,
                    f'Страница {address} должна использовать '
                    f'шаблон "{template}"')

    def test_page_available_to_authorized_user(self):
        """Проверяем, что страницы требующие авторизацию доступны
        авторизованному пользователю по namespase:name."""

        for address in UsersPagesTests.urls_authorized_client.keys():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code,
                                 HTTPStatus.OK,
                                 f'Страница {address} должна быть '
                                 'доступна авторизованному пользователю')

    def test_template_page_available_to_authorized_user(self):
        """Проверяем, что страницы требующие авторизацию
        используют правильные шаблоны по namespase:name.
        """

        urls = UsersPagesTests.urls_authorized_client.items()
        for address, template in urls:
            with self.subTest(address=address, template=template):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(
                    response,
                    template,
                    f'Страница {address} должна использовать '
                    f'шаблон "{template}"')

    def test_context_post_edit_page(self):
        """Проверяем, что контекст страницы содержит
        правильный тип полей формы."""

        form_fields = {
            'first_name': forms.fields.CharField,
            'last_name': forms.fields.CharField,
            'username': forms.fields.CharField,
            'email': forms.fields.EmailField,
        }
        response = self.authorized_client.get(reverse('users:signup'))
        for field, expected in form_fields.items():
            with self.subTest(field=field):
                form_field = response.context.get('form').fields.get(field)
                self.assertIsInstance(
                    form_field,
                    expected,
                    'Контекст страницы posts:post_edit '
                    f'содержит правильный тип поля "{field}"')
