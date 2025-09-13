from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenBlacklistView

from OUGreenApp.views import UserViewSet, CategoryViewSet, NewsViewSet, ProjectContestViewSet, DocumentViewSet, \
    ProposalViewSet, FeedbackViewSet, AIUsageLogViewSet, CommentViewSet, LikeViewSet, dashboard_stats, classify_waste, \
    NewsletterViewSet, TagViewSet, ChatSessionViewSet, chat_history, send_message, create_chat_session

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'news', NewsViewSet, basename='news')
router.register(r'project-contests', ProjectContestViewSet, basename='project-contest')
router.register(r'proposals', ProposalViewSet, basename='proposal')
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'feedbacks', FeedbackViewSet, basename='feedback')
router.register(r'ai-logs', AIUsageLogViewSet, basename='ai-log')
router.register(r'comments', CommentViewSet, basename='comment')
router.register(r'likes', LikeViewSet, basename='like')
router.register(r"newsletter", NewsletterViewSet, basename="newsletter")
router.register(r"chat-sessions", ChatSessionViewSet, basename="chat-session")

urlpatterns = [
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/logout/', TokenBlacklistView.as_view(), name='token_blacklist'),
    path('dashboard/stats/', dashboard_stats, name='dashboard-stats'),
    path("ai/classify/", classify_waste, name="classify_waste"),
    path("chat/session/", create_chat_session, name="create_chat_session"),
    path("chat/send/", send_message, name="send_message"),
    path("chat/history/<int:session_id>/", chat_history, name="chat_history"),
    path('', include(router.urls)),
]
