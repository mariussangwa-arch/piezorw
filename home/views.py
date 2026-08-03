# home/views.py
import os

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.models import User
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum
from django.core.paginator import Paginator

from .forms import RegisterForm, UploadForm
from .models import File, Like


# ------------------- AUTH -------------------

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()

            current_site = get_current_site(request)
            subject = 'Activate Your ShareHub Account'
            message = render_to_string('home/email_verification.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL or 'noreply@sharehub.local',
                [user.email],
                fail_silently=False
            )
            return render(request, 'home/activation_sent.html')
    else:
        form = RegisterForm()
    return render(request, 'home/register.html', {'form': form})


def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        messages.success(request, 'Email verified! Welcome to ShareHub!')
        return redirect('dashboard')
    else:
        messages.error(request, 'Invalid or expired link.')
        return redirect('login')


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'Please verify your email first.')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'home/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


# ------------------- DASHBOARD -------------------

@login_required
def dashboard(request):
    user_files_list = File.objects.filter(uploaded_by=request.user).order_by('-upload_date')
    
    for f in user_files_list:
        f.likes_count = Like.objects.filter(file=f, is_like=True).count()
        f.dislikes_count = Like.objects.filter(file=f, is_like=False).count()
        f.user_liked = Like.objects.filter(file=f, user=request.user, is_like=True).exists()
        f.user_disliked = Like.objects.filter(file=f, user=request.user, is_like=False).exists()
    
    paginator = Paginator(user_files_list, 9)
    page_number = request.GET.get('page')
    user_files = paginator.get_page(page_number)

    stats = {
        'total_files': user_files_list.count(),
        'total_views': user_files_list.aggregate(Sum('views'))['views__sum'] or 0,
        'total_downloads': user_files_list.aggregate(Sum('downloads'))['downloads__sum'] or 0,
        'total_shares': user_files_list.aggregate(Sum('shares'))['shares__sum'] or 0
    }

    all_users = None
    inactive_users = None
    if request.user.is_staff:
        all_users = User.objects.all().order_by('-date_joined')
        inactive_users = User.objects.filter(is_active=False).order_by('-date_joined')

    return render(request, 'home/dashboard.html', {
        'files': user_files,
        'all_users': all_users,
        'inactive_users': inactive_users,
        'stats': stats
    })


# ------------------- UPLOAD FILE -------------------

