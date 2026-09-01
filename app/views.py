from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Issue, Attachment
from .forms import AttachmentForm

@login_required
def upload_attachment(request, issue_id):
    issue = get_object_or_404(Issue, pk=issue_id)
    if request.method == 'POST':
        form = AttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            attachment = form.save(commit=False)
            attachment.issue = issue
            attachment.uploaded_by = request.user
            attachment.save()
            return JsonResponse({
                'id': attachment.id,
                'file_name': attachment.file.name,
                'uploaded_at': attachment.uploaded_at.isoformat(),
                'uploaded_by': attachment.uploaded_by.username,
            })
        else:
            return JsonResponse({'error': 'Invalid form'}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def delete_attachment(request, attachment_id):
    attachment = get_object_or_404(Attachment, pk=attachment_id)
    if request.user == attachment.uploaded_by or request.user.is_superuser:
        attachment.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Permission denied'}, status=403)
