from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Role, User


_INPUT_CLASS = "input-warp"


class RegisterForm(UserCreationForm):
    role = forms.ChoiceField(
        choices=Role.choices,
        initial=Role.STUDENT,
        widget=forms.RadioSelect(attrs={"class": "role-radio"}),
    )

    class Meta:
        model = User
        fields = ("username", "email", "role", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == "role":
                continue
            field.widget.attrs.setdefault("class", _INPUT_CLASS)
            field.widget.attrs.setdefault("placeholder", field.label)


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", _INPUT_CLASS)
            field.widget.attrs.setdefault("placeholder", field.label)
