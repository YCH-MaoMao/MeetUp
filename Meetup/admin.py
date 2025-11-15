from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Activity, Address, Rating, Comment, UserPreference, Message, Category, IssueReport, JoinRequest, Conversation

# Custom UserAdmin
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ("username", "email", "status", "is_staff", "is_active")  # Columns in the admin panel
    list_filter = ("is_staff", "is_active", "status")
    search_fields = ("username", "email")
    ordering = ("date_created",)

# Register models
admin.site.register(User, CustomUserAdmin)  # Register User with CustomUserAdmin
admin.site.register(Activity)
admin.site.register(Address)
admin.site.register(Rating)
admin.site.register(Comment)
admin.site.register(UserPreference)
admin.site.register(Message)
admin.site.register(Category)
admin.site.register(IssueReport)
admin.site.register(JoinRequest)
admin.site.register(Conversation)