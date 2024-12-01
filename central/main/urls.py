# urls.py
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'threads', views.ThreadViewSet, basename='thread')
router.register(r'replies', views.ReplyViewSet, basename='reply')
router.register(r'feed', views.FeedViewSet, basename='feed')