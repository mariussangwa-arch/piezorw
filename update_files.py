# Quick script to update all existing files with correct file types
# Run this in Django shell: python manage.py shell < update_files.py

from home.models import File
import os

print("=" * 60)
print("FILE TYPE UPDATE SCRIPT")
print("=" * 60)

# Get all files
all_files = File.objects.all()
total = all_files.count()

if total == 0:
    print("\n❌ No files found in database!")
    print("Upload some files first, then run this script.\n")
else:
    print(f"\n📁 Found {total} files in database")
    print("🔄 Updating file types...\n")

    updated_count = 0
    errors = 0

    for i, file_obj in enumerate(all_files, 1):
        try:
            # Store old values
            old_type = file_obj.file_type
            old_size = file_obj.file_size

            # Save triggers automatic file type detection
            file_obj.save()

            # Get extension for display
            ext = file_obj.get_file_extension()

            # Check if anything changed
            if old_type != file_obj.file_type:
                updated_count += 1
                print(f"✅ [{i}/{total}] {file_obj.name}")
                print(f"   Extension: {ext}")
                print(f"   Type: {old_type or 'None'} → {file_obj.file_type}")
                print(f"   Size: {file_obj.format_file_size()}")
                print()
            else:
                print(f"⏭️  [{i}/{total}] {file_obj.name} (already correct: {file_obj.file_type})")

        except Exception as e:
            errors += 1
            print(f"❌ [{i}/{total}] Error updating {file_obj.name}: {str(e)}")
            print()

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total files: {total}")
    print(f"✅ Updated: {updated_count}")
    print(f"⏭️  Already correct: {total - updated_count - errors}")
    print(f"❌ Errors: {errors}")
    print()

    if updated_count > 0:
        print("🎉 File types successfully updated!")
    else:
        print("ℹ️  All files already had correct types.")

    print()
    print("Next steps:")
    print("1. Refresh your browser")
    print("2. Check the 'All Files' page")
    print("3. Verify file type badges are correct")
    print()

print("=" * 60)
