from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Chat, Message
from accounts import views as accounts_views
from django.contrib.auth import views as auth_views


from django.urls import path
from . import views

urlpatterns = [

        # ... سایر URL ها مثل login, logout, register
    path('profile/<int:user_id>/', views.profile_view, name='profile_detail'), # برای نمایش پروفایل دیگران
    path('my-profile/', views.profile_detail_current, name='profile_detail_current'), # برای نمایش پروفایل خود کاربر
    path('edit-profile/', views.update_profile, name='update_profile'),

    path('<int:chat_id>/', views.chat_detail, name='chat_detail'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('register/', views.register_step1, name='register_step1'),
    path('register/verify/', views.register_step2, name='register_step2'),
    path('password/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
]