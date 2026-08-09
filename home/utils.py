import os


def get_file_type(file_field):
    ext = os.path.splitext(file_field.name)[1].lower()
    return detect_file_type(ext)


def detect_file_type(ext):
    video_formats = ['.mp4', '.avi', '.mkv', '.mov', '.webm', '.flv', '.wmv', '.m4v', '.mpg', '.mpeg']
    audio_formats = ['.mp3', '.wav', '.ogg', '.m4a', '.flac', '.aac', '.wma', '.aiff']
    image_formats = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.ico', '.tiff']
    document_formats = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.rtf', '.odt']
    archive_formats = ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2']
    code_formats = ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.php', '.rb', '.go', '.rs']

    if ext in video_formats:
        return 'video'
    elif ext in audio_formats:
        return 'audio'
    elif ext in image_formats:
        return 'image'
    elif ext == '.pdf':
        return 'pdf'
    elif ext in document_formats:
        return 'document'
    elif ext in archive_formats:
        return 'archive'
    elif ext in code_formats:
        return 'code'
    else:
        return 'other'


def get_file_extension(file_field):
    return os.path.splitext(file_field.name)[1].lower()


def format_file_size(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"
