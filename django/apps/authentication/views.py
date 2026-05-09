from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from .forms import LoginForm, RegisterForm


def _post_login_redirect(user):
    if getattr(user, "is_teacher", False):
        return redirect("classrooms:list")
    return redirect("classrooms:list")


class AppLoginView(LoginView):
    template_name = "auth/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy("classrooms:list")


class AppLogoutView(LogoutView):
    next_page = reverse_lazy("auth:login")


def register(request):
    if request.user.is_authenticated:
        return _post_login_redirect(request.user)
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return _post_login_redirect(user)
    else:
        form = RegisterForm()
    return render(request, "auth/register.html", {"form": form})
