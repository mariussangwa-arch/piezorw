from home.models import File
import os

for f in File.objects.all():
    if f.file and os.path.exists(f.file.path):
        f.file_size = f.file.size  # read size from actual file
        f.save()
        print(f"Updated: {f.name} → {f.file_size} bytes")
    else:
        print(f"File not found on disk: {f.name}")
