from cloudinary.models import CloudinaryField
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.text import slugify


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class User(AbstractUser, TimeStampedModel):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('editor', 'Editor'),
        ('admin', 'Admin'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='user'
    )
    avatar = CloudinaryField('avatars/')
    phone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.username


class Category(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["slug"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug or self.slug.strip() == "":
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Tag(TimeStampedModel):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["slug"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug or self.slug.strip() == "":
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class News(TimeStampedModel):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="news")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="news")
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True, null=True)
    image = CloudinaryField('images/')

    tags = models.ManyToManyField(Tag, related_name='news_items', blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["title"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return self.title


class Document(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="documents")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    file = CloudinaryField('documents/')

    tags = models.ManyToManyField(Tag, related_name='documents', blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class ProjectContest(TimeStampedModel):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('archived', 'Archived'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        db_index=True
    )
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"


class Proposal(TimeStampedModel):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    project_contest = models.ForeignKey(
        ProjectContest, on_delete=models.CASCADE, related_name='proposals'
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='proposals'
    )
    content = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )

    class Meta:
        unique_together = ('project_contest', 'user')
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.user} → {self.project_contest} ({self.get_status_display()})"


class Feedback(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedbacks')
    message = models.TextField()

    class Meta:
        indexes = [
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"Feedback #{self.id} by {self.user}"


class Comment(TimeStampedModel):
    content = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    news = models.ForeignKey(News, on_delete=models.CASCADE, null=True, blank=True)
    project = models.ForeignKey(ProjectContest, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.user.username}: {self.content[:30]}"


class Like(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="likes")
    news = models.ForeignKey(News, on_delete=models.CASCADE, null=True, blank=True, related_name="likes")
    project = models.ForeignKey(ProjectContest, on_delete=models.CASCADE, null=True, blank=True, related_name="likes")

    class Meta:
        unique_together = ('user', 'news', 'project')
        indexes = [
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        target = self.news or self.project
        return f"{self.user.username} liked {target}"


class AIUsageLog(TimeStampedModel):
    TYPE_CHOICES = [
        ('waste_classifier', 'Waste Classifier'),
        ('chatbot', 'Chatbot'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='ai_logs',
        null=True, blank=True
    )
    type = models.CharField(max_length=50, choices=TYPE_CHOICES, db_index=True)
    input_data = models.JSONField(blank=True, null=True)
    output_data = models.JSONField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=["type"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.get_type_display()} by {self.user or 'Anonymous'} at {self.created_at}"


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email
