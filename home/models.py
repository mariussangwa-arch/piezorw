# home/models.py
from django.db import models
from django.contrib.auth.models import User
import os

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
            file_extension = os.path.splitext(self.file.name)[1].lower()
            self.file_type = self.get_file_type(file_extension)
            try:
                self.file_size = self.file.size
            except:
                self.file_size = 0
        super().save(*args, **kwargs)
    
    def get_file_type(self, extension):
        """Determine file type based on extension"""
        ext = extension.replace('.', '').lower()
        video_formats = ['mp4', 'avi', 'mkv', 'mov', 'webm', 'flv', 'wmv', 'm4v', 'mpg', 'mpeg']
        audio_formats = ['mp3', 'wav', 'ogg', 'm4a', 'flac', 'aac', 'wma', 'aiff']
        image_formats = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp', 'ico', 'tiff']
        document_formats = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'rtf', 'odt']
        archive_formats = ['zip', 'rar', '7z', 'tar', 'gz', 'bz2']
        code_formats = ['py', 'js', 'html', 'css', 'java', 'cpp', 'c', 'php', 'rb', 'go', 'rs']

        if ext in video_formats:
            return 'video'
        elif ext in audio_formats:
            return 'audio'
        elif ext in image_formats:
            return 'image'
        elif ext == 'pdf':
            return 'pdf'
        elif ext in document_formats:
            return 'document'
        elif ext in archive_formats:
            return 'archive'
        elif ext in code_formats:
            return 'code'
        else:
            return 'other'
    
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
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

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

