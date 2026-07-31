
from django.urls import path
from . import views
app_name = 'core'
urlpatterns = [
path('', views.index, name='index'), # صفحه اصلی
path('login/', views.login_view, name='login'),
 # صفحه ورود
# ... سایر URL ها ...
    ]