@login_required
def upload_file(request):
    if request.method == 'POST':
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            file_instance = form.save(commit=False)
            file_instance.uploaded_by = request.user

            uploaded_file = request.FILES['file']
            filename = uploaded_file.name
            ext = os.path.splitext(filename)[1].lower()

            # Robust file type detection — extension first (most reliable)
            if ext in {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg', '.tiff'}:
                file_instance.file_type = 'image'
            elif ext in {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv', '.wmv', '.mpg', '.mpeg'}:
                file_instance.file_type = 'video'
            elif ext in {'.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a', '.wma'}:
                file_instance.file_type = 'audio'
            elif ext == '.pdf':
                file_instance.file_type = 'pdf'
            elif ext in {'.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'}:
                file_instance.file_type = 'archive'
            elif ext in {'.doc', '.docx', '.odt', '.rtf', '.pages'}:
                file_instance.file_type = 'document'
            elif ext in {'.py', '.js', '.html', '.css', '.json', '.xml', '.java', '.cpp', '.c', '.php', '.rb', '.go', '.ts', '.tsx', '.sql', '.sh', '.yaml', '.yml', '.md'}:
                file_instance.file_type = 'code'
            elif ext in {'.txt', '.log', '.csv'}:
                file_instance.file_type = 'document'
            else:
                # Fallback to MIME type
                ct = uploaded_file.content_type
                if ct.startswith('image/'):
                    file_instance.file_type = 'image'
                elif ct.startswith('video/'):
                    file_instance.file_type = 'video'
                elif ct.startswith('audio/'):
                    file_instance.file_type = 'audio'
                elif ct == 'application/pdf':
                    file_instance.file_type = 'pdf'
                else:
                    file_instance.file_type = 'document'

            file_instance.save()
            messages.success(request, f'File "{file_instance.name}" uploaded successfully!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Upload failed. Please check the file and form.')
    else:
        form = UploadForm()

    return render(request, 'home/upload.html', {'form': form})


# ------------------- ALL FILES -------------------

@login_required
def all_files(request):
    files = File.objects.all().order_by('-upload_date')

    file_type = request.GET.get('type', 'all')
    if file_type != 'all':
        files = files.filter(file_type=file_type)

    for f in files:
        f.likes_count = Like.objects.filter(file=f, is_like=True).count()
        f.dislikes_count = Like.objects.filter(file=f, is_like=False).count()
        f.user_liked = Like.objects.filter(file=f, user=request.user, is_like=True).exists()
        f.user_disliked = Like.objects.filter(file=f, user=request.user, is_like=False).exists()
        f.format_file_size = f.format_file_size()

    sort = request.GET.get('sort', 'newest')
    if sort == 'oldest':
        files = files.order_by('upload_date')
    elif sort == 'likes':
        files = sorted(files, key=lambda f: f.likes_count, reverse=True)

    paginator = Paginator(files, 12)
    page_number = request.GET.get('page')
    page_files = paginator.get_page(page_number)

    return render(request, 'home/all_files.html', {
        'files': page_files,
        'current_sort': sort,
        'current_type': file_type,
    })


# ------------------- REMAINING VIEWS (unchanged but cleaned) -------------------

@login_required
def view_file(request, file_id):
    file = get_object_or_404(File, id=file_id)
    if request.user != file.uploaded_by:
        file.views += 1
        file.save(update_fields=['views'])

    file.likes_count = Like.objects.filter(file=file, is_like=True).count()
    file.dislikes_count = Like.objects.filter(file=file, is_like=False).count()
    file.user_liked = Like.objects.filter(file=file, user=request.user, is_like=True).exists()
    file.user_disliked = Like.objects.filter(file=file, user=request.user, is_like=False).exists()

    code_content = None
    if file.file_type == 'code':
        try:
            file.file.seek(0)
            raw = file.file.read()
            code_content = raw.decode('utf-8', errors='replace')
        except:
            code_content = "# Error reading file content"

    return render(request, 'home/view_file.html', {
        'file': file,
        'file_type': file.file_type,
        'code_content': code_content,
    })


@login_required
def download_file(request, file_id):
    file = get_object_or_404(File, id=file_id)
    response = HttpResponse(file.file, content_type='application/force-download')
    response['Content-Disposition'] = f'attachment; filename="{file.name}{file.get_file_extension()}"'
    file.downloads += 1
    file.save(update_fields=['downloads'])
    return response


@login_required
def delete_file(request, file_id):
    file = get_object_or_404(File, id=file_id)
    if file.uploaded_by != request.user and not request.user.is_staff:
        messages.error(request, "You are not allowed to delete this file.")
        return redirect('dashboard')
    file.delete()
    messages.success(request, "File deleted successfully.")
    return redirect('dashboard')


@login_required
def like_file(request, file_id):
    file = get_object_or_404(File, id=file_id)
    like, created = Like.objects.get_or_create(user=request.user, file=file)
    if not created and like.is_like:
        like.delete()
    else:
        like.is_like = True
        like.save()
    Like.objects.filter(user=request.user, file=file, is_like=False).delete()
    return redirect(request.META.get('HTTP_REFERER', 'all_files'))


@login_required
def dislike_file(request, file_id):
    file = get_object_or_404(File, id=file_id)
    like, created = Like.objects.get_or_create(user=request.user, file=file)
    if not created and not like.is_like:
        like.delete()
    else:
        like.is_like = False
        like.save()
    Like.objects.filter(user=request.user, file=file, is_like=True).delete()
    return redirect(request.META.get('HTTP_REFERER', 'all_files'))


@login_required
def unlike_file(request, file_id):
    Like.objects.filter(user=request.user, file_id=file_id).delete()
    return redirect(request.META.get('HTTP_REFERER', 'all_files'))


# ------------------- ADMIN ONLY -------------------

@login_required
@user_passes_test(lambda u: u.is_staff)
@csrf_exempt
def instant_activate(request, user_id=None):
    if user_id:
        user = User.objects.filter(id=user_id, is_active=False).first()
        if user:
            user.is_active = True
            user.save()
            messages.success(request, f'User {user.username} activated!')
    else:
        latest = User.objects.filter(is_active=False).order_by('-date_joined').first()
        if latest:
            latest.is_active = True
            latest.save()
            messages.success(request, f'User {latest.username} activated!')
    return redirect('dashboard')


@login_required
@user_passes_test(lambda u: u.is_staff)
@csrf_exempt
def deactivate_user(request, user_id):
    user = User.objects.filter(id=user_id).first()
    if user and not user.is_superuser:
        user.is_active = False
        user.save()
        messages.success(request, f'User {user.username} deactivated!')
    return redirect('dashboard')


@login_required
@user_passes_test(lambda u: u.is_staff)
@csrf_exempt
def delete_user(request, user_id):
    user = User.objects.filter(id=user_id).first()
    if user and not user.is_superuser and user != request.user:
        username = user.username
        user.delete()
        messages.success(request, f'User {username} deleted!')
    return redirect('dashboard')


@login_required
@user_passes_test(lambda u: u.is_staff)
@csrf_exempt
def make_staff(request, user_id):
    user = User.objects.filter(id=user_id).first()
    if user:
        user.is_staff = not user.is_staff
        user.save()
        status = "granted" if user.is_staff else "revoked"
        messages.success(request, f'Staff privileges {status} for {user.username}!')
    return redirect('dashboard')


def is_admin(user):
    return user.is_staff or user.is_superuser


@login_required
@user_passes_test(is_admin)
def user_list(request):
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'users/user_list.html', {'users': users})
