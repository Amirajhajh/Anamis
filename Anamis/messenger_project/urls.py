from django.contrib import admin
from django.urls import path, include
from accounts import views as accounts_views
from django.contrib.auth import views as auth_views
from chat import views
from django.conf import settings
from django.conf.urls.static import static

# urlpatterns = [
#     path('admin/', admin.site.urls),
#     path('accounts/', include('accounts.urls')), # برای ورود/خروج
#     path('', include('core.urls')),
#     path('chat/', include('chat.urls')), # برای URLهای مربوط به چت
# ]

from django.contrib import admin
from django.urls import path, include
urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('chat/', include(('chat.urls', 'chat'), namespace='chat_list')),
    path('core/', include('core.urls')),
    path(
        '',
        auth_views.LoginView.as_view(template_name='core/login.html'),
        name='login'),
    path('profile/<int:user_id>/', views.profile_detail, name='profile_detail'),
    
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)