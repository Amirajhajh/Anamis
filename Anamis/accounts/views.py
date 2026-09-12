
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
import random

from django.conf import settings
from .forms import UserProfileForm
from chat.models import Chat

User = get_user_model()


def chat_detail(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)
    return render(request, "accounts/chat_detail.html", {"chat": chat})


@login_required
def profile_view(request, user_id):
    profile_user = get_object_or_404(User, id=user_id)
    return render(
        request,
        "accounts/profile_detail.html",
        {"profile_user": profile_user},
    )


@login_required
def update_profile(request):
    user = request.user

    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES, instance=user)

        if form.is_valid():
            form.save()
            user.last_seen = timezone.now()
            user.save(update_fields=["last_seen"])
            return redirect("profile_detail_current")
    else:
        form = UserProfileForm(instance=user)

    return render(request, "accounts/update_profile.html", {"form": form})


@login_required
def profile_detail_current(request):
    user = request.user
    user.last_seen = timezone.now()
    user.online_status = True
    user.save(update_fields=["last_seen", "online_status"])

    return render(
        request,
        "accounts/profile_detail.html",
        {"profile_user": user},
    )


def register_step1(request):
    if request.method == "POST":
        email = request.POST.get("email")

        if not email:
            messages.error(request, "Please enter your email.")
            return redirect("register_step1")

        if User.objects.filter(email=email).exists():
            messages.error(request, "This email is already registered.")
            return redirect("register_step1")

        otp_code = str(random.randint(100000, 999999))

        try:
            send_mail(
                "Registration Verification Code",
                f"Your verification code is: {otp_code}",
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )

            request.session["otp_email"] = email
            request.session["otp_code"] = otp_code
            request.session.modified = True

            return redirect("register_step2")

        except Exception:
            messages.error(
                request,
                "Failed to send the verification email. Please try again.",
            )
            return redirect("register_step1")

    return render(request, "accounts/register_step1.html")


def register_step2(request):
    if request.method == "POST":
        entered_code = request.POST.get("code")
        username = request.POST.get("username")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        email = request.session.get("otp_email")
        stored_code = request.session.get("otp_code")

        if not email or not stored_code:
            messages.error(
                request,
                "The verification code has expired. Please register again.",
            )
            return redirect("register_step1")

        if entered_code != stored_code:
            messages.error(request, "Invalid verification code.")
            return render(request, "accounts/register_step2.html")

        if not username:
            messages.error(request, "Please enter a username.")
            return render(request, "accounts/register_step2.html")

        if User.objects.filter(username=username).exists():
            messages.error(request, "This username is already taken.")
            return render(request, "accounts/register_step2.html")

        if User.objects.filter(email=email).exists():
            messages.error(request, "This email is already registered.")
            return render(request, "accounts/register_step2.html")

        if not password:
            messages.error(request, "Please enter a password.")
            return render(request, "accounts/register_step2.html")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, "accounts/register_step2.html")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
        )

        request.session.pop("otp_email", None)
        request.session.pop("otp_code", None)

        login(request, user)

        messages.success(request, "Registration completed successfully.")
        return redirect("chat:chat_list")

    return render(request, "accounts/register_step2.html")


def register_direct_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if not username:
            messages.error(request, "Please enter a username.")
            return render(request, "accounts/register_account.html")

        if User.objects.filter(username=username).exists():
            messages.error(request, "This username is already taken.")
            return render(request, "accounts/register_account.html")

        if not password:
            messages.error(request, "Please enter a password.")
            return render(request, "accounts/register_account.html")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, "accounts/register_account.html")

        user = User.objects.create_user(
            username=username,
            password=password,
        )

        login(request, user)

        messages.success(request, "Registration completed successfully.")
        return redirect("chat:chat_list")

    return render(request, "accounts/register_account.html")
