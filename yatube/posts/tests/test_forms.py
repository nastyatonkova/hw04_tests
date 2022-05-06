from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User


class PostFormTest(TestCase):

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.user = User.objects.create_user(username='auth')
        self.group = Group.objects.create(
            title='Test group',
            slug='test-slug',
            description='Test description',
        )
        self.post = Post.objects.create(
            author=self.user,
            text='Test text',
            group=self.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_group_post(self):
        """Valid form creates post in Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Another test',
            'group': self.group.id,
            'author_id': self.user.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        last_object = response.context['page_obj'][0]
        self.assertRedirects(response,
                             reverse('posts:profile',
                                     kwargs={'username': self.user}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(last_object.text, form_data['text'])
        self.assertEqual(last_object.group.id, form_data['group'])

    def test_edit_post(self):
        """Valid form edits post in Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст поста с группой',
            'group': self.group.id,
            'author_id': self.user.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        post_context = response.context['post']
        self.assertRedirects(response,
                             reverse('posts:post_detail',
                                     kwargs={'post_id': self.post.id}))
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(post_context.text, form_data['text'])
        self.assertEqual(post_context.group.id, form_data['group'])

    def test_create_post_by_guest(self):
        """Creating a post by unauthorized client."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Post from unauthorized client',
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        create_url = reverse('posts:post_create')
        login_url = reverse('users:login')
        self.assertRedirects(response, f'{login_url}?next={create_url}')
        self.assertEqual(Post.objects.count(), posts_count)

    def test_edit_post_by_guest(self):
        """Editing a post by unauthorized client."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Edited post from unauthorized client',
        }
        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        edit_url = reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        login_url = reverse('users:login')
        self.assertRedirects(response, f'{login_url}?next={edit_url}')
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(self.post.text, self.post.text)
        self.assertNotEqual(self.post.text, form_data['text'])
