from django.contrib import admin
from django.urls import path, include
from chat import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # حساب کاربری
    path('accounts/', include('accounts.urls')),

    # بخش چت
    path('chat/', include(('chat.urls', 'chat'), namespace='chat')),

    # صفحه اصلی
    path('', include('core.urls')),

    # پروفایل
    path('profile/<int:user_id>/', views.profile_detail, name='profile_detail'),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )