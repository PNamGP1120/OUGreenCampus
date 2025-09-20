import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth import get_user_model
from OUGreenApp.models import News, Category, Tag
from datetime import datetime
import feedparser
from urllib.parse import urljoin

User = get_user_model()


class Command(BaseCommand):
    help = "Tự động crawl tin tức môi trường từ nhiều nguồn RSS và lưu vào bảng News (ảnh lưu link gốc)"

    def handle(self, *args, **options):
        # 📡 Danh sách nhiều nguồn tin tức
        rss_urls = [
            "https://baotainguyenmoitruong.vn/rss/home.rss",   # Báo TN&MT
            "https://vnexpress.net/rss/khoa-hoc.rss",         # VNExpress Khoa học
            "https://tuoitre.vn/rss/khoa-hoc.rss",            # Tuổi Trẻ Khoa học
            "https://thanhnien.vn/rss/giao-duc/khoa-hoc.rss", # Thanh Niên Khoa học
            "https://vietnamnet.vn/rss/khoa-hoc.rss",         # Vietnamnet Khoa học
        ]

        # 🔑 Bộ từ khóa về môi trường
        keywords = [
            "môi trường", "biến đổi khí hậu", "năng lượng tái tạo",
            "năng lượng sạch", "rác thải", "tái chế", "ô nhiễm",
            "khí thải", "thiên nhiên", "phát triển bền vững",
            "bảo vệ động vật", "sinh thái", "trồng cây", "tài nguyên",
            "nước thải", "không khí", "rừng", "biển", "đại dương", "năng lượng xanh"
        ]

        # 📂 Category mặc định
        category, _ = Category.objects.get_or_create(name="Tin tức môi trường")

        # 👤 Author mặc định: từ settings hoặc fallback
        author = None
        default_author_username = getattr(settings, "DEFAULT_NEWS_AUTHOR", None)
        if default_author_username:
            author = User.objects.filter(username=default_author_username).first()
        if not author:
            author = User.objects.filter(role="admin").first() or User.objects.first()

        for rss_url in rss_urls:
            self.stdout.write(f"📡 Đang crawl từ {rss_url}")
            feed = feedparser.parse(rss_url)

            for entry in feed.entries:
                title = entry.title.strip()
                link = entry.link
                published = entry.get("published_parsed", None)

                # Ngày đăng
                published_at = datetime.now()
                if published:
                    published_at = datetime(*published[:6])

                # Crawl nội dung chi tiết + ảnh
                content = ""
                img_url = None
                try:
                    response = requests.get(link, timeout=10)
                    soup = BeautifulSoup(response.text, "html.parser")

                    # Lấy nội dung
                    paragraphs = soup.find_all("p")
                    content = "\n".join([p.get_text() for p in paragraphs if p.get_text()])

                    # Lấy ảnh đầu tiên
                    img_tag = soup.find("img")
                    if img_tag and img_tag.get("src"):
                        img_url = img_tag["src"]
                        if img_url.startswith("/"):
                            img_url = urljoin(link, img_url)
                except Exception:
                    pass

                # 🔍 Lọc chính xác hơn
                text_title = title.lower()
                text_content = content.lower()

                if any(kw in text_title for kw in keywords):
                    is_relevant = True
                else:
                    is_relevant = any(kw in text_content for kw in keywords)

                if not is_relevant:
                    self.stdout.write(self.style.NOTICE(f"⏭ Bỏ qua (không liên quan): {title}"))
                    continue

                # ✅ Lưu tin tức nếu chưa có
                if not News.objects.filter(title=title).exists():
                    news = News.objects.create(
                        category=category,
                        author=author,
                        title=title,
                        content=content,
                        image=img_url,  # 👉 lưu link ảnh gốc
                        status="draft"
                    )
                    self.stdout.write(self.style.SUCCESS(f"✅ Đã thêm: {title}"))

                    # Tag theo domain (nguồn báo)
                    tag_name = rss_url.split("/")[2]
                    tag, _ = Tag.objects.get_or_create(name=tag_name)
                    news.tags.add(tag)
                else:
                    self.stdout.write(self.style.WARNING(f"⏭ Bỏ qua (đã có): {title}"))

