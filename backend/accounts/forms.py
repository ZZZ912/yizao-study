from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import User
from .security import normalize_email


class UserAdminCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("email", "display_name")

    def clean_email(self):
        return normalize_email(self.cleaned_data["email"])


class UserAdminChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = "__all__"

    def clean_email(self):
        return normalize_email(self.cleaned_data["email"])
