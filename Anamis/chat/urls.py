
from django.urls import path
from . import views # فرض می‌کنیم تابع chat_list در views.py اپلیکیشن chat هست

app_name = 'chat' # این قسمت خیلی مهمه برای استفاده از 'chat:chat_list'

urlpatterns = [
    path('chats/', views.chat_list, name='chat_list'), # فرض کنید view شما chat_list_view است
    path('chat/new/', views.start_chat, name='start_chat'),
    path('chat/<int:chat_id>/', views.chat_detail, name='chat_detail'),
    path('message/delete/<int:message_id>/', views.delete_message, name='delete_message'),
    path('profile/<int:user_id>/', views.profile_detail, name='profile_detail'),
    path('profile/current/', views.profile_detail_current, name='profile_detail_current'),
    path('chat/<int:chat_id>/', views.chat_detail, name='chat_detail'),

        # URL برای نمایش جزئیات گروه
    path('groups/<int:chat_id>/', views.chat_detail_group, name='chat_group'), # همانطور که قبلا داشتید

        # URL برای شروع چت جدید
    path('chat/new/', views.start_chat, name='start_chat'),

        # URL برای پردازش ارسال پیام در گروه
        # از chat_id استفاده می‌کنیم که همان group.id است
    path('groups/<int:chat_id>/send_message/', views.process_group_message, name='send_group_message'), # نام جدید

        # URL برای حذف پیام
    path('message/delete/<int:message_id>/', views.delete_message, name='delete_message'),

        # URL های پروفایل
    path('profile/<int:user_id>/', views.profile_detail, name='profile_detail'),
    path('profile/current/', views.profile_detail_current, name='profile_detail_current'),

    #     # URL های گروه
    # path('groups/create/', views.create_group_view, name='create_group'),
    # path('groups/process_create/', views.process_group_creation_view, name='process_group_creation'),
    # path('dashboard/', views.dashboard_view, name='dashboard'),

        # URL برای لیست چت ها
    path('chats/', views.chat_list, name='chat_list'),

        # نمایش صفحه چت
    path('group/<int:chat_id>/', views.chat_detail_group, name='chat_group'),
    # ارسال پیام
    path('group/<int:chat_id>/send/', views.process_group_message, name='send_group_message'),
    # path('group/<int:group_id>/add-member/', views.add_group_member, name='add_group_member')
    

]