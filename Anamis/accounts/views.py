# accounts/views.py
from chat.models import Chat,Message, ChatMember
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.utils import timezone
from .forms import UserProfileForm
from django.db.models import OuterRef, Subquery, Max
import random
from django.contrib import messages 
from django.contrib.auth import login, authenticate
from django.core.mail import send_mail
from django.conf import settings


User = get_user_model()

# @login_required # اگر نیاز به لاگین دارد
def chat_detail(request, chat_id): # فرض می‌کنیم chat_id را دریافت می‌کند
    try:
        chat = Chat.objects.get(id=chat_id)
        # می توانید پیام ها یا اطلاعات دیگر چت را هم اینجا بارگذاری کنید
        # messages = chat.messages.all()
        context = {'chat': chat}
        return render(request, 'accounts/chat_detail.html', context) # یا template مناسب
    except Chat.DoesNotExist:
        # اگر چت پیدا نشد، صفحه خطا یا لیست چت ها را نشان دهید
        return render(request, 'accounts/chat_list.html', {'error': 'Chat not found'})


@login_required
def profile_view(request, user_id):
    # این ویو برای نمایش پروفایل کاربر خاص (مثلا در صفحه چت)
    try:
        profile_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        # اگر کاربر پیدا نشد، می‌تونی به صفحه خطا یا لیست چت‌ها برگردونی
        return redirect('chat_list') # فرض می‌کنیم همچین URL ای داریم

    context = {
        'profile_user': profile_user
    }
    return render(request, 'accounts/profile_detail.html', context) # این تمپلیت رو باید بسازیم

@login_required
def update_profile(request):
    user = request.user
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            # آپدیت last_seen هنگام ذخیره فرم
            user.last_seen = timezone.now()
            user.save(update_fields=['last_seen'])
            return redirect('profile_detail_current') # یک URL برای نمایش پروفایل کاربر جاری
    else:
        form = UserProfileForm(instance=user)

    context = {
        'form': form
    }
    return render(request, 'accounts/update_profile.html', context) # این تمپلیت رو باید بسازیم

@login_required
def profile_detail_current(request):
    # این ویو برای نمایش پروفایل کاربر لاگین شده (مثلا در صفحه پروفایل خود کاربر)
    user = request.user
    # آپدیت last_seen در هر بازدید از پروفایل خود کاربر
    user.last_seen = timezone.now()
    user.online_status = True # فرض می‌کنیم اگر صفحه پروفایل رو باز کرده آنلاینه
    user.save(update_fields=['last_seen', 'online_status'])

    context = {
        'profile_user': user
    }
    return render(request, 'accounts/profile_detail.html', context) 

def register_step1(request):
    if request.method == 'POST':
        email = request.POST.get('email')

        if not email:
            messages.error(request, 'لطفاً ایمیل خود را وارد کنید.')
            return redirect('register_step1')

        otp_code = random.randint(100000, 999999)

        try:
            send_mail(
                'کد تایید ثبت نام',
                f'کد تایید شما: {otp_code}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )

            # فقط اگر ایمیل با موفقیت ارسال شد، کد را در session ذخیره کن
            request.session['otp_email'] = email
            request.session['otp_code'] = str(otp_code)

            messages.success(
                request,
                'کد تایید به ایمیل شما ارسال شد.'
            )

            return redirect('register_step2')

        except Exception as e:
            print('EMAIL ERROR:', e)
            messages.error(
                request,
                'ارسال ایمیل انجام نشد. لطفاً دوباره تلاش کنید.'
            )

    return render(request, 'accounts/register_step1.html')

def register_step2(request):
    if request.method == 'POST':
        entered_code = request.POST.get('code')
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        email = request.session.get('otp_email')
        stored_code = request.session.get('otp_code')

        # بررسی وجود کد و ایمیل در سشن
        if not email or not stored_code:
            messages.error(request, 'کد تأیید منقضی شده است. دوباره ثبت‌نام کنید.')
            return redirect('register_step1')

        # بررسی کد تأیید
        if entered_code != stored_code:
            messages.error(request, 'کد تأیید اشتباه است.')
            return render(request, 'accounts/register_step2.html')

        # اعتبارسنجی نام کاربری
        if not username:
            messages.error(request, 'نام کاربری را وارد کنید.')
            return render(request, 'accounts/register_step2.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'این نام کاربری قبلاً انتخاب شده است.')
            return render(request, 'accounts/register_step2.html')

        # بررسی تکراری نبودن ایمیل
        if User.objects.filter(email=email).exists():
            messages.error(request, 'این ایمیل قبلاً ثبت شده است.')
            return render(request, 'accounts/register_step2.html')

        # اعتبارسنجی رمز عبور
        if not password:
            messages.error(request, 'رمز عبور را وارد کنید.')
            return render(request, 'accounts/register_step2.html')

        if password != confirm_password:
            messages.error(request, 'رمز عبور و تکرار آن یکسان نیستند.')
            return render(request, 'accounts/register_step2.html')

        # ساخت کاربر
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        # پاک کردن اطلاعات تأیید از سشن
        request.session.pop('otp_email', None)
        request.session.pop('otp_code', None)

        # ورود خودکار
        login(request, user)

        messages.success(request, 'ثبت‌نام با موفقیت انجام شد.')
        return redirect('chat:chat_list')

    return render(request, 'accounts/register_step2.html')
