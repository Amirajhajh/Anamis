from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login # برای احراز هویت
from django.urls import reverse # برای ساخت URL



def chat_list(request):
    chats = Chat.objects.filter(
        Q(user1=request.user) | Q(user2=request.user)
    )

def login_view(request):
    error_message = None # برای نمایش پیام خطا در صورت ناموفق بودن ورود
    if request.method == 'POST':
        form_username = request.POST.get('username')
        form_password = request.POST.get('password')

        # سعی در احراز هویت کاربر
        user = authenticate(request, username=form_username, password=form_password)

        if user is not None:
            login(request, user)
            # فرض می‌کنیم URL pattern برای صفحه چت 'chat:chat_list' نام دارد
            return redirect(reverse('chat:chat_list')) # این خط درست است
        else:
            error_message = "نام کاربری یا رمز عبور اشتباه است."

    # اگر متد GET بود یا ورود ناموفق بود، صفحه ورود را نمایش بده
    context = {'error_message': error_message}
    return render(request, 'core/login.html', context)

        # if user is not None:
        #     # اگر احراز هویت موفق بود، کاربر را وارد سیستم کن
        #     login(request, user)
        #     # کاربر را به صفحه چت هدایت کن
        #     # فرض می‌کنیم URL pattern برای صفحه چت 'chat:chat_list' نام دارد
        #     # اگر نام دیگری دارد، آن را جایگزین کن
        #     return redirect(reverse('chat:chat_list')) # یا هر URL pattern دیگری که برای صفحه چت اصلی داری
        # else:
        #     error_message = "نام کاربری یا رمز عبور اشتباه است."

    # اگر متد GET بود یا ورود ناموفق بود، صفحه ورود را نمایش بده
    context = {'error_message': error_message}
    return render(request, 'core/login.html', context)


@login_required
def index(request):
    # این صفحه باید لیست چت‌ها رو نمایش بده
    # برای شروع، یک صفحه ساده که فقط خوش‌آمد بگه
    return render(request, 'core/index.html')

# def login_view(request):
#     return render(request, 'core/login.html') 


