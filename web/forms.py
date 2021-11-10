from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import Order


class OrderForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['order_date'].label = 'Date of receipt of the order'
    order_date = forms.DateField(widget=forms.TextInput(attrs={'type': 'date'}))

    class Meta:
        model = Order
        fields = (
            'first_name', 'second_name', 'phone_number', 'address', 'buying_type', 'order_date',
        )

# Login form
class LoginForm(forms.ModelForm):

    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'password']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Username'
        self.fields['password'].label = 'Password'

    def clean(self):
        username = self.cleaned_data['username']
        password = self.cleaned_data['password']
        if not User.objects.filter(username=username).exists():
            raise forms.ValidationError(f"User with login {username} does not exist!")
        user = User.objects.filter(username=username).first()
        if user:
            if not user.check_password(password):
                raise forms.ValidationError('Wrong password!')
        return self.cleaned_data


# Registration form
class RegistrationForm(forms.ModelForm):

    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    phone_number = forms.CharField(required=False)
    email = forms.EmailField(required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Username'
        self.fields['password'].label = 'Password'
        self.fields['confirm_password'].label = 'Confirm password'
        self.fields['phone_number'].label = 'Phone number'
        self.fields['first_name'].label = 'First name'
        self.fields['last_name'].label = 'Last name'
        self.fields['email'].label = 'Email'

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(f'Name {username} is already taken!')
        return username

    def clean(self):
        password = self.cleaned_data['password']
        confirm_password = self.cleaned_data['confirm_password']
        if confirm_password != password:
            raise forms.ValidationError("Passwords don't match!")

    class Meta:
        model = User
        fields = ['username', 'password', 'confirm_password', 'first_name', 'last_name', 'phone_number', 'email']
