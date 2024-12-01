from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.db.models import Count

class User(AbstractUser):
    """
    Extended User model with additional fields for Threads-like functionality
    """
    bio = models.TextField(max_length=150, blank=True)
    # profile_picture = models.ImageField(upload_to='profile_pics/', blank=True)
    verified = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    
    @property
    def followers_count(self):
        return self.followers.count()
    
    @property
    def following_count(self):
        return self.following.count()
    
    class Meta:
        db_table = 'users'

class Thread(models.Model):
    """
    Main Thread model for posts
    """
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='threads')
    content = models.TextField(max_length=500)
    # image = models.ImageField(upload_to='thread_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_repost = models.BooleanField(default=False)
    original_thread = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='reposts'
    )
    
    @property
    def likes_count(self):
        return self.likes.count()
    
    @property
    def replies_count(self):
        return self.replies.count()
    
    @property
    def reposts_count(self):
        return self.reposts.count()
    
    # For efficient querying with counts
    @classmethod
    def with_counts(cls):
        return cls.objects.annotate(
            likes_count=Count('likes'),
            replies_count=Count('replies'),
            reposts_count=Count('reposts')
        )
    
    class Meta:
        db_table = 'threads'
        ordering = ['-created_at']  

class Reply(models.Model):
    """
    Model for replies to threads
    """
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='replies')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='replies')
    content = models.TextField(max_length=500)
    # image = models.ImageField(upload_to='reply_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def likes_count(self):
        return self.likes.count()
    
    # For efficient querying with counts
    @classmethod
    def with_counts(cls):
        return cls.objects.annotate(
            likes_count=Count('likes')
        )
    
    class Meta:
        db_table = 'replies'
        ordering = ['created_at']

class Like(models.Model):
    """
    Model for likes on threads and replies
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='likes', null=True)
    reply = models.ForeignKey(Reply, on_delete=models.CASCADE, related_name='likes', null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'likes'
        unique_together = [
            ('user', 'thread'),
            ('user', 'reply'),
        ]

class Follow(models.Model):
    """
    Model for user follows
    """
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    followed = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'follows'
        unique_together = ['follower', 'followed']