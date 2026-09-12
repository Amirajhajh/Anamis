
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse

from chat.models import Chat


def chat_list(request):
    chats = Chat.objects.filter(
        Q(user1=request.user) | Q(user2=request.user)
    )
    return render(request, "core/chat_list.html", {"chats": chats})


def login_view(request):
    error_message = None

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect(reverse("chat:chat_list"))

        error_message = "Invalid username or password."

    return render(request, "core/login.html", {"error_message": error_message})


@login_required
def index(request):
    return render(request, "core/index.html")


def home(request):
    return render(request, "core/Anamis.html")
