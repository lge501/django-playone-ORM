from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .forms import PlayerChangeForm, PlayerCreationForm
from .models import Player


@admin.register(Player)
class PlayerAdmin(UserAdmin):
    # The forms to add and change user instances
    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference the removed 'username' field
    fieldsets = (
        (None, {'fields': ('password',)}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'gender', 'date_of_birth', 'mobile_number')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'gender', 'date_of_birth')}
         ),
    )
    form = PlayerChangeForm
    add_form = PlayerCreationForm
    list_display = ('email', 'first_name', 'last_name', 'mobile_number', 'is_staff')
    list_filter = ('is_staff',)
    filter_horizontal = ()
    search_fields = ('email', 'first_name', 'last_name', 'mobile_number')
    ordering = ['email',]
