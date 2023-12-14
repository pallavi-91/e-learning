from django.db import models
from datetime import date, time, datetime
from apps.status.mixins import AutoCreatedUpdatedMixin
from django.contrib.auth import get_user_model
from apps.status import NotificationType
from core.store.storage_backends import PrivateMediaStorage


def notification_template_image(obj, filename):
    """
        set template image path
    """
    return f"notification_templates/courses/{obj.id}/{filename}"

class NotificationTemplate(AutoCreatedUpdatedMixin):
    """ Notification Templates"""
    class Meta:
        db_table = 'notification_templates'
        verbose_name = "Notification Template"
        verbose_name_plural = "Notification Templates"
        
    title = models.CharField(verbose_name="Title", max_length=200)
    course = models.ForeignKey('courses.Course', related_name="notifications",on_delete=models.CASCADE)
    notification_type = models.CharField(verbose_name="Notification Type", max_length=20, default=NotificationType.ANNOUNCEMENTS, choices=NotificationType.choices, unique=True)
    template_image = models.ImageField(upload_to=notification_template_image, null=True, blank=True, storage=PrivateMediaStorage())
    description = models.TextField(verbose_name="Description", blank=True, default="")
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)

    def __str__(self):
        return f"<NotificationTemplate> {self.notification_type}"
    

class Notification(AutoCreatedUpdatedMixin):
    """Notifications"""
    class Meta:
        db_table = 'notifications'
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        
    user = models.ForeignKey(get_user_model(),related_name='notifications',on_delete=models.CASCADE)
    template = models.ForeignKey('NotificationTemplate',related_name='notifications',on_delete=models.CASCADE)
    seen_status = models.BooleanField(default=False)
    description = models.TextField(verbose_name="Description", blank=True, default="")
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)

    def __str__(self):
        return f"<Notification> {self.id}"
    
