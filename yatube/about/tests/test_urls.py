from http import HTTPStatus

from django.test import TestCase, Client


class AboutURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.url_available_to_everyone = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }

    def setUp(self):
        self.guest_client = Client()

    def test_about_url(self):
        """Проверяем, что доступны страницы технологии и автор."""

        urls = AboutURLTests.url_available_to_everyone.keys()
        for address in urls:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code,
                                 HTTPStatus.OK,
                                 f'Страница {address} должна быть '
                                 'доступна всем')

    def test_template_url_available_to_authorized_user(self):
        """Проверяем, что страницы технологии и автор
        используют правильный шаблон.
        """

        urls = AboutURLTests.url_available_to_everyone.items()
        for address, template in urls:
            with self.subTest(address=address, template=template):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(
                    response,
                    template,
                    f'Страница {address} должна использовать '
                    f'шаблон "{template}"')
