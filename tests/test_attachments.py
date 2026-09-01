from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from app.models import Issue, Project, Attachment

class AttachmentTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.project = Project.objects.create(name='Test Project')
        self.issue = Issue.objects.create(project=self.project, title='Test Issue')
        self.client.login(username='testuser', password='testpass')

    def test_upload_attachment(self):
        file = SimpleUploadedFile('test.txt', b'file content')
        response = self.client.post(f'/issue/{self.issue.id}/upload/', {'file': file})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('id', data)
        self.assertEqual(data['file_name'], 'attachments/test.txt')

    def test_upload_attachment_unauthenticated(self):
        self.client.logout()
        file = SimpleUploadedFile('test.txt', b'file content')
        response = self.client.post(f'/issue/{self.issue.id}/upload/', {'file': file})
        self.assertRedirects(response, '/accounts/login/?next=/issue/1/upload/')

    def test_delete_attachment(self):
        file = SimpleUploadedFile('test.txt', b'file content')
        attachment = Attachment.objects.create(issue=self.issue, file=file, uploaded_by=self.user)
        response = self.client.post(f'/attachment/{attachment.id}/delete/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Attachment.objects.count(), 0)

    def test_delete_attachment_permission_denied(self):
        other_user = User.objects.create_user(username='other', password='pass')
        file = SimpleUploadedFile('test.txt', b'file content')
        attachment = Attachment.objects.create(issue=self.issue, file=file, uploaded_by=other_user)
        response = self.client.post(f'/attachment/{attachment.id}/delete/')
        self.assertEqual(response.status_code, 403)

    def test_delete_attachment_unauthenticated(self):
        self.client.logout()
        file = SimpleUploadedFile('test.txt', b'file content')
        attachment = Attachment.objects.create(issue=self.issue, file=file, uploaded_by=self.user)
        response = self.client.post(f'/attachment/{attachment.id}/delete/')
        self.assertRedirects(response, f'/accounts/login/?next=/attachment/{attachment.id}/delete/')
