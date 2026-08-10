# home/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from .models import File

class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('you@example.com'),
            'autocomplete': 'off',
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Choose a username'),
            'autocomplete': 'off',
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Create a strong password'),
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Repeat your password'),
        })

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class ShareHubPasswordResetForm(PasswordResetForm):
    def save(self, use_https=False, token_generator=None, from_email=None, email_template_name='home/password_reset_email.html', request=None, domain_override=None, extra_email_context=None, **kwargs):
        from django.contrib.sites.shortcuts import get_current_site
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes

        email = self.cleaned_data['email']
        users = User.objects.filter(email=email, is_active=True)
        for user in users:
            protocol = 'https' if use_https or (request and request.is_secure()) else 'http'
            domain = domain_override or get_current_site(request).domain
            if domain == 'example.com':
                domain = 'localhost'
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = token_generator.make_token(user)

            context = {
                'email': email,
                'domain': domain,
                'site_name': domain,
                'uid': uid,
                'user': user,
                'token': token,
                'protocol': protocol,
                'host_with_port': request.get_host() if request else domain,
                **(extra_email_context or {}),
            }

            subject = render_to_string('home/password_reset_subject.txt', context)
            subject = ''.join(subject.splitlines())
            html_body = render_to_string(email_template_name, context)
            text_body = render_to_string('home/password_reset_email.txt', context)

            email_message = EmailMultiAlternatives(subject, text_body, from_email, [email])
            email_message.attach_alternative(html_body, 'text/html')
            email_message.send(fail_silently=False)


class UploadForm(forms.ModelForm):
    class Meta:
        model = File
        fields = ['name', 'file', 'description']
