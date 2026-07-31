# accounts/forms.py
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserChangeForm # برای ویرایش کاربر

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
