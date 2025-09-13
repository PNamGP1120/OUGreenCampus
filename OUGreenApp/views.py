from django.db.models import Count
from django.db.models.functions import TruncMonth, TruncDate
from rest_framework import filters
from rest_framework import viewsets, permissions, parsers, status
from rest_framework.decorators import action, api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from sendgrid import SendGridAPIClient, Mail
from transformers import pipeline

from OUGreenApp import serializers
from OUGreenApp.ai_utils import predict_waste
from OUGreenApp.models import (
    User, Category, News, ProjectContest, Proposal,
    Document, AIUsageLog, Feedback, Comment, Like, NewsletterSubscriber, Tag, ChatSession, ChatMessage
)
from OUGreenApp.perms import IsAdmin, IsEditorOrAdmin, IsOwnerOrAdminOrReadOnly
from OUGreenApp.rag_utils import search_news
from OUGreenApp.serializers import (
    UserSerializer, CategorySerializer, NewsSerializer, ProjectContestSerializer,
    ProposalSerializer, DocumentSerializer, AIUsageLogSerializer,
    FeedbackSerializer, CommentSerializer, LikeSerializer, WasteClassifySerializer, NewsletterSubscriberSerializer,
    TagSerializer, ChatMessageSerializer, ChatSessionSerializer
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

class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [IsEditorOrAdmin()]


class NewsViewSet(viewsets.ModelViewSet):
    queryset = News.objects.all().order_by("-created_at")
    serializer_class = NewsSerializer
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    filterset_fields = ["category", "tags"]
    search_fields = ["title"]
    ordering_fields = ["created_at", "title"]


    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        if not user.is_authenticated or user.role == "user":
            qs = qs.filter(status="published")
        return qs

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [IsEditorOrAdmin()]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, status="draft")


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

    filterset_fields = ["category", "tags"]
    search_fields = ["title"]
    ordering_fields = ["created_at", "title"]

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
    "cardboard": (
        "Thùng carton và các loại bìa cứng có thể tái chế. "
        "Bạn nên gấp gọn, tránh để ướt, và cho vào thùng rác tái chế. "
        "Nếu còn sạch sẽ, có thể tận dụng để đóng gói hoặc làm đồ thủ công."
    ),
    "glass": (
        "Chai, lọ thủy tinh có thể tái chế nhiều lần mà không làm giảm chất lượng. "
        "Hãy rửa sạch trước khi bỏ đi, phân loại riêng để đưa đến điểm thu gom. "
        "Tránh làm vỡ để đảm bảo an toàn."
    ),
    "metal": (
        "Lon nhôm, sắt và các vật dụng kim loại có thể được tái chế. "
        "Bạn nên dồn riêng chúng lại và bán cho ve chai hoặc đưa tới cơ sở tái chế. "
        "Nếu dính thực phẩm, hãy rửa sạch để tránh ô nhiễm và mùi hôi."
    ),
    "paper": (
        "Giấy báo, vở cũ, hộp giấy đều có thể tái chế. "
        "Hãy phân loại riêng, giữ khô ráo và không lẫn với thực phẩm hoặc chất bẩn. "
        "Bạn cũng có thể tái sử dụng giấy cho việc ghi chú hoặc gói hàng."
    ),
    "plastic": (
        "Nhựa là loại rác có thể tái chế, nhưng cần hạn chế sử dụng và thải bỏ. "
        "Hãy rửa sạch chai, lọ, hộp nhựa trước khi phân loại. "
        "Ưu tiên tái sử dụng nhiều lần và hạn chế nhựa dùng một lần để bảo vệ môi trường."
    ),
    "trash": (
        "Đây là loại rác thải còn lại (hữu cơ lẫn vô cơ khó phân loại). "
        "Bạn cần xử lý theo hướng dẫn của địa phương, ví dụ: bỏ vào thùng rác sinh hoạt. "
        "Nên giảm thiểu lượng rác này bằng cách ưu tiên tái chế, tái sử dụng, và phân loại đúng từ đầu."
    ),
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


