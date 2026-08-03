# update_files_full.py
from home.models import File
import os

print("=" * 60)
print("FULL FILE UPDATE SCRIPT")
print("=" * 60)

all_files = File.objects.all()
total = all_files.count()

if total == 0:
    print("\n❌ No files found in database!")
else:
    print(f"\n📁 Found {total} files in database")
    print("🔄 Updating file types and sizes...\n")

    updated_count = 0
    errors = 0

    for i, f in enumerate(all_files, 1):
        try:
            old_type = f.file_type
            old_size = f.file_size

            # Update file type
            if f.file:
                ext = os.path.splitext(f.file.name)[1].lower()
                f.file_type = f.get_file_type(ext)

                # Update file size if file exists on disk
                if os.path.exists(f.file.path):
                    f.file_size = f.file.size
                else:
                    f.file_size = 0

                f.save()

            if old_type != f.file_type or old_size != f.file_size:
                updated_count += 1
                print(f"✅ [{i}/{total}] {f.name}")
                print(f"   Extension: {ext}")
                print(f"   Type: {old_type or 'None'} → {f.file_type}")
                print(f"   Size: {old_size} → {f.file_size} bytes\n")
            else:
                print(f"⏭️  [{i}/{total}] {f.name} (already correct)")

        except Exception as e:
            errors += 1
            print(f"❌ [{i}/{total}] Error updating {f.name}: {str(e)}\n")

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total files: {total}")
    print(f"✅ Updated: {updated_count}")
    print(f"⏭️  Already correct: {total - updated_count - errors}")
    print(f"❌ Errors: {errors}")
    print("\n🎉 File types and sizes successfully updated!\n")
print("=" * 60)
