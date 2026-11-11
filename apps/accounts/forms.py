import secrets
import string
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit

User = get_user_model()


class CustomLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout('username', 'password', Submit('submit', 'Login', css_class='btn btn-primary w-100'))


class AdminCreateGuestForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email', 'real_name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['real_name'].required = True
        self.fields['real_name'].label = 'Guest Full Name'
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'email',
            'real_name',
            Submit('submit', 'Create Guest & Send Credentials', css_class='btn btn-primary w-100')
        )

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if not email:
            raise forms.ValidationError('Email is required.')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('A user with this email already exists.')
        return email

    def save(self, commit=True, created_by=None):
        user = super().save(commit=False)
        email = self.cleaned_data['email']
        base = email.split('@')[0].replace('.', '_').replace('-', '_')[:20] or 'guest'
        username = base
        i = 1
        while User.objects.filter(username__iexact=username).exists():
            i += 1
            username = f"{base}{i}"
        user.username = username
        user.email = email
        user.role = 'BUYER'
        user.email_verified = True
        user.must_change_password = True
        user.is_active = True
        if created_by:
            user.created_by = created_by
        alphabet = string.ascii_letters + string.digits
        temp_password = ''.join(secrets.choice(alphabet) for _ in range(10)) + 'A1!'
        user.set_password(temp_password)
        if commit:
            user.save()
        user._temp_password = temp_password
        return user


class ForcePasswordChangeForm(forms.Form):
    new_password1 = forms.CharField(label='New password', min_length=8, widget=forms.PasswordInput(attrs={'class': 'form-control form-control-lg', 'minlength': '8'}))
    new_password2 = forms.CharField(label='Confirm new password', min_length=8, widget=forms.PasswordInput(attrs={'class': 'form-control form-control-lg', 'minlength': '8'}))

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('new_password1')
        p2 = cleaned.get('new_password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('New passwords do not match.')
        return cleaned
