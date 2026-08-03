# home/views.py  ←  REPLACE YOUR ENTIRE FILE WITH THIS EXACT CODE

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
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
from django.views.decorators.csrf import csrf_exempt   # ← THIS FIXES THE 403 ERROR
from urllib.parse import quote  # ← NEW IMPORT (replaces urlquote)

from .forms import RegisterForm, UploadForm
from .models import File, Like


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
    return redirect('login')


@login_required
def dashboard(request):
    user_files = File.objects.filter(uploaded_by=request.user)
    return render(request, 'home/dashboard.html', {'files': user_files})


@login_required
def upload_file(request):
    if request.method == 'POST':
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.save(commit=False)
            file.uploaded_by = request.user
            file.save()
            return redirect('dashboard')
    else:
        form = UploadForm()
    return render(request, 'home/upload.html', {'form': form})


@login_required
def all_files(request):
    files = File.objects.all()
    for file in files:
        file.likes = Like.objects.filter(file=file, is_like=True).count()
        file.dislikes = Like.objects.filter(file=file, is_like=False).count()
        file.user_liked = Like.objects.filter(file=file, user=request.user, is_like=True).exists()
        file.user_disliked = Like.objects.filter(file=file, user=request.user, is_like=False).exists()
    return render(request, 'home/all_files.html', {'files': files})


@login_required
def download_file(request, file_id):
    file = get_object_or_404(File, id=file_id)
    response = HttpResponse(file.file, content_type='application/force-download')
    response['Content-Disposition'] = f'attachment; filename={file.name}'
    return response


@login_required
def view_file(request, file_id):
    file_obj = get_object_or_404(File, id=file_id)
    
    if not file_obj.file.name.lower().endswith('.pdf'):
        messages.error(request, "Only PDF files can be viewed online.")
        return redirect('all_files')
    
    # URL-encode the file path (works with spaces/special chars)
    safe_pdf_url = request.build_absolute_uri(quote(file_obj.file.url))
    
    return render(request, 'home/view_pdf.html', {
        'pdf_url': safe_pdf_url
    })

@login_required
def like_file(request, file_id):
    file = get_object_or_404(File, id=file_id)
    like, created = Like.objects.get_or_create(user=request.user, file=file)
    like.is_like = True
    like.save()
    Like.objects.filter(user=request.user, file=file, is_like=False).delete()
    return redirect('all_files')


@login_required
def dislike_file(request, file_id):
    file = get_object_or_404(File, id=file_id)
    like, created = Like.objects.get_or_create(user=request.user, file=file)
    like.is_like = False
    like.save()
    Like.objects.filter(user=request.user, file=file, is_like=True).delete()
    return redirect('all_files')


@login_required
def unlike_file(request, file_id):
    Like.objects.filter(user=request.user, file_id=file_id).delete()
    return redirect('all_files')


# ADMIN ONLY: ONE-CLICK USER ACTIVATION (NO MORE 403 ERROR!)
@login_required
@csrf_exempt
def instant_activate(request):
    if not request.user.is_staff:
        messages.error(request, "Only admins can use this.")
        return redirect('dashboard')
    
    latest_user = User.objects.filter(is_active=False).order_by('-date_joined').first()
    if latest_user:
        latest_user.is_active = True
        latest_user.save()
        messages.success(request, f"{latest_user.username} activated instantly!")
    else:
        messages.info(request, "No users waiting for activation.")
    
    return redirect('dashboard')
