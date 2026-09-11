import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.db.models import Q, Prefetch
from django import forms
from django.http import JsonResponse
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import Chat, Message

# تعریف مدل کاربر از تنظیمات پروژه
User = get_user_model()

class MessageForm(forms.ModelForm):
    """فرم استاندارد برای ارسال پیام و فایل"""
    class Meta:
        model = Message
        fields = ['content', 'file']


@login_required
def chat_list(request):
    """نمایش لیست تمام گفتگوهای کاربر به همراه آخرین پیام"""
    user = request.user
    
    # بهینه‌سازی کوئری برای جلوگیری از مشکل N+1
    # ما پیام‌ها را از قبل لود می‌کنیم تا در حلقه for، کوئری جدید به دیتابیس زده نشود
    recent_messages = Message.objects.order_by('-created_at')
    
    # کد اصلاح شده در chat/views.py

    chats = Chat.objects.filter(
        Q(user1=user) | Q(user2=user)
    ).prefetch_related(
        # به جای 'message_set' از نامی که در models.py تعریف کردید استفاده کنید
        # اگر related_name='messages' است، اینجا بنویسید 'messages'
        Prefetch('messages', queryset=recent_messages, to_attr='recent_messages_list')
    ).distinct()


    chat_data = []
    for chat in chats:
        # تشخیص کاربر مقابل
        other_user = chat.user2 if chat.user1 == user else chat.user1
        
        # دریافت آخرین پیام از لیستِ لود شده در حافظه
        last_message = chat.recent_messages_list[0] if chat.recent_messages_list else None
        
        # مدیریت ایمن عکس پروفایل
        profile_pic_url = None
        if hasattr(other_user, 'profile_picture') and other_user.profile_picture:
            profile_pic_url = other_user.profile_picture.url

        chat_data.append({
            'chat': chat,
            'other_user': other_user,
            'last_message': last_message,
            'other_user_profile_pic': profile_pic_url,
        })

    # مرتب‌سازی چت‌ها بر اساس زمان آخرین پیام (از جدید به قدیم)
    chat_data.sort(
        key=lambda x: x['last_message'].created_at if x['last_message'] else datetime.datetime.min, 
        reverse=True
    )

    return render(request, 'chat/chat_list.html', {'chat_data': chat_data})


@login_required
def start_chat(request):
    """ایجاد چت جدید با یک کاربر با استفاده از نام کاربری"""
    if request.method == 'POST':
        username_to_chat = request.POST.get('username', '').strip()

        if not username_to_chat:
            messages.error(request, 'لطفاً نام کاربری را وارد کنید.')
            return redirect('chat:start_chat')

        try:
            other_user = get_object_or_404(User, username=username_to_chat)

            if other_user == request.user:
                messages.error(request, 'شما نمی‌توانید با خودتان گفتگو ایجاد کنید.')
                return redirect('chat:start_chat')

            # بررسی وجود چت قبلی بین این دو کاربر
            existing_chat = Chat.objects.filter(
                (Q(user1=request.user) & Q(user2=other_user)) |
                (Q(user1=other_user) & Q(user2=request.user))
            ).first()

            if existing_chat:
                return redirect('chat:chat_detail', chat_id=existing_chat.id)
            else:
                new_chat = Chat.objects.create(user1=request.user, user2=other_user)
                messages.success(request, f'گفتگو با {other_user.username} آغاز شد.')
                return redirect('chat:chat_detail', chat_id=new_chat.id)

        except Exception as e:
            messages.error(request, f'خطایی رخ داد: {str(e)}')
            return redirect('chat:start_chat')

    return render(request, 'chat/start_chat.html')

@login_required
def chat_detail(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)

    # بررسی دسترسی کاربر به چت
    if request.user not in [chat.user1, chat.user2]:
        return JsonResponse({"error": "unauthorized"}, status=403)

    other_user = chat.user2 if chat.user1 == request.user else chat.user1
    messages_list = chat.messages.exclude(deleted_for=request.user).order_by('created_at')
    form = MessageForm()

    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.chat = chat
            message.status = "sent"
            message.save()

            # آماده‌سازی داده‌ها برای ارسال
            file_url = message.file.url if message.file else None
            send_time = message.created_at.strftime('%H:%M')

            # --- بخش ارسال از طریق WebSocket (برای طرف مقابل) ---
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"chat_{chat.id}",
                {
                    "type": "chat_message",
                    "message_id": message.id,
                    "message": message.content,
                    "sender_id": request.user.id,
                    "file_url": file_url,  # بسیار مهم برای گیرنده
                    "time": send_time,
                    'file_name': message.file.name if message.file else None,
                }
            )

            # --- پاسخ به فرستنده (از طریق AJAX) ---
            return JsonResponse({
                'success': True,
                'message_id': message.id,
                'content': message.content,
                'file_url': file_url,
                'time': send_time,
            })

        return JsonResponse({"success": False, "errors": form.errors})

    return render(request, 'chat/chat_detail.html', {
        'chat': chat,
        'messages': messages_list,
        'other_user': other_user,
        'form': form,
    })


