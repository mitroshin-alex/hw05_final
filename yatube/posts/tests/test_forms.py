from http import HTTPStatus
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings

from ..models import Group, Post, Obscene
from ..forms import PostForm, CommentForm

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test',
                                            email='test@test.test',
                                            password='password')
        cls.user_2 = User.objects.create_user(username='test_2',
                                              email='test2@test.test',
                                              password='password2')
        cls.group = Group.objects.create(
            title='Тестовая группа ',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая пост',
        )
        cls.small_gif_1 = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.small_gif_2 = (
            b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xFF\xFF\xFF"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x01\x00\x01\x00\x00\x02\x01\x00\x00"
        )
        cls.small_gif_3 = (
            b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xFF\xFF\xFF"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x01\x00\x01\x00\x00\x02\x01\x00\x00"
        )
        cls.uploaded_1 = SimpleUploadedFile(
            name='small_1.gif',
            content=cls.small_gif_1,
            content_type='image/gif'
        )
        cls.uploaded_2 = SimpleUploadedFile(
            name='small_2.gif',
            content=cls.small_gif_2,
            content_type='image/gif'
        )
        cls.uploaded_3 = SimpleUploadedFile(
            name='small_3.gif',
            content=cls.small_gif_3,
            content_type='image/gif'
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTests.user)
        self.another_client = Client()
        self.another_client.force_login(PostFormTests.user_2)

    def test_create_new_valid_post(self):
        """Проверяем, что при отправке валидного POST запроса на создание
        нового поста происходит редирект на страницу автора поста,
        увеличивается количество постов в базе данных,
        пост сохраняется с переданными значениями."""
        form_data = (
            {'text': 'новый пост 1',
             'group': PostFormTests.group.id},
            {'text': 'новый пост 2'},
        )
        for form in form_data:
            with self.subTest(form=form):
                post_count = Post.objects.count()
                before = timezone.now()
                response = self.authorized_client.post(
                    reverse('posts:post_create'),
                    data=form,
                    follow=True)
                after = timezone.now()
                self.assertRedirects(
                    response,
                    reverse(
                        'posts:profile',
                        kwargs={'username': PostFormTests.user.username}),
                    msg_prefix='После отправки валидной формы должен быть '
                               'осуществлен редирект на posts:profile '
                               'автора поста')
                self.assertEqual(
                    Post.objects.count(),
                    post_count + 1,
                    'После отправки валидной формы количество постов должно '
                    'увеличится на 1')
                self.assertTrue(
                    Post.objects.filter(
                        text=form.get('text'),
                        group=form.get('group'),
                        author=PostFormTests.user.id,
                        pub_date__range=(before, after)
                    ).exists(),
                    'После отправки валидной формы должен создаться '
                    'пост со всеми полями ')

    def test_edit_exist_post(self):
        """Проверяем, что при отправке валидного POST запроса на изменение
        поста происходит редирект на страницу просмотра измененного поста,
        количество постов в базе данных остается прежним,
        пост содержит новые значения из запроса."""

        post_count = Post.objects.count()
        form_data = {'text': 'Измененный текст',
                     'group': PostFormTests.group.id}
        response = self.authorized_client.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': PostFormTests.post.id}),
            data=form_data,
            follow=True)
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostFormTests.post.id}),
            msg_prefix='После отправки валидной формы должен быть осуществлен '
                       'редирект на posts:post_detail редактируемого поста')
        self.assertEqual(
            Post.objects.count(),
            post_count,
            'После редактирования поста количество постов '
            'должно не изменяться')
        self.assertTrue(
            Post.objects.filter(
                pk=PostFormTests.post.id,
                text=form_data.get('text'),
                group=form_data.get('group'),
                author=PostFormTests.user.id,
                pub_date=PostFormTests.post.pub_date
            ).exists(),
            'После редактирования пост должен содержать новые, '
            'переданные в запросе, значения')

    def test_not_valid_post_form(self):
        """Проверяем, что при отправке не валидного POST запроса
        страница должна быть доступна, количество постов не должно изменяться,
        форма содержит правильные сообщения об ошибке валидации."""

        form_data = (
            (
                {'group': PostFormTests.group.id},
                {'field': 'text',
                 'error': 'Обязательное поле.'}
            ),
            (
                {'text': 'новый пост 2',
                 'group': 99},
                {'field': 'group',
                 'error': 'Выберите корректный вариант. '
                          'Вашего варианта нет среди допустимых значений.'}
            )
        )
        for form, error_info in form_data:
            with self.subTest(form=form):
                post_count = Post.objects.count()
                response = self.authorized_client.post(
                    reverse('posts:post_create'),
                    data=form,
                    follow=True
                )
                self.assertEqual(response.status_code,
                                 HTTPStatus.OK,
                                 'После отправки не валидной формы '
                                 'страница должна быть доступна')
                self.assertEqual(
                    Post.objects.count(),
                    post_count,
                    'После отправки не валидной формы количество постов '
                    'должно не изменяться')
                self.assertFormError(
                    response,
                    'form',
                    error_info.get('field'),
                    error_info.get('error'),
                    msg_prefix='Должно быть правильное сообщение об ошибке '
                               'валидации'
                )

    def test_create_new_valid_post_from_guest(self):
        """Проверяем, что при отправке валидного POST запроса на создание
        нового поста неавторизованным пользователем будет произведен
        редирект на страницу авторизации и не будет создан новый пост."""

        post_count = Post.objects.count()
        form_data = {'text': 'Измененный текст'}
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('users:login') + '?next=' + reverse('posts:post_create'),
            msg_prefix='После отправки валидной формы неавторизованным '
                       'пользователем должен быть осуществлен '
                       'редирект на страницу авторизации')
        self.assertEqual(
            Post.objects.count(),
            post_count,
            'После отправки валидной формы неавторизованным '
            'пользователем количество постов должно оставаться прежним')

    def test_edit_post_from_guest(self):
        """Проверяем, что при отправке валидного POST запроса на
        редактирование существующего поста неавторизованным пользователем
        будет произведен редирект на страницу авторизации
        и пост не будет измене."""

        url = reverse('posts:post_edit',
                      kwargs={'post_id': PostFormTests.post.id})
        form_data = {'text': 'Измененный текст',
                     'group': PostFormTests.group.id}
        response = self.guest_client.post(
            url,
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('users:login') + '?next=' + url,
            msg_prefix='После отправки валидной формы неавторизованным '
                       'пользователем должен быть осуществлен '
                       'редирект на страницу авторизации')
        self.assertFalse(
            Post.objects.filter(
                pk=PostFormTests.post.id,
                text=form_data.get('text'),
                group=form_data.get('group'),
                author=PostFormTests.user.id,
                pub_date=PostFormTests.post.pub_date
            ).exists(),
            'После отправки валидной формы неавторизованным '
            'пользователем пост не должен меняться')

    def test_edit_post_from_another_user(self):
        """Проверяем, что при отправке валидного POST запроса на
        редактирование существующего поста авторизованным пользователем
        отличным от автора поста будет произведен редирект на страницу
        просмотра поста и пост не будет изменен."""

        form_data = {'text': 'Измененный текст',
                     'group': PostFormTests.group.id}
        response = self.another_client.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': PostFormTests.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail',
                    kwargs={'post_id': PostFormTests.post.id}),
            msg_prefix='После отправки валидной формы, пользователем '
                       'отличным от автора поста, должен быть осуществлен '
                       'редирект на просмотр поста')
        self.assertFalse(
            Post.objects.filter(
                pk=PostFormTests.post.id,
                text=form_data.get('text'),
                group=form_data.get('group'),
                author=PostFormTests.user.id,
                pub_date=PostFormTests.post.pub_date
            ).exists(),
            'После отправки валидной формы, пользователем '
            'отличным от автора поста, пост не должен меняться')

    def test_post_form_help_text(self):
        """Проверяем, что форма содержит правильный текст подсказок полей."""

        field_data = {
            'text': 'Текст вашего поста',
            'group': 'Тематическая группа'
        }
        for field, help_text in field_data.items():
            with self.subTest(field=field):
                title_help_text = PostFormTests.form.fields[
                    field].help_text
                self.assertEqual(title_help_text,
                                 help_text, f'Для поля "{field}" текст '
                                            f'подсказки: "{help_text}"')

    def test_post_form_image(self):
        """Проверяем, что при отправке валидного POST запроса на
        создание поста с картинкой, пост создается в базе данных."""

        post_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост с картинкой',
            'group': PostFormTests.group.id,
            'image': PostFormTests.uploaded_1,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True)

        self.assertEqual(response.status_code,
                         HTTPStatus.OK,
                         'После отправки не валидной формы '
                         'страница должна быть доступна')
        self.assertEqual(
            Post.objects.count(),
            post_count + 1,
            'После отправки валидной формы количество постов '
            'должно увеличиться на 1')
        self.assertTrue(
            Post.objects.filter(
                author=PostFormTests.user.id,
                text=form_data['text'],
                group=form_data['group'],
                image='posts/small_1.gif'
            ).exists()
        )

    def test_post_form_edit_image(self):
        """Проверяем, что при отправке валидного POST запроса на
        добавление, изменение и удаление картинкой, пост правильно
        записывается в базу данных."""

        post_count = Post.objects.count()
        form_data_tuple = (
            {'text': PostFormTests.post.text,
             'image': PostFormTests.uploaded_2},
            {'text': PostFormTests.post.text,
             'image': PostFormTests.uploaded_3},
            {'text': PostFormTests.post.text,
             'image': ''},
        )
        for form_data in form_data_tuple:
            with self.subTest(form_data=form_data):
                response = self.authorized_client.post(
                    reverse('posts:post_edit',
                            kwargs={'post_id': PostFormTests.post.id}),
                    data=form_data,
                    follow=True)
                self.assertEqual(response.status_code,
                                 HTTPStatus.OK,
                                 'После отправки валидной формы '
                                 'страница должна быть доступна')
                self.assertEqual(
                    Post.objects.count(),
                    post_count,
                    'После отправки валидной формы количество постов '
                    'должно оставаться неизменным')
                image = form_data.get("image")
                if image:
                    self.assertTrue(
                        Post.objects.filter(
                            author=PostFormTests.user.id,
                            text=PostFormTests.post.text,
                            image=f'posts/{image}'
                        ).exists(),
                        'У поста должна быть использована '
                        f'картинка {str(image)}'
                    )
                else:
                    self.assertTrue(
                        PostFormTests.post.image == image,
                        'У поста должна отсутствовать картинка'
                    )


