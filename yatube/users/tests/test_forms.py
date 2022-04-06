from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from ..forms import UserCreationForm

User = get_user_model()


class UserFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.form = UserCreationForm()

    def setUp(self):
        self.guest_client = Client()

    def test_create_new_user(self):
        form_data = {
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'username': 'ivanov',
            'email': 'test@test.test',
            'password1': '1qwerty.',
            'password2': '1qwerty.',
        }
        user_count = User.objects.count()
        response = self.guest_client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True)
        self.assertRedirects(
            response,
            reverse(
                'posts:index'),
            msg_prefix='После отправки валидной формы должен быть осуществлен '
                       'редирект на главную страницу')
        self.assertEqual(
            User.objects.count(),
            user_count + 1,
            'После отправки валидной формы количество пользователей должно '
            'увеличится на 1')
        self.assertTrue(
            User.objects.filter(
                first_name=form_data.get('first_name'),
                last_name=form_data.get('last_name'),
                username=form_data.get('username'),
                email=form_data.get('email')
            ).exists(),
            'После отправки валидной формы должен создаться '
            'пользователь со всеми полями ')
