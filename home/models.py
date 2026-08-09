# home/models.py
from django.db import models
from django.contrib.auth.models import User
import os
from .utils import detect_file_type, format_file_size, get_file_extension

class File(models.Model):
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='uploads/')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    upload_date = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)
    file_type = models.CharField(max_length=50, blank=True, null=True)
    file_size = models.BigIntegerField(default=0)

    # New fields for dashboard stats
    views = models.PositiveIntegerField(default=0)
    downloads = models.PositiveIntegerField(default=0)
    shares = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        # Detect file type and size before saving
        if self.file:
            ext = os.path.splitext(self.file.name)[1].lower()
            self.file_type = detect_file_type(ext)
            try:
                self.file_size = self.file.size
            except:
                self.file_size = 0
        super().save(*args, **kwargs)
    
    def get_file_type(self, extension):
        return detect_file_type(extension)
    
    def get_file_extension(self):
        return os.path.splitext(self.file.name)[1].lower()
    
    def get_file_icon(self):
        icons = {
            'video': 'fa-file-video',
            'audio': 'fa-file-audio',
            'image': 'fa-file-image',
            'pdf': 'fa-file-pdf',
            'document': 'fa-file-word',
            'archive': 'fa-file-archive',
            'code': 'fa-file-code',
            'other': 'fa-file'
        }
        return icons.get(self.file_type, 'fa-file')
    
    def format_file_size(self):
        return format_file_size(self.file_size)

    def __str__(self):
        return self.name


class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.ForeignKey(File, on_delete=models.CASCADE)
    is_like = models.BooleanField(default=True)  # True for like, False for dislike
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'file')
    
    def __str__(self):
        action = "liked" if self.is_like else "disliked"
        return f"{self.user.username} {action} {self.file.name}"

