
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

User = get_user_model()


class UserProfileForm(UserChangeForm):
    profile_picture = forms.ImageField(
        required=False,
        label="Profile Picture",
    )
    bio = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.Textarea,
        label="Bio",
    )

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "username",
            "email",
            "profile_picture",
            "bio",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop("password", None)


class CustomUserCreationForm(UserCreationForm):
    profile_picture = forms.ImageField(
        required=False,
        label="Profile Picture",
    )
    bio = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.Textarea,
        label="Bio",
    )

    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "profile_picture",
            "bio",
        )