@login_required
def chat_detail(request, chat_id):
    """
    صفحه اصلی چت و ارسال پیام با AJAX/HTTP.

    WebSocket فقط وظیفه broadcast کردن پیام ذخیره‌شده
    را بر عهده دارد.
    """

    chat = get_object_or_404(Chat, id=chat_id)

    # =========================================================
    # بررسی دسترسی
    # =========================================================

    if request.user not in (chat.user1, chat.user2):
        return JsonResponse(
            {
                "success": False,
                "error": "unauthorized",
            },
            status=403,
        )

    other_user = (
        chat.user2
        if chat.user1 == request.user
        else chat.user1
    )

    # =========================================================
    # دریافت پیام‌ها
    # =========================================================

    messages_list = (
        chat.messages
        .exclude(
            deleted_for=request.user
        )
        .select_related(
            "sender",
            "reply_to",
        )
        .order_by("created_at")
    )

    # =========================================================
    # ارسال پیام
    # =========================================================

    if request.method == "POST":

        form = MessageForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():

            message = form.save(
                commit=False
            )

            # فرستنده
            message.sender = request.user

            # چت
            message.chat = chat

            # وضعیت اولیه
            message.status = "sent"

            # -------------------------------------------------
            # Reply
            # -------------------------------------------------

            reply_to_id = request.POST.get(
                "reply_to"
            )

            if reply_to_id:

                try:
                    reply_message = (
                        Message.objects
                        .get(
                            id=reply_to_id,
                            chat=chat,
                        )
                    )

                    message.reply_to = (
                        reply_message
                    )

                except Message.DoesNotExist:
                    message.reply_to = None

            # -------------------------------------------------
            # ذخیره پیام
            # -------------------------------------------------

            message.save()

            # -------------------------------------------------
            # اطلاعات پیام
            # -------------------------------------------------

            file_url = None
            file_name = None

            if message.file:

                try:
                    file_url = message.file.url
                except (ValueError, AttributeError):
                    file_url = None

                file_name = message.file.name

            send_time = (
                message.created_at.strftime(
                    "%H:%M"
                )
            )

            reply_to_id = (
                message.reply_to_id
                if message.reply_to_id
                else None
            )

            reply_text = ""

            if message.reply_to:
                reply_text = (
                    message.reply_to.content
                    or ""
                )

            # -------------------------------------------------
            # ارسال به WebSocket
            # -------------------------------------------------

            channel_layer = get_channel_layer()

            async_to_sync(
                channel_layer.group_send
            )(
                f"chat_{chat.id}",
                {
                    "type": "chat_message",

                    "message_id": message.id,

                    "message": (
                        message.content
                        or ""
                    ),

                    "sender_id": (
                        request.user.id
                    ),

                    "file_url": file_url,

                    "file_name": file_name,

                    "time": send_time,

                    "reply_to_id": (
                        reply_to_id
                    ),

                    "reply_text": (
                        reply_text
                    ),
                },
            )

            # -------------------------------------------------
            # پاسخ به JavaScript
            # -------------------------------------------------

            return JsonResponse(
                {
                    "success": True,

                    "message_id": message.id,

                    "content": (
                        message.content
                        or ""
                    ),

                    "file_url": file_url,

                    "file_name": file_name,

                    "time": send_time,

                    "sender_id": (
                        request.user.id
                    ),

                    "reply_to_id": (
                        reply_to_id
                    ),

                    "reply_text": (
                        reply_text
                    ),

                    "status": "sent",
                }
            )

        # -----------------------------------------------------
        # خطای فرم
        # -----------------------------------------------------

        return JsonResponse(
            {
                "success": False,
                "errors": form.errors,
            },
            status=400,
        )

    # GET
    form = MessageForm()

    return render(
        request,
        "chat/chat_detail.html",
        {
            "chat": chat,
            "messages": messages_list,
            "other_user": other_user,
            "form": form,
        },
    )


