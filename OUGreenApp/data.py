# OUGreenApp/data.py
from django.contrib.auth import get_user_model
from .models import Category, Tag, News, Document, ProjectContest, Proposal, Feedback, AIUsageLog

def init_data():
    User = get_user_model()

    # --- XÓA HẾT DỮ LIỆU ---
    Proposal.objects.all().delete()
    News.objects.all().delete()
    Document.objects.all().delete()
    Feedback.objects.all().delete()
    AIUsageLog.objects.all().delete()
    ProjectContest.objects.all().delete()
    Category.objects.all().delete()
    Tag.objects.all().delete()
    User.objects.exclude(is_superuser=True).delete()  # giữ lại superuser

    print("⚡ Đã xoá toàn bộ dữ liệu cũ")

    # --- Superuser ---
    if not User.objects.filter(username="admin").exists():
        admin = User.objects.create_superuser(
            username="admin",
            email="admin@ou.edu.vn",
            password="Admin@123",
            role="admin",
        )
        print("✅ Superuser 'admin' created")
    else:
        admin = User.objects.get(username="admin")

    # --- Users ---
    users = [
        User.objects.create_user(username="nam", email="nam@student.ou.edu.vn", password="User@123", role="user"),
        User.objects.create_user(username="hoa", email="hoa@student.ou.edu.vn", password="User@123", role="user"),
        User.objects.create_user(username="linh", email="linh@student.ou.edu.vn", password="User@123", role="user"),
        User.objects.create_user(username="tuan", email="tuan@student.ou.edu.vn", password="User@123", role="user"),
        User.objects.create_user(username="anh", email="anh@student.ou.edu.vn", password="User@123", role="user"),
    ]

    editors = [
        User.objects.create_user(username="editor_minh", email="minh@ou.edu.vn", password="Editor@123", role="editor"),
        User.objects.create_user(username="editor_hanh", email="hanh@ou.edu.vn", password="Editor@123", role="editor"),
        User.objects.create_user(username="editor_long", email="long@ou.edu.vn", password="Editor@123", role="editor"),
        User.objects.create_user(username="editor_mai", email="mai@ou.edu.vn", password="Editor@123", role="editor"),
        User.objects.create_user(username="editor_hoang", email="hoang@ou.edu.vn", password="Editor@123", role="editor"),
    ]

    # --- Categories ---
    categories = [
        Category.objects.create(name="Môi trường", description="Hoạt động bảo vệ môi trường tại OU."),
        Category.objects.create(name="Công nghệ xanh", description="Ứng dụng công nghệ hỗ trợ phát triển bền vững."),
        Category.objects.create(name="Giáo dục", description="Các chương trình giáo dục nâng cao ý thức xanh."),
        Category.objects.create(name="Sự kiện", description="Sự kiện do OU tổ chức về bảo vệ môi trường."),
        Category.objects.create(name="Tình nguyện", description="Hoạt động tình nguyện vì cộng đồng."),
    ]

    # --- Tags ---
    tags = [
        Tag.objects.create(name="Tái chế", description="Các hoạt động tái chế vật liệu."),
        Tag.objects.create(name="Tiết kiệm năng lượng", description="Giải pháp giảm điện, nước."),
        Tag.objects.create(name="Cộng đồng", description="Hoạt động phục vụ và gắn kết cộng đồng."),
        Tag.objects.create(name="Sáng tạo", description="Ý tưởng sáng tạo, khởi nghiệp xanh."),
        Tag.objects.create(name="Giáo dục", description="Chia sẻ kiến thức và nâng cao nhận thức."),
    ]

    # --- News ---
    news_items = [
        News.objects.create(
            category=categories[0],
            author=editors[0],
            title="Sinh viên OU tham gia phân loại rác tại nguồn",
            content="Hơn 200 sinh viên đã tham gia buổi tập huấn phân loại rác ngay tại ký túc xá.",
            image="sample.jpg",
        ),
        News.objects.create(
            category=categories[1],
            author=editors[1],
            title="Ứng dụng AI trong phân loại rác thải",
            content="Nhóm nghiên cứu CNTT đã phát triển hệ thống AI hỗ trợ phân loại rác nhanh chóng.",
            image="sample.jpg",
        ),
        News.objects.create(
            category=categories[2],
            author=editors[2],
            title="Chương trình giáo dục xanh cho học sinh",
            content="CLB OU Green đã tổ chức 5 buổi ngoại khóa cho học sinh tiểu học về môi trường.",
            image="sample.jpg",
        ),
        News.objects.create(
            category=categories[3],
            author=editors[3],
            title="Ngày hội Sống Xanh 2025",
            content="Hàng ngàn sinh viên đã tham gia ngày hội, lan tỏa thông điệp sống xanh.",
            image="sample.jpg",
        ),
        News.objects.create(
            category=categories[4],
            author=editors[4],
            title="Chiến dịch thu gom pin cũ",
            content="Sinh viên OU đã thu gom hơn 500kg pin cũ trong vòng 1 tháng.",
            image="sample.jpg",
        ),
    ]
    # Thêm tags cho news
    news_items[0].tags.add(tags[0])
    news_items[1].tags.add(tags[1], tags[3])
    news_items[2].tags.add(tags[4], tags[2])
    news_items[3].tags.add(tags[2], tags[3])
    news_items[4].tags.add(tags[0], tags[2])

    # --- Documents ---
    documents = [
        Document.objects.create(user=editors[0], title="Sổ tay sống xanh", description="Hướng dẫn 10 bước sống xanh tại OU.", file="docs/songxanh.pdf"),
        Document.objects.create(user=editors[1], title="Hướng dẫn tiết kiệm năng lượng", description="Các biện pháp tiết kiệm điện và nước trong trường học.", file="docs/nangluong.pdf"),
        Document.objects.create(user=editors[2], title="Tài liệu về tái chế nhựa", description="Các phương pháp tái chế và tái sử dụng nhựa.", file="docs/nhua.pdf"),
        Document.objects.create(user=editors[3], title="Chương trình giáo dục xanh", description="Giáo trình cho CLB về môi trường.", file="docs/giaoduc.pdf"),
        Document.objects.create(user=editors[4], title="Kế hoạch tình nguyện xanh", description="Kế hoạch chi tiết cho chiến dịch tình nguyện.", file="docs/tinhnguyen.pdf"),
    ]
    documents[0].tags.add(tags[2], tags[4])
    documents[1].tags.add(tags[1])
    documents[2].tags.add(tags[0])
    documents[3].tags.add(tags[4])
    documents[4].tags.add(tags[2])

    # --- Project Contests ---
    contests = [
        ProjectContest.objects.create(title="Cuộc thi Đại sứ Môi trường 2025", description="Tìm kiếm gương mặt sinh viên tiêu biểu bảo vệ môi trường.", status="open"),
        ProjectContest.objects.create(title="Hackathon Công nghệ Xanh", description="Sinh viên phát triển giải pháp công nghệ cho môi trường.", status="draft"),
        ProjectContest.objects.create(title="Ý tưởng tái chế sáng tạo", description="Khuyến khích ý tưởng tái chế độc đáo.", status="open"),
        ProjectContest.objects.create(title="Giáo dục xanh cho cộng đồng", description="Các dự án nâng cao nhận thức cộng đồng.", status="closed"),
        ProjectContest.objects.create(title="Tình nguyện xanh 2025", description="Chiến dịch tình nguyện bảo vệ môi trường.", status="archived"),
    ]

    # --- Proposals ---
    proposals = [
        Proposal.objects.create(project_contest=contests[0], user=users[0], content="Dự án trồng cây tại ký túc xá OU.", status="pending"),
        Proposal.objects.create(project_contest=contests[1], user=users[1], content="Ứng dụng IoT giám sát rác thải.", status="approved"),
        Proposal.objects.create(project_contest=contests[2], user=users[2], content="Tái chế chai nhựa thành vật dụng học tập.", status="rejected"),
        Proposal.objects.create(project_contest=contests[3], user=users[3], content="Tổ chức workshop giáo dục xanh cho học sinh.", status="approved"),
        Proposal.objects.create(project_contest=contests[4], user=users[4], content="Chiến dịch dọn rác ven sông Sài Gòn.", status="pending"),
    ]

    # --- Feedback ---
    feedbacks = [
        Feedback.objects.create(user=users[0], message="Ứng dụng rất hữu ích cho việc phân loại rác."),
        Feedback.objects.create(user=users[1], message="Mong có thêm nhiều tài liệu hướng dẫn."),
        Feedback.objects.create(user=users[2], message="Các sự kiện xanh rất thú vị."),
        Feedback.objects.create(user=users[3], message="Cuộc thi công nghệ xanh thật sự truyền cảm hứng."),
        Feedback.objects.create(user=users[4], message="Hoạt động tình nguyện xanh giúp kết nối cộng đồng."),
    ]

    # --- AIUsageLog ---
    logs = [
        AIUsageLog.objects.create(user=users[0], type="waste_classifier", input_data={"input": "Chai nhựa"}, output_data={"output": "Tái chế"}),
        AIUsageLog.objects.create(user=users[1], type="chatbot", input_data={"input": "Làm sao tiết kiệm điện?"}, output_data={"output": "Tắt thiết bị khi không dùng."}),
        AIUsageLog.objects.create(user=users[2], type="waste_classifier", input_data={"input": "Pin cũ"}, output_data={"output": "Bỏ vào thùng pin chuyên dụng."}),
        AIUsageLog.objects.create(user=users[3], type="chatbot", input_data={"input": "OU có sự kiện xanh nào sắp tới?"}, output_data={"output": "Ngày hội Sống Xanh 2025."}),
        AIUsageLog.objects.create(user=users[4], type="chatbot", input_data={"input": "Cách tái chế giấy"}, output_data={"output": "Dùng giấy đã in 1 mặt để ghi chú."}),
    ]

    print("✅ Đã khởi tạo dữ liệu thực tế cho hệ thống")
