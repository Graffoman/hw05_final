from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField('Группа', max_length=200)
    slug = models.SlugField(max_length=50, unique=True)
    description = models.TextField('Описание')

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField('Текст')
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='posts',
        verbose_name='Автор'
    )
    group = models.ForeignKey(
        Group, on_delete=models.SET_NULL,
        blank=True, null=True, related_name='posts', verbose_name='Группа'
    )
    image = models.ImageField(
        upload_to='posts/', blank=True, null=True, verbose_name='Изображение'
    )

    class Meta:
        ordering = ['-pub_date']

    def __str__(self):
        post_info = (
            f'{self.author} : '
            f'{self.pub_date.strftime("%m/%d/%Y")} : '
            f'{self.text[:20]} ...'
        )
        return post_info


class Comment(models.Model):
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE,
        blank=True, null=True, related_name='comments',
        verbose_name='Пост'
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        blank=True, null=True, related_name='comments',
        verbose_name='Автор комментария'
    )
    text = models.TextField('Текст комментария', max_length=200)
    created = models.DateTimeField('Дата комментария', auto_now_add=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        comment_info = (
            f'{self.author} : '
            f'{self.created.strftime("%m/%d/%Y")} : '
            f'{self.text[:20]} ...'
        )
        return comment_info


class Follow(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, blank=True, null=True,
        related_name='follower', verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, blank=True, null=True,
        related_name='following', verbose_name='Тот, на кого подписались'
    )

    class Meta:
        unique_together = (('user', 'author'),)

    def __str__(self):
        follow_info = (
            f'{self.user.username} подписан на: {self.author.username}'
        )
        return follow_info
