from django.contrib.auth import get_user_model
from django.test import TestCase
from django.conf import settings

from ..models import Group, Post, Comment, Follow

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая пост длиной больше 15 символов',
        )

    def test_post_have_correct_object_names(self):
        """Проверяем, что у модели Post корректно работает __str__."""

        post = PostModelTest.post
        self.assertEqual(str(post),
                         post.text[:settings.POST_STR_LIMIT],
                         'Для модели Post строковое представление должно быть '
                         'срезом поля text длиной не более '
                         f'{settings.POST_STR_LIMIT} символов')

    def test_post_help_text(self):
        """Проверяем, что у модели Post
        help_text в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
            'image': 'Картинка вашего поста'
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text,
                    expected_value,
                    f'Для модели Post help_text поля {field} '
                    f'должно быть: "{expected_value}"'
                )

    def test_post_verbose_name(self):
        """Проверяем, что у модели Post
        verbose_name в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_verbose_name = {
            'text': 'Текст поста',
            'group': 'Группа',
            'image': 'Картинка поста'
        }
        for field, expected_value in field_verbose_name.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name,
                    expected_value,
                    f'Для модели Post verbose_name поля {field} '
                    f'должно быть: "{expected_value}"'
                )


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )

    def test_group_have_correct_object_names(self):
        """Проверяем, что у модели Group корректно работает __str__."""

        group = GroupModelTest.group
        self.assertEqual(str(group),
                         group.title,
                         'Для модели Group строковое '
                         'представление должно быть равно полю title'
                         )

    def test_group_verbose_name(self):
        """Проверяем, что у модели Group
        verbose_name в полях совпадает с ожидаемым."""
        group = GroupModelTest.group
        field_verbose_name = {
            'title': 'Заголовок группы',
            'slug': 'Название группы',
            'description': 'Описание группы',
        }
        for field, expected_value in field_verbose_name.items():
            with self.subTest(field=field):
                self.assertEqual(
                    group._meta.get_field(field).verbose_name,
                    expected_value,
                    f'Для модели Group verbose_name поля {field} '
                    f'должно быть: "{expected_value}"'
                )


class CommentModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая пост',
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый комментарий длиннее 15 символов',
        )

    def test_comment_have_correct_object_names(self):
        """Проверяем, что у модели Comment корректно работает __str__."""

        comment = CommentModelTest.comment
        self.assertEqual(str(comment),
                         comment.text[:settings.COMMENT_STR_LIMIT],
                         'Для модели Comment строковое представление должно '
                         'быть срезом поля text длиной не более '
                         f'{settings.COMMENT_STR_LIMIT} символов')


class FollowModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_1 = User.objects.create_user(username='user_1')
        cls.user_2 = User.objects.create_user(username='user_2')
        cls.follow = Follow.objects.create(
            user=cls.user_1,
            author=cls.user_2
        )

    def test_follow_have_correct_object_names(self):
        """Проверяем, что у модели Follow корректно работает __str__."""

        follow = FollowModelTest.follow
        self.assertEqual(str(follow),
                         f'{follow.user.username} подписан '
                         f'на {follow.author.username}',
                         'Для модели Follow строковое '
                         'представление должно быть равно '
                         'user.username + " подписан на " + '
                         'author.username'
                         )
