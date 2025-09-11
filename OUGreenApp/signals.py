from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from .models import News, NewsletterSubscriber

@receiver(post_save, sender=News)
def send_newsletter_on_new_news(sender, instance, created, **kwargs):
    if created:  # chỉ khi tạo mới, không gửi khi update
        subject = f"📰 Tin tức mới: {instance.title}"
        message = instance.content[:200] + "..." if instance.content else "Xem chi tiết tại website."

        subscribers = NewsletterSubscriber.objects.values_list("email", flat=True)
        if not subscribers:
            return

        try:
            sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
            for email in subscribers:
                mail = Mail(
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to_emails=email,
                    subject=subject,
                    plain_text_content=message,
                )
                sg.send(mail)
        except Exception as e:
            print(f"[Newsletter] Error sending email: {e}")