from django.urls import path
from . import views

urlpatterns = [
    path('issue/<int:issue_id>/upload/', views.upload_attachment, name='upload_attachment'),
    path('attachment/<int:attachment_id>/delete/', views.delete_attachment, name='delete_attachment'),
]
