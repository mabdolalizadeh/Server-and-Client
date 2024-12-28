from django.contrib import admin

from login.models import User


# Register your models here.
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    readonly_fields = ('date_joined', 'last_login', 'is_superuser', 'is_staff')
    list_display = ('username', 'last_login')

