from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse


class AboutViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.url_available_to_everyone = {
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html',
        }

    def setUp(self):
        self.guest_client = Client()

    def test_about_pages(self):
        """Проверяем, что доступны страницы технологии и автор."""

        urls = AboutViewsTests.url_available_to_everyone.keys()
        for address in urls:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code,
                                 HTTPStatus.OK,
                                 f'Страница {address} должна быть '
                                 'доступна всем')

    def test_template_url_available_to_guest_user(self):
        """Проверяем, что страницы технологии и автор
        используют правильный шаблон.
        """

        urls = AboutViewsTests.url_available_to_everyone.items()
        for address, template in urls:
            with self.subTest(address=address, template=template):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(
                    response,
                    template,
                    f'Страница {address} должна использовать '
                    f'шаблон "{template}"')
