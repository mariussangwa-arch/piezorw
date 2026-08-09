from django.urls import path
from django.shortcuts import redirect
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from .views import (
    register, login_view, logout_view, dashboard, profile, upload_file,
    all_files, download_file, view_file, like_file, dislike_file,
    unlike_file, activate, instant_activate, delete_file, share_file, user_list,
    ShareHubPasswordResetView
)

def root_redirect(request):
    return redirect('dashboard') if request.user.is_authenticated else redirect('login')

urlpatterns = [
    path('', root_redirect),

    path('register/', register, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),

    path('activate/<uidb64>/<token>/', activate, name='activate'),
    path('activate-latest/', instant_activate, name='activate_latest'),
    path('activate-latest/<int:user_id>/', instant_activate, name='activate_user'),

    path('dashboard/', dashboard, name='dashboard'),
    path('profile/', profile, name='profile'),
    path('upload/', upload_file, name='upload'),
    path('all_files/', all_files, name='all_files'),
    path('view/<int:file_id>/', view_file, name='view_file'),
    path('download/<int:file_id>/', download_file, name='download_file'),
    path('delete-file/<int:file_id>/', delete_file, name='delete_file'),
    path('like/<int:file_id>/', like_file, name='like_file'),
    path('dislike/<int:file_id>/', dislike_file, name='dislike_file'),
    path('unlike/<int:file_id>/', unlike_file, name='unlike_file'),
    path('share/<int:file_id>/', share_file, name='share_file'),
    path('users/', user_list, name='user_list'),
    path('password_reset/', ShareHubPasswordResetView.as_view(
        template_name='home/password_reset.html',
        email_template_name='home/password_reset_email.html',
        subject_template_name='home/password_reset_subject.txt'
    ), name='password_reset'),
    path('password_reset/done/', PasswordResetDoneView.as_view(
        template_name='home/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(
        template_name='home/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('reset/done/', PasswordResetCompleteView.as_view(
        template_name='home/password_reset_complete.html'
    ), name='password_reset_complete'),
]
