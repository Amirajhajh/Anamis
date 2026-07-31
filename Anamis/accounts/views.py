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

        # اگر از کلاس ها استفاده می کنید:
        # from django.views.generic import DetailView
        # class ChatDetailView(DetailView):
        #     model = Chat
        #     template_name = 'accounts/chat_detail.html'
        #     context_object_name = 'chat'
        #
        #     def get_object(self, queryset=None):
        #         # اینجا logic لازم برای پیدا کردن آبجکت چت را پیاده سازی کنید
        #         # مثلا بر اساس user یا chat_id
        #         return get_object_or_404(Chat, id=self.kwargs.get('chat_id'))

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
    return render(request, 'accounts/profile_detail.html', context) # می‌تونیم از همون تمپلیت profile_detail استفاده کنیم

# def register_step1(request):
#     if request.method == 'POST':
#         phone = request.POST.get('phone')
#         if len(phone) == 11 and phone.startswith('09'):
#             otp_code = random.randint(100000, 999999)
            
#             request.session['otp_phone'] = phone
#             request.session['otp_code'] = str(otp_code)
            
#             print(f"کد تأیید برای {phone}: {otp_code}")
            
#             messages.success(request, 'کد تأیید ارسال شد.')

#             print(otp_code)
            
#             # 👈 این خط رو اصلاح کن:
#             return redirect('register_step2') 
            
#         else:
#             return redirect('register_step2') 
    
#     return render(request, 'accounts/register_step1.html')
def register_step1(request):
    if request.method == 'POST':
        phone = request.POST.get('phone')
        
        # ابتدا بررسی کنید که phone مقدار None یا خالی نباشد
        if phone: # این شرط بررسی می کند که phone وجود داشته باشد و خالی نباشد
            if len(phone) == 11 and phone.startswith('09'):
                otp_code = random.randint(100000, 999999)
                
                request.session['otp_phone'] = phone
                request.session['otp_code'] = str(otp_code)
                
                print(f"کد تأیید برای {phone}: {otp_code}")
                
                messages.success(request, 'کد تأیید ارسال شد.')
                
                # در اینجا می توانید واقعا کد OTP را ارسال کنید (مثلا با یک سرویس پیامکی)
                print(otp_code) # این خط برای دیباگ است و می توانید حذف کنید
                
                return redirect('register_step2') 
            else:
                # اگر فرمت شماره تلفن اشتباه بود
                messages.error(request, 'شماره تلفن باید ۱۱ رقم باشد و با ۰۹ شروع شود.')
        else:
            # اگر فیلد شماره تلفن خالی بود
            messages.error(request, 'لطفاً شماره تلفن خود را وارد کنید.')
        
        # اگر خطا رخ داد یا فرمت اشتباه بود، کاربر را به همان صفحه برگردانید
        # تا خطاها را ببیند و مجددا تلاش کند.
        return redirect('register_step1') # به جای register_step2، به همان صفحه اول برگردانید تا خطا نمایش داده شود

    # اگر متد GET بود، صفحه ثبت نام را نمایش بده
    return render(request, 'accounts/register_step1.html')

def register_step2(request):
    if request.method == 'POST':
        # دریافت داده‌ها از فرم
        entered_code = request.POST.get('code')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        email = request.POST.get('email')
        
        # دریافت شماره و کد از سشن با استفاده از pop (برای جلوگیری از ارور)
        phone = request.session.pop('otp_phone', None)
        stored_code = request.session.pop('otp_code', None)
        
        # بررسی صحت کد
        if phone and stored_code and entered_code == stored_code:
            # بررسی تطابق پسورد و ایمیل
            if not password:
                messages.error(request, 'لطفاً رمز عبور را وارد کنید.')
                return render(request, 'accounts/register_step2.html')
            
            if password != confirm_password:
                messages.error(request, 'رمز عبور و تکرار آن مطابقت ندارند.')
                return render(request, 'accounts/register_step2.html')
            
            if not email:
                messages.error(request, 'لطفاً ایمیل خود را وارد کنید.')
                return render(request, 'accounts/register_step2.html')
            
            # ساخت کاربر با اطلاعاتی که کاربر وارد کرده
            user = User.objects.create_user(
                username=phone,
                password=password,  # 👈 پسوردی که کاربر وارد کرده
                email=email
            )
            
            # لاگین کردن کاربر
            login(request, user)
            
            messages.success(request, 'ثبت‌نام با موفقیت انجام شد! خوش آمدید. 🎉')
            
            # هدایت به صفحه چت
            return redirect('chat:chat_list')
        else:
            messages.error(request, 'کد تأیید اشتباه است یا منقضی شده.')
            return render(request, 'accounts/register_step2.html')
    
    return render(request, 'accounts/register_step2.html')

# def register_step2(request):
#     """مرحله دوم: وارد کردن کد تأیید و ثبت نام"""
#     if request.method == 'POST':
#         entered_code = request.POST.get('code')
#         phone = request.session.get('otp_phone')
#         stored_code = request.session.get('otp_code')
        
#         if phone and stored_code and entered_code == stored_code:
#             # کد درست بود، حالا کاربر رو بساز
#             if not User.objects.filter(username=phone).exists():
#                 user = User.objects.create_user(
#                     username=phone,
#                     password=str(random.randint(100000, 999999)), # رمز عبور تصادفی
#                     # phone=phone # اگر فیلد phone داری
#                 )
#                 login(request, user)
#                 # پاک کردن سشن‌ها
#                 phone = request.session.pop('otp_phone', None)
#                 stored_code = request.session.pop('otp_code', None)
#                 messages.success(request, 'ثبت‌نام با موفقیت انجام شد.')
#                 return redirect('chat:chat_list') # یا هر صفحه‌ای که می‌خوای
#             else:
#                 messages.error(request, 'این شماره قبلاً ثبت شده است.')
#                 return redirect('register_step1')
#         else:
#             messages.error(request, 'کد وارد شده اشتباه است.')
#             return render(request, 'accounts/register_step2.html')
            

#     return render(request, 'accounts/register_step2.html')