@login_required
def send_message(request, receiver_id):
    """
    ارسال پیام از مسیر receiver.
    
    این View برای سیستم قدیمی/صفحه send_message نگه داشته شده
    و با reply_to و status هماهنگ شده است.
    """

    receiver = get_object_or_404(
        User,
        id=receiver_id,
    )

    if request.method != "POST":
        form = MessageForm()

        return render(
            request,
            "chat/send_message.html",
            {
                "form": form,
                "receiver": receiver,
            },
        )

    form = MessageForm(
        request.POST,
        request.FILES,
    )

    if not form.is_valid():
        return render(
            request,
            "chat/send_message.html",
            {
                "form": form,
                "receiver": receiver,
            },
        )

    message = form.save(
        commit=False
    )

    message.sender = request.user
    message.receiver = receiver
    message.status = "sent"

    # =========================================================
    # Reply
    # =========================================================

    reply_to_id = request.POST.get(
        "reply_to"
    )

    if reply_to_id:

        try:
            reply_message = (
                Message.objects
                .get(id=reply_to_id)
            )

            # بهتر است reply هم به یکی از طرفین همین مکالمه
            # مربوط باشد.
            if (
                reply_message.sender_id
                in (
                    request.user.id,
                    receiver.id,
                )
            ):
                message.reply_to = (
                    reply_message
                )

        except Message.DoesNotExist:
            pass

    # =========================================================
    # ذخیره
    # =========================================================

    message.save()

    # =========================================================
    # WebSocket
    # =========================================================

    file_url = None
    file_name = None

    if message.file:

        try:
            file_url = message.file.url
        except (ValueError, AttributeError):
            file_url = None

        file_name = message.file.name

    reply_to_id = (
        message.reply_to_id
        if message.reply_to_id
        else None
    )

    reply_text = ""

    if message.reply_to:
        reply_text = (
            message.reply_to.content
            or ""
        )

    # ---------------------------------------------------------
    # پیدا کردن Chat
    # ---------------------------------------------------------

    chat = (
        Chat.objects
        .filter(
            user1__in=[
                request.user,
                receiver,
            ],
            user2__in=[
                request.user,
                receiver,
            ],
        )
        .first()
    )

    if chat:

        channel_layer = get_channel_layer()

        async_to_sync(
            channel_layer.group_send
        )(
            f"chat_{chat.id}",
            {
                "type": "chat_message",

                "message_id": message.id,

                "message": (
                    message.content
                    or ""
                ),

                "sender_id": (
                    request.user.id
                ),

                "file_url": file_url,

                "file_name": file_name,

                "time": (
                    message.created_at
                    .strftime("%H:%M")
                ),

                "reply_to_id": (
                    reply_to_id
                ),

                "reply_text": (
                    reply_text
                ),
            },
        )

    # =========================================================
    # پاسخ
    # =========================================================

    messages.success(
        request,
        "پیام با موفقیت ارسال شد.",
    )

    return redirect(
        "chat:inbox",
        receiver_id=receiver_id,
    )


@login_required
def delete_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)

    chat_id = message.chat.id

    # حذف کامل پیام از دیتابیس
    message.delete()

    return redirect(
        'chat:chat_detail',
        chat_id=chat_id
    )

@login_required
def delete_for_me(request, message_id):

    message = get_object_or_404(Message, id=message_id)

    message.deleted_for.add(request.user)

    return JsonResponse({
        "success": True
    })





@login_required
def profile_detail(request, user_id):
    """نمایش پروفایل یک کاربر"""
    target_user = get_object_or_404(User, id=user_id)
    return render(request, 'chat/profile_detail.html', {'user': target_user})


@login_required
def profile_detail_current(request):
    """نمایش پروفایل کاربر جاری"""
    return render(request, 'chat/profile_detail.html', {'user': request.user})


@login_required
def create_group_view(request):
    """نمایش فرم ساخت گروه"""
    return render(request, 'chat/create_group.html')


@login_required
def process_group_creation_view(request):
    """پردازش ساخت گروه جدید"""
    if request.method == 'POST':
        group_name = request.POST.get('group_name')
        if group_name:
            new_group = Group.objects.create(name=group_name, owner=request.user)
            new_group.members.add(request.user)
            messages.success(request, f'گروه "{group_name}" با موفقیت ساخته شد.')
            return redirect('chat:chat_detail', chat_id=new_group.id)
        else:
            messages.error(request, 'نام گروه نمی‌تواند خالی باشد.')
            
    return redirect('chat:create_group')
    # ویوی جدید برای پردازش پیام

@login_required
def chat_detail_group(request, chat_id):
    group = get_object_or_404(Group, id=chat_id, members=request.user)
    chat_instance, created = Chat.objects.get_or_create(group=group)
    # دریافت پیام‌ها و مرتب‌سازی
    messages = chat_instance.messages.all().order_by('created_at')
    
    return render(request, 'chat/group_chat_detail.html', {
        'group': group,
        'chat_messages': messages,
    })

@login_required
def process_group_message(request, chat_id):
    if request.method == "POST":
        group = get_object_or_404(Group, id=chat_id, members=request.user)
        content = request.POST.get('content', '').strip()
        
        if content:
            chat_instance, _ = Chat.objects.get_or_create(group=group)
            Message.objects.create(
                chat=chat_instance,
                sender=request.user,
                content=content
            )
            
    return redirect('chat:chat_group', chat_id=chat_id)