class ChatSessionViewSet(viewsets.ModelViewSet):
    queryset = ChatSession.objects.all().order_by("-created_at")
    serializer_class = ChatSessionSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticatedOrReadOnly()]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user if self.request.user.is_authenticated else None)

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.role == "admin":
            return ChatSession.objects.all()
        return ChatSession.objects.filter(user=user)

    @action(methods=["post"], detail=True, url_path="ask", permission_classes=[permissions.AllowAny])
    def ask(self, request, pk=None):
        """
        Nhận câu hỏi từ user, lưu vào ChatMessage, tìm context từ news,
        trả về câu trả lời + lịch sử.
        """
        session = self.get_object()
        question = request.data.get("question")

        if not question:
            return Response({"error": "Missing question"}, status=status.HTTP_400_BAD_REQUEST)

        # Lưu câu hỏi
        ChatMessage.objects.create(session=session, role="user", content=question)

        # Tìm context từ news
        context_docs = search_news(question, top_k=3)
        answer = context_docs[0] if context_docs else "Xin lỗi, hiện mình chưa tìm thấy thông tin phù hợp."

        # Lưu câu trả lời
        ChatMessage.objects.create(session=session, role="bot", content=answer)

        # Log usage
        AIUsageLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            type="chatbot",
            input_data={"question": question},
            output_data={"answer": answer, "sources": context_docs}
        )

        return Response({
            "session_id": session.id,
            "answer": answer,
            "history": ChatMessageSerializer(session.messages.all(), many=True).data
        })

    @action(methods=["post"], detail=True, url_path="clear", permission_classes=[permissions.IsAuthenticated])
    def clear(self, request, pk=None):
        """
        Xóa toàn bộ message trong session (reset hội thoại).
        """
        session = self.get_object()
        session.messages.all().delete()
        return Response({"status": "cleared", "session_id": session.id})

@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def create_chat_session(request):
    session = ChatSession.objects.create(
        user=request.user if request.user.is_authenticated else None
    )
    return Response({"id": session.id})


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def send_message(request):
    session_id = request.data.get("session_id")
    message = request.data.get("message")

    if not message:
        return Response({"error": "Message is required"}, status=400)

    # Nếu chưa có session thì tạo mới
    if not session_id:
        session = ChatSession.objects.create(
            user=request.user if request.user.is_authenticated else None
        )
    else:
        try:
            session = ChatSession.objects.get(id=session_id)
        except ChatSession.DoesNotExist:
            return Response({"error": "Session not found"}, status=404)

    # Lưu tin nhắn của user
    ChatMessage.objects.create(session=session, role="user", content=message)

    # 🔍 Tìm tin tức liên quan bằng RAG
    retrieved_news = search_news(message)

    # 🧠 Gọi model AI (ví dụ GPT-2)
    nlp = pipeline("text-generation", model="gpt2")
    bot_text = nlp(f"User asked: {message}. Relevant news: {retrieved_news}", max_length=100)[0]["generated_text"]

    # Lưu tin nhắn bot
    ChatMessage.objects.create(session=session, role="bot", content=bot_text)

    # Log AI usage
    AIUsageLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        type="chatbot",
        input_data={"message": message},
        output_data={"reply": bot_text}
    )

    # Trả về toàn bộ lịch sử chat
    history = [
        {"role": m.role, "content": m.content, "created_at": m.created_at}
        for m in session.messages.all().order_by("created_at")
    ]

    return Response({"session_id": session.id, "history": history})


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def chat_history(request, session_id):
    try:
        session = ChatSession.objects.get(id=session_id)
    except ChatSession.DoesNotExist:
        return Response({"error": "Session not found"}, status=404)

    history = [
        {"role": m.role, "content": m.content, "created_at": m.created_at}
        for m in session.messages.all().order_by("created_at")
    ]

    return Response({"session_id": session.id, "history": history})
