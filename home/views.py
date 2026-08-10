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
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.models import User
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum, Q
from django.core.paginator import Paginator
from django.contrib.auth.views import PasswordResetView

from django.utils.translation import gettext as _
from .forms import RegisterForm, UploadForm, ShareHubPasswordResetForm
from .models import File, Like
from .utils import detect_file_type


# ------------------- AUTH -------------------

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()

            current_site = get_current_site(request)
            if current_site.domain == 'example.com':
                current_site.domain = 'localhost'
            subject = _('Activate Your ShareHub Account')
            host_with_port = request.get_host()
            verify_url = f"{'https' if request.is_secure() else 'http'}://{host_with_port}/activate/{urlsafe_base64_encode(force_bytes(user.pk))}/{default_token_generator.make_token(user)}/"
            html_message = render_to_string('home/email_verification.html', {
                'user': user,
                'domain': current_site.domain,
                'host_with_port': host_with_port,
                'protocol': 'https' if request.is_secure() else 'http',
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            text_message = _("Hi {username},\n\nPlease verify your email by clicking the link below:\n{url}\n\nThis link expires in 3 days.\n\nThanks,\nShareHub Team").format(
                username=user.username,
                url=verify_url,
            )

            email = EmailMultiAlternatives(
                subject,
                text_message,
                settings.DEFAULT_FROM_EMAIL or 'noreply@sharehub.local',
                [user.email]
            )
            email.attach_alternative(html_message, "text/html")
            email.send(fail_silently=False)
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
        messages.success(request, _('Email verified! Welcome to ShareHub!'))
        return redirect('dashboard')
    else:
        messages.error(request, _('Invalid or expired link.'))
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
                messages.error(request, _('Please verify your email before logging in.'))
        else:
            try:
                user_obj = User.objects.get(username=username)
                if not user_obj.is_active:
                    messages.error(request, _('Please verify your email before logging in.'))
                else:
                    messages.error(request, _('Incorrect password. Please try again.'))
            except User.DoesNotExist:
                messages.error(request, _('No account found with that username.'))
    return render(request, 'home/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, _('You have been logged out successfully.'))
    return redirect('login')


# ------------------- DASHBOARD -------------------

@login_required
def dashboard(request):
    user_files_list = File.objects.filter(uploaded_by=request.user).order_by('-upload_date')

    search_query = request.GET.get('q', '')
    if search_query:
        user_files_list = user_files_list.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
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
        'stats': stats,
        'search_query': search_query,
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

            file_instance.file_type = detect_file_type(ext)

            file_instance.save()
            messages.success(request, _(f'File "{file_instance.name}" uploaded successfully!'))
            return redirect('dashboard')
        else:
            messages.error(request, _('Upload failed. Please check the file and form.'))
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

    search_query = request.GET.get('q', '')
    if search_query:
        files = files.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(uploaded_by__username__icontains=search_query)
        )

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
        'search_query': search_query,
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
        messages.error(request, _("You are not allowed to delete this file."))
        return redirect('dashboard')
    file.delete()
    messages.success(request, _("File deleted successfully."))
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


@login_required
def profile(request):
    user = request.user
    user_files = File.objects.filter(uploaded_by=user).order_by('-upload_date')[:6]
    total_files = File.objects.filter(uploaded_by=user).count()
    total_views = sum(f.views for f in File.objects.filter(uploaded_by=user))
    total_downloads = sum(f.downloads for f in File.objects.filter(uploaded_by=user))
    total_shares = sum(f.shares for f in File.objects.filter(uploaded_by=user))

    return render(request, 'home/profile.html', {
        'user': user,
        'user_files': user_files,
        'total_files': total_files,
        'total_views': total_views,
        'total_downloads': total_downloads,
        'total_shares': total_shares,
    })


def is_admin(user):
    return user.is_staff or user.is_superuser


@login_required
@user_passes_test(is_admin)
def user_list(request):
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'users/user_list.html', {'users': users})


@login_required
def share_file(request, file_id):
    file = get_object_or_404(File, id=file_id)
    file.shares += 1
    file.save(update_fields=['shares'])
    share_url = request.build_absolute_uri(f'/view/{file.id}/')
    return render(request, 'home/share.html', {
        'file': file,
        'share_url': share_url,
    })


class ShareHubPasswordResetView(PasswordResetView):
    form_class = ShareHubPasswordResetForm
    extra_email_context = {}


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
            messages.success(request, _(f'User {user.username} activated!'))
    else:
        latest = User.objects.filter(is_active=False).order_by('-date_joined').first()
        if latest:
            latest.is_active = True
            latest.save()
            messages.success(request, _(f'User {latest.username} activated!'))
    return redirect('dashboard')


@login_required
@user_passes_test(lambda u: u.is_staff)
@csrf_exempt
def deactivate_user(request, user_id):
    user = User.objects.filter(id=user_id).first()
    if user and not user.is_superuser:
        user.is_active = False
        user.save()
        messages.success(request, _(f'User {user.username} deactivated!'))
    return redirect('dashboard')


@login_required
@user_passes_test(lambda u: u.is_staff)
@csrf_exempt
def delete_user(request, user_id):
    user = User.objects.filter(id=user_id).first()
    if user and not user.is_superuser and user != request.user:
        username = user.username
        user.delete()
        messages.success(request, _(f'User {username} deleted!'))
    return redirect('dashboard')


@login_required
@user_passes_test(lambda u: u.is_staff)
@csrf_exempt
def make_staff(request, user_id):
    user = User.objects.filter(id=user_id).first()
    if user:
        user.is_staff = not user.is_staff
        user.save()
        status = _("granted") if user.is_staff else _("revoked")
        messages.success(request, _(f'Staff privileges {status} for {user.username}!'))
    return redirect('dashboard')
