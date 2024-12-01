from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django.shortcuts import get_object_or_404
from django.db.models import Prefetch
from .models import Thread, Reply, Like, Follow, User
from .serializers import (
    ThreadSerializer, ThreadDetailSerializer, ReplySerializer,
    LikeSerializer, FollowSerializer, UserDetailSerializer,
    UserBriefSerializer
)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'bio']
    
    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return UserDetailSerializer
        return UserBriefSerializer
    
    @action(detail=True, methods=['post'])
    def follow(self, request, pk=None):
        user_to_follow = self.get_object()
        serializer = FollowSerializer(
            data={'followed': user_to_follow.id},
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def unfollow(self, request, pk=None):
        user_to_unfollow = self.get_object()
        follow = Follow.objects.filter(
            follower=request.user,
            followed=user_to_unfollow
        ).first()
        
        if follow:
            follow.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {"detail": "Not following this user."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True)
    def followers(self, request, pk=None):
        user = self.get_object()
        followers = user.followers.all()
        serializer = UserBriefSerializer(followers, many=True)
        return Response(serializer.data)
    
    @action(detail=True)
    def following(self, request, pk=None):
        user = self.get_object()
        following = user.following.all()
        serializer = UserBriefSerializer(following, many=True)
        return Response(serializer.data)
    
    @action(detail=True)
    def threads(self, request, pk=None):
        user = self.get_object()
        threads = Thread.with_counts().filter(author=user)
        serializer = ThreadSerializer(
            threads, many=True, context={'request': request}
        )
        return Response(serializer.data)

class ThreadViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['content']
    
    def get_queryset(self):
        queryset = Thread.with_counts().select_related('author')
        queryset = queryset.prefetch_related(
            Prefetch(
                'replies',
                queryset=Reply.with_counts().order_by('-created_at')[:3],
                to_attr='recent_replies'
            )
        )
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ThreadDetailSerializer
        return ThreadSerializer
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        thread = self.get_object()
        serializer = LikeSerializer(
            data={'thread': thread.id},
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def unlike(self, request, pk=None):
        thread = self.get_object()
        like = Like.objects.filter(
            user=request.user,
            thread=thread
        ).first()
        
        if like:
            like.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {"detail": "Thread not liked."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'])
    def repost(self, request, pk=None):
        original_thread = self.get_object()
        repost = Thread.objects.create(
            author=request.user,
            is_repost=True,
            original_thread=original_thread
        )
        serializer = ThreadSerializer(repost, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class ReplyViewSet(viewsets.ModelViewSet):
    serializer_class = ReplySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        queryset = Reply.with_counts().select_related('author', 'thread')
        thread_id = self.request.query_params.get('thread', None)
        if thread_id:
            queryset = queryset.filter(thread_id=thread_id)
        return queryset
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        reply = self.get_object()
        serializer = LikeSerializer(
            data={'reply': reply.id},
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def unlike(self, request, pk=None):
        reply = self.get_object()
        like = Like.objects.filter(
            user=request.user,
            reply=reply
        ).first()
        
        if like:
            like.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {"detail": "Reply not liked."},
            status=status.HTTP_400_BAD_REQUEST
        )

class FeedViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ThreadSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Get IDs of users the current user follows
        following_ids = self.request.user.following.values_list(
            'followed_id', flat=True
        )
        # Get threads from followed users and the current user
        return Thread.with_counts().filter(
            author_id__in=list(following_ids) + [self.request.user.id]
        ).select_related('author').order_by('-created_at')