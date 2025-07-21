from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Shop, Category, Expense, CustomUser,ExpenseItem,DailySaleSummary

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'username', 'shop', 'role', 'is_staff')
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password', 'shop', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'shop', 'role'),
        }),
    )
    search_fields = ('email', 'username')
    ordering = ('email',)

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Shop)
admin.site.register(Category)
# admin.site.register(Income)
admin.site.register(Expense)
admin.site.register(ExpenseItem)
admin.site.register(DailySaleSummary)
