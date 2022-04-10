from django import forms

from .models import Post, Comment, Obscene


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        help_texts = {
            'text': 'Текст вашего поста',
            'group': 'Тематическая группа',
            'image': 'Картинка'
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)

    def clean_text(self):
        obscene = set(Obscene.objects.values_list('word', flat=True))
        text_list = self.cleaned_data['text'].split()
        for i, word in enumerate(text_list):
            if word.strip().lower() in obscene:
                text_list[i] = '*' * len(text_list[i])
        return ' '.join(text_list)
