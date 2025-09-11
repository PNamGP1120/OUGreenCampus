from django.db.models import Count
from django.db.models.functions import TruncMonth, TruncDate
from rest_framework import viewsets, permissions, parsers, status
from rest_framework.decorators import action, api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from sendgrid import SendGridAPIClient, Mail

from OUGreenApp import serializers
from OUGreenApp.ai_utils import predict_waste
from OUGreenApp.models import (
    User, Category, News, ProjectContest, Proposal,
    Document, AIUsageLog, Feedback, Comment, Like, NewsletterSubscriber
)
from OUGreenApp.perms import IsAdmin, IsEditorOrAdmin, IsOwnerOrAdminOrReadOnly
from OUGreenApp.serializers import (
    UserSerializer, CategorySerializer, NewsSerializer, ProjectContestSerializer,
    ProposalSerializer, DocumentSerializer, AIUsageLogSerializer,
    FeedbackSerializer, CommentSerializer, LikeSerializer, WasteClassifySerializer, NewsletterSubscriberSerializer
)
from backend import settings


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.filter(is_active=True)
    parser_classes = [parsers.JSONParser, parsers.MultiPartParser, parsers.FormParser]

    @action(methods=['get'], detail=False, url_path='me', permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        return Response(serializers.UserSerializer(self.request.user).data)

    def get_permissions(self):
        if self.action in ['list', 'destroy']:
            return [IsAdmin()]
        elif self.action in ['update', 'partial_update']:
            return [IsOwnerOrAdminOrReadOnly()]
        return [permissions.AllowAny()]


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [IsEditorOrAdmin()]


class NewsViewSet(viewsets.ModelViewSet):
    queryset = News.objects.all()
    serializer_class = NewsSerializer
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [IsEditorOrAdmin()]


class ProjectContestViewSet(viewsets.ModelViewSet):
    queryset = ProjectContest.objects.all()
    serializer_class = ProjectContestSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [IsAdmin()]


class ProposalViewSet(viewsets.ModelViewSet):
    queryset = Proposal.objects.all()
    serializer_class = ProposalSerializer

    def get_permissions(self):
        if self.action in ['create']:
            return [permissions.IsAuthenticated()]
        return [IsOwnerOrAdminOrReadOnly()]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [IsEditorOrAdmin()]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    http_method_names = ['get', 'post', 'delete']

    def get_permissions(self):
        if self.action in ['list', 'destroy']:
            return [IsAdmin()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            serializer.save(user=None)


class AIUsageLogViewSet(viewsets.ModelViewSet):
    queryset = AIUsageLog.objects.all()
    serializer_class = AIUsageLogSerializer
    http_method_names = ['get', 'post']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            serializer.save(user=None)


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all().order_by("-created_at")
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrAdminOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class LikeViewSet(viewsets.ModelViewSet):
    queryset = Like.objects.all().order_by("-created_at")
    serializer_class = LikeSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdminOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@api_view(['GET'])
@permission_classes([IsAdmin])
def dashboard_stats(request):
    data = {
        # 1. User
        "users": {
            "total": User.objects.aggregate(total=Count("id")),
            "by_role": list(User.objects.values("role").annotate(total=Count("id"))),
            "by_month": list(
                User.objects.annotate(month=TruncMonth("date_joined"))
                .values("month")
                .annotate(total=Count("id"))
                .order_by("month")
            ),
        },

        # 2. News
        "news": {
            "total": News.objects.aggregate(total=Count("id")),
            "by_month": list(
                News.objects.annotate(month=TruncMonth("created_at"))
                .values("month")
                .annotate(total=Count("id"))
                .order_by("month")
            ),
        },

        # 3. Documents
        "documents": {
            "total": Document.objects.aggregate(total=Count("id")),
            "by_month": list(
                Document.objects.annotate(month=TruncMonth("created_at"))
                .values("month")
                .annotate(total=Count("id"))
                .order_by("month")
            ),
        },

        # 4. Projects / Contests
        "projects": {
            "total": ProjectContest.objects.aggregate(total=Count("id")),
            "by_status": list(
                ProjectContest.objects.values("status").annotate(total=Count("id"))
            ),
            "by_month": list(
                ProjectContest.objects.annotate(month=TruncMonth("created_at"))
                .values("month")
                .annotate(total=Count("id"))
                .order_by("month")
            ),
        },

        # 5. Comments
        "comments": {
            "total": Comment.objects.aggregate(total=Count("id")),
            "by_day": list(
                Comment.objects.annotate(day=TruncDate("created_at"))
                .values("day")
                .annotate(total=Count("id"))
                .order_by("day")
            ),
        },

        # 6. Likes
        "likes": {
            "total": Like.objects.aggregate(total=Count("id")),
            "by_day": list(
                Like.objects.annotate(day=TruncDate("created_at"))
                .values("day")
                .annotate(total=Count("id"))
                .order_by("day")
            ),
        },

        # 7. AI usage logs
        "ai_usage": {
            "total": AIUsageLog.objects.aggregate(total=Count("id")),
            "by_type": list(
                AIUsageLog.objects.values("type").annotate(total=Count("id"))
            ),
            "by_month": list(
                AIUsageLog.objects.annotate(month=TruncMonth("created_at"))
                .values("month", "type")
                .annotate(total=Count("id"))
                .order_by("month")
            ),
        },
    }

    return Response(data)


SUGGESTIONS = {
    "cardboard": "Thùng carton có thể tái chế.",
    "glass": "Chai, lọ thủy tinh nên rửa sạch và tái chế.",
    "metal": "Lon kim loại có thể bán ve chai hoặc tái chế.",
    "paper": "Giấy nên phân loại riêng và tái chế.",
    "plastic": "Nhựa có thể tái chế, hạn chế vứt bừa bãi.",
    "trash": "Rác khác, cần xử lý theo hướng dẫn địa phương."
}

@api_view(["POST"])
@permission_classes([permissions.AllowAny])  # cho phép cả khách
@parser_classes([MultiPartParser, FormParser])
def classify_waste(request):
    serializer = WasteClassifySerializer(data=request.data)
    if serializer.is_valid():
        img = serializer.validated_data["image"]

        # Dự đoán bằng AI
        label, confidence = predict_waste(img)

        result = {
            "label": label,
            "confidence": round(confidence, 2),
            "suggestion": SUGGESTIONS.get(label, "Hãy xử lý rác theo hướng dẫn.")
        }

        # Lưu log
        log = AIUsageLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            type="waste_classifier",
            input_data={"filename": img.name},
            output_data=result
        )
        result["log_id"] = log.id

        return Response(result, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NewsletterViewSet(viewsets.ModelViewSet):
    queryset = NewsletterSubscriber.objects.all()
    serializer_class = NewsletterSubscriberSerializer

    def get_permissions(self):
        if self.action in ["create"]:   # ai cũng có thể đăng ký
            return [permissions.AllowAny()]
        elif self.action in ["list", "destroy"]:  # chỉ admin xem và xóa
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]  # mặc định cho các action khác

    @action(methods=["post"], detail=False, url_path="send",
            permission_classes=[permissions.IsAdminUser])  # chỉ admin mới được gửi mail
    def send_newsletter(self, request):
        subject = request.data.get("subject", "OU Green Campus Newsletter")
        message = request.data.get("message", "")
        emails = NewsletterSubscriber.objects.values_list("email", flat=True)

        if not emails:
            return Response({"error": "No subscribers found"}, status=400)

        try:
            sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
            for email in emails:
                mail = Mail(
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to_emails=email,
                    subject=subject,
                    plain_text_content=message,
                )
                sg.send(mail)

            return Response({"status": "Emails sent", "total": len(emails)})
        except Exception as e:
            return Response({"error": str(e)}, status=500)