class CommentFormTest(TestCase):
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
        cls.url = reverse('posts:add_comment',
                          kwargs={'post_id': cls.post.id})
        cls.form = CommentForm()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(CommentFormTest.user)

    def test_comment_from_guest(self):
        """Проверяем, что гости не могут комментировать."""

        count = CommentFormTest.post.comments.count()
        form_data = {'text': 'Тестовый комментарий'}

        response = self.guest_client.post(CommentFormTest.url,
                                          data=form_data,
                                          follow=True)

        self.assertRedirects(
            response,
            reverse('users:login') + '?next=' + CommentFormTest.url,
            msg_prefix='После отправки валидной формы неавторизованным '
                       'пользователем должен быть осуществлен '
                       'редирект на страницу авторизации')

        self.assertEqual(count,
                         CommentFormTest.post.comments.count(),
                         'Количество комментариев должно остаться прежним')

    def test_comment_from_authorized_client(self):
        """Проверяем, что авторизованные пользователи могут комментировать
        и комментарии доступны на странице."""

        count = CommentFormTest.post.comments.count()
        form_data = {
            'text': 'Тестовый комментарий авторизованного пользователя'
        }
        response = self.authorized_client.post(
            CommentFormTest.url,
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail',
                    kwargs={'post_id': CommentFormTest.post.id}),
            msg_prefix='После отправки валидной формы авторизованным '
                       'пользователем должен быть осуществлен '
                       'редирект страницу поста'
        )
        self.assertEqual(CommentFormTest.post.comments.count(),
                         count + 1,
                         'Количество комментариев должно увеличиться на 1')

    def test_comment_from_text_validator(self):
        """Проверяем, что в комментарии с запретным словом оно заменится на
        количество звездочек равной длине слова."""

        word = 'донцова'
        Obscene.objects.create(word=word)
        form_data = {
            'text': f'Тестовый комментарий о {word.upper()}'
        }
        response = self.authorized_client.post(
            CommentFormTest.url,
            data=form_data,
            follow=True
        )
        self.assertContains(response,
                            '*' * len(word),
                            'Текст страницы не должен содержать '
                            'запретное слово')
