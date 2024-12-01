# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Thread, Reply, Like, Follow

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_filter = ('verified', 'date_joined', 'is_staff')
    search_fields = ('username', 'email')
    ordering = ('-date_joined',)
    

@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'content_preview', 'created_at', 'likes_count', 'replies_count')
    list_filter = ('created_at', 'is_repost')
    search_fields = ('content', 'author__username')
    raw_id_fields = ('author', 'original_thread')
    date_hierarchy = 'created_at'
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'

@admin.register(Reply)
class ReplyAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'thread', 'content_preview', 'created_at', 'likes_count')
    list_filter = ('created_at',)
    search_fields = ('content', 'author__username')
    raw_id_fields = ('author', 'thread')
    date_hierarchy = 'created_at'
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'get_content_type', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username',)
    raw_id_fields = ('user', 'thread', 'reply')
    date_hierarchy = 'created_at'
    
    def get_content_type(self, obj):
        return 'Thread' if obj.thread else 'Reply'
    get_content_type.short_description = 'Type'

@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('id', 'follower', 'followed', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('follower__username', 'followed__username')
    raw_id_fields = ('follower', 'followed')
    date_hierarchy = 'created_at'

# # Optional: Customize admin site header and title
# admin.site.site_header = 'Threads Admin'
# admin.site.site_title = 'Threads Admin Portal'
# admin.site.index_title = 'Welcome to Threads Admin Portal'