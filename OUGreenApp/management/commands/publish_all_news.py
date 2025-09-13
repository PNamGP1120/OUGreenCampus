from django.core.management.base import BaseCommand
from OUGreenApp.models import News

class Command(BaseCommand):
    help = "Publish tất cả tin tức đang ở trạng thái draft"

    def handle(self, *args, **options):
        drafts = News.objects.filter(status="draft")
        count = drafts.count()
        if count == 0:
            self.stdout.write(self.style.WARNING("⚠️ Không có tin nào ở trạng thái draft."))
            return

        drafts.update(status="published")
        self.stdout.write(self.style.SUCCESS(f"✅ Đã publish {count} tin tức."))
