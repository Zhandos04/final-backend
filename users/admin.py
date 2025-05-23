from django.contrib import admin
from .models import Profile

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'currency')
    list_filter = ('currency',)
    search_fields = ('user__username',)

admin.site.register(Profile, ProfileAdmin)