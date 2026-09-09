# accounts/forms.py
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserChangeForm # برای ویرایش کاربر
from django.contrib.auth.forms import UserCreationForm
User = get_user_model()

class UserProfileForm(UserChangeForm):
    # فیلدهای اضافی که می‌خواهیم ویرایش کنیم
    profile_picture = forms.ImageField(required=False, label="عکس پروفایل")
    bio = forms.CharField(widget=forms.Textarea, required=False, label="بیو")

    class Meta:
        model = User
        fields = (
            'first_name', # نام نمایشی
            'username',   # نام کاربری
            'email',      # ایمیل
            'profile_picture',
            'bio',
            # password رو از UserChangeForm میگیره
        )



class CustomUserCreationForm(UserCreationForm):
    profile_picture = forms.ImageField(required=False, label='تصویر پروفایل')
    bio = forms.CharField(max_length=255, required=False, label='بیوگرافی')

    class Meta:
        model = User
        # به جای full_name از فیلدهای استاندارد جنگو استفاده کنید
        fields = ('username', 'first_name', 'last_name', 'email', 'profile_picture', 'bio')

        class Meta:
            model = User  # مدل سفارشی خودتان را مشخص کنید
            # فیلدهایی که می‌خواهید در فرم نمایش داده شوند
            fields = ('username', 'full_name', 'email', 'profile_picture', 'bio') 
            # توجه: 'password' و 'password_confirm' به صورت خودکار توسط UserCreationForm مدیریت می‌شوند
            # اگر فیلدهای دیگری در مدل User دارید که باید نمایش داده شوند، اضافه کنید
            # مثال: 'date_of_birth'

    # برای اینکه بتونیم password رو هم ویرایش کنیم (اختیاری)
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.fields['password'] = forms.CharField(widget=forms.PasswordInput, required=False, label="رمز عبور جدید")

    # اگر می‌خواهید password رو هم در همین فرم ویرایش کنید، باید متد save رو override کنید
    # def save(self, commit=True):
    #     user = super().save(commit=False)
    #     if commit:
    #         user.save()
    #     return user
