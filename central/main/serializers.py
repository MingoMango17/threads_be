from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Thread, Reply, Like, Follow

User = get_user_model()

class UserBriefSerializer(serializers.ModelSerializer):
    """
    Simplified User serializer for nested representations
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'verified']


class UserDetailSerializer(serializers.ModelSerializer):
    """
    Detailed User serializer for profile views
    """
    followers_count = serializers.IntegerField(read_only=True)
    following_count = serializers.IntegerField(read_only=True)
    is_following = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'bio',
            'verified', 'date_joined', 'followers_count',
            'following_count', 'is_following'
        ]
        extra_kwargs = {
            'email': {'write_only': True},
            'date_joined': {'read_only': True}
        }
    
    def get_is_following(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Follow.objects.filter(
                follower=request.user,
                followed=obj
            ).exists()
        return False


class ReplySerializer(serializers.ModelSerializer):
    """
    Serializer for replies
    """
    author = UserBriefSerializer(read_only=True)
    likes_count = serializers.IntegerField(read_only=True)
    is_liked = serializers.SerializerMethodField()
    
    class Meta:
        model = Reply
        fields = [
            'id', 'author', 'thread', 'content',
            'created_at', 'updated_at', 'likes_count', 'is_liked'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Like.objects.filter(
                user=request.user,
                reply=obj
            ).exists()
        return False
    
    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


class ThreadSerializer(serializers.ModelSerializer):
    """
    Serializer for threads with basic reply information
    """
    author = UserBriefSerializer(read_only=True)
    likes_count = serializers.IntegerField(read_only=True)
    replies_count = serializers.IntegerField(read_only=True)
    reposts_count = serializers.IntegerField(read_only=True)
    is_liked = serializers.SerializerMethodField()
    is_reposted = serializers.SerializerMethodField()
    recent_replies = ReplySerializer(many=True, read_only=True, source='replies')
    
    class Meta:
        model = Thread
        fields = [
            'id', 'author', 'content', 'created_at',
            'updated_at', 'likes_count', 'replies_count',
            'reposts_count', 'is_liked', 'is_reposted',
            'is_repost', 'original_thread', 'recent_replies'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Like.objects.filter(
                user=request.user,
                thread=obj
            ).exists()
        return False
    
    def get_is_reposted(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Thread.objects.filter(
                author=request.user,
                is_repost=True,
                original_thread=obj
            ).exists()
        return False
    
    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


class ThreadDetailSerializer(ThreadSerializer):
    """
    Detailed thread serializer with all replies
    """
    replies = ReplySerializer(many=True, read_only=True)
    
    class Meta(ThreadSerializer.Meta):
        fields = ThreadSerializer.Meta.fields + ['replies']


class LikeSerializer(serializers.ModelSerializer):
    """
    Serializer for likes
    """
    user = UserBriefSerializer(read_only=True)
    
    class Meta:
        model = Like
        fields = ['id', 'user', 'thread', 'reply', 'created_at']
        read_only_fields = ['created_at']
    
    def validate(self, data):
        if not data.get('thread') and not data.get('reply'):
            raise serializers.ValidationError(
                "Either thread or reply must be provided"
            )
        if data.get('thread') and data.get('reply'):
            raise serializers.ValidationError(
                "Cannot like both thread and reply simultaneously"
            )
        return data
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class FollowSerializer(serializers.ModelSerializer):
    """
    Serializer for follows
    """
    follower = UserBriefSerializer(read_only=True)
    followed = UserBriefSerializer(read_only=True)
    
    class Meta:
        model = Follow
        fields = ['id', 'follower', 'followed', 'created_at']
        read_only_fields = ['created_at']
    
    def validate(self, data):
        followed_id = self.context['request'].data.get('followed')
        if not followed_id:
            raise serializers.ValidationError("Followed user ID is required")
            
        try:
            followed = User.objects.get(id=followed_id)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")
            
        if followed == self.context['request'].user:
            raise serializers.ValidationError("Cannot follow yourself")
            
        data['followed'] = followed
        return data
    
    def create(self, validated_data):
        validated_data['follower'] = self.context['request'].user
        return super().create(validated_data)