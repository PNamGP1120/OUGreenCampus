from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import path
from django.db.models import Count
from django.db.models.functions import TruncMonth, TruncDate
import json

from .models import (
    User, Category, Tag, News, Document, ProjectContest,
    Proposal, Feedback, AIUsageLog, Comment, Like
)
from .ai_evaluate import evaluate_model


# ===============================
# Đăng ký các model cơ bản
# ===============================
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "role", "is_active", "date_joined")
    list_filter = ("role", "is_active")
    search_fields = ("username", "email")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    search_fields = ("name",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    search_fields = ("name",)


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "author", "status", "created_at")
    list_filter = ("status", "category")
    search_fields = ("title", "content")



@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "created_at")
    search_fields = ("title", "description")


@admin.register(ProjectContest)
class ProjectContestAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "start_date", "end_date", "created_at")
    list_filter = ("status",)


@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display = ("user", "project_contest", "status", "created_at")
    list_filter = ("status",)


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("user", "message", "created_at")


@admin.register(AIUsageLog)
class AIUsageLogAdmin(admin.ModelAdmin):
    list_display = ("user", "type", "created_at")
    list_filter = ("type",)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("user", "content", "created_at")
    search_fields = ("content",)


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at")


# ===============================
# Custom Admin Site
# ===============================
class OUGreenAdminSite(admin.AdminSite):
    site_header = "OU Green Campus Admin"
    site_title = "OU Green Campus"
    index_title = "Trang quản trị"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("stats/", self.admin_view(self.stats_view), name="ou_stats"),
            path("ai-stats/", self.admin_view(self.ai_stats_view), name="ou_ai_stats"),
        ]
        return custom_urls + urls

    def stats_view(self, request):
        """Thống kê hệ thống"""

        user_by_role = list(User.objects.values("role").annotate(total=Count("id")))
        news_by_month = list(
            News.objects.annotate(month=TruncMonth("created_at"))
            .values("month").annotate(total=Count("id")).order_by("month")
        )
        docs_by_month = list(
            Document.objects.annotate(month=TruncMonth("created_at"))
            .values("month").annotate(total=Count("id")).order_by("month")
        )
        projects_by_status = list(
            ProjectContest.objects.values("status").annotate(total=Count("id"))
        )
        comments_by_day = list(
            Comment.objects.annotate(day=TruncDate("created_at"))
            .values("day").annotate(total=Count("id")).order_by("day")
        )
        likes_by_day = list(
            Like.objects.annotate(day=TruncDate("created_at"))
            .values("day").annotate(total=Count("id")).order_by("day")
        )
        ai_by_type = list(AIUsageLog.objects.values("type").annotate(total=Count("id")))

        context = dict(
            self.each_context(request),
            stats_data={
                "users": {"by_role": user_by_role},
                "news": {"by_month": news_by_month},
                "documents": {"by_month": docs_by_month},
                "projects": {"by_status": projects_by_status},
                "comments": {"by_day": comments_by_day},
                "likes": {"by_day": likes_by_day},
                "ai_usage": {"by_type": ai_by_type},
            },
            stats=json.dumps({
                "users": {"by_role": user_by_role},
                "news": {"by_month": news_by_month},
                "documents": {"by_month": docs_by_month},
                "projects": {"by_status": projects_by_status},
                "comments": {"by_day": comments_by_day},
                "likes": {"by_day": likes_by_day},
                "ai_usage": {"by_type": ai_by_type},
            }, default=str)
        )
        return TemplateResponse(request, "admin/stats.html", context)

    def ai_stats_view(self, request):
        """Thống kê hiệu quả AI"""
        ai_eval = evaluate_model()
        context = dict(
            self.each_context(request),
            ai_eval=ai_eval
        )
        return TemplateResponse(request, "admin/ai_stats.html", context)


# Khởi tạo admin site mới
admin_site = OUGreenAdminSite(name="ou_admin")
