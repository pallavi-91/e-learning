import os
from typing import Iterable, Optional
from django.db import models
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils.translation import gettext as _
from apps.status import CourseLectureType
from apps.status.mixins import AutoCreatedUpdatedMixin
from apps.utils.cloudflare import CloudflareStream
from django.db.models import Q
from django.contrib.auth import get_user_model
from apps.utils.helpers import calc_read_time, file_info, quill_delta_to_text
from core.store.storage_backends import CoursesMediaStorage, PrivateMediaStorage

def course_lecture_media(obj, filename):
    """ set course main media image
    """
    return (
        f"users/{obj.section.course.user.id}/"
        f"courses/{obj.section.course.id}/"
        f"sections/{obj.section.id}/"
        f"lectures/{obj.id}/{filename}"
    )

def course_lecture_resources_media(obj, filename):
    """ set course main media image
    """
    return (
        f"users/{obj.lecture.section.course.user.id}/"
        f"courses/{obj.lecture.section.course.id}/"
        f"sections/{obj.lecture.section.id}/"
        f"lectures/{obj.lecture.id}/"
        f"downloadables/{filename}"
    )

def course_lecture_article(obj,filename):
    return f'{obj.user.id}/articles/{filename}'

class Lecture(AutoCreatedUpdatedMixin):
    """ lecture
    """
    class Meta:
        db_table = 'course_lecture'
        verbose_name_plural = "Lectures"
        
    title = models.CharField(max_length=100)
    section = models.ForeignKey('courses.Section', related_name="lectures", on_delete=models.CASCADE)
    video = models.FileField(upload_to=course_lecture_media, null=True, blank=True, storage=CoursesMediaStorage())
    video_id = models.CharField(max_length=255,null=True,blank=True)
    video_info = models.JSONField(default=dict, blank=True, null=True)
    article = models.JSONField(null=True, blank=True)
    type = models.CharField(max_length=10, choices=CourseLectureType.choices, null=True, blank=True)
    position = models.PositiveIntegerField(default=0)
    preview = models.BooleanField(default=False)

    def __str__(self):
        return f"<Lecture>: {self.title} ({self.type}: {self.id})"

    @staticmethod
    def successful_lectures():
        qs_article_video = Lecture.objects.filter(Q(video_info__status='completed')|Q(type=CourseLectureType.ARTICLE))
        return qs_article_video.distinct()


    # @property
    # def video_info(self):
    #     """ return video information
    #     """
    #     if not self.video: return {}

    #     d = file_info(self.video.path)
    #     path_, name = os.path.split(self.video.name)
    #     return {
    #         'filename': name,
    #         'duration': float(d['duration']), 
    #         'bit_rate': sizeof_fmt(int(d['bit_rate'])),
    #         'codec_name': d['codec_name'],
    #         'size': sizeof_fmt(self.video.size),
    #     }

    @property
    def duration(self):
        if self.type == CourseLectureType.ARTICLE:
            text_data = quill_delta_to_text(self.article) if type(self.article) == dict else ""
            return calc_read_time(text_data)
        else:
            duration = self.video_info.get('duration', None)
            # if duration == None:
            #     dfi = file_info(self.video.url)
            #     return float(dfi['duration'])
            return duration if duration else 0

    @property
    def article_info(self):
        if not self.type == CourseLectureType.ARTICLE: return {}
        # self.article => https://quilljs.com/docs/delta/
        text_data = quill_delta_to_text(self.article) if type(self.article) == dict else ""
        return {
            'duration': calc_read_time(text_data),
            'text_data': text_data
        }

class LectureResource(AutoCreatedUpdatedMixin):
    """ downloadable resources
    """
    class Meta:
        db_table = 'course_lecture_resources'
        verbose_name_plural = "Lecture Resources"
        
    lecture = models.ForeignKey(Lecture, related_name="resources", on_delete=models.CASCADE)
    file = models.FileField(upload_to=course_lecture_resources_media, storage=PrivateMediaStorage())

    def __str__(self):
        return f"<Lecture Resource> : {self.id}"


class ImageUpload(AutoCreatedUpdatedMixin):
    """ Image upload for articles
    """
    class Meta:
        db_table = 'articles_images'
        
    user = models.ForeignKey(get_user_model(),related_name='image_uploads',on_delete=models.CASCADE)
    section = models.ForeignKey('courses.Section',related_name='image_uploads',on_delete=models.CASCADE)
    height = models.PositiveIntegerField(default=0)
    width = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to=course_lecture_article, height_field='height', width_field='width', storage=PrivateMediaStorage())

    def __str__(self):
        return f"{self.id}"
    
@receiver(post_delete, sender=LectureResource)
def after_delete(instance, **kwargs):
    if instance.file and os.path.isfile(instance.file.path):
        os.remove(instance.file.path)



@receiver(post_delete, sender=Lecture)
def after_delete_video_lecture(instance, **kwargs):
    if instance.type == CourseLectureType.ARTICLE: return
    
    # if not instance.video_id and instance.video_info.get('uid'):
    #     return CloudflareStream(video_id=instance.video_info.get('uid')).delete()

    # if instance.video_id:
    #     CloudflareStream(video_id=instance.video_id).delete()

@receiver(pre_save, sender=Lecture)
def before_delete_lecture(instance, **kwargs):
    if not instance.id: return
    if instance.type == CourseLectureType.ARTICLE: return
    
    # lecture = Lecture.objects.get(id=instance.id)
    # if instance.video_id != lecture.video_id:
    #     CloudflareStream(video_id=lecture.video_id).delete()
    #     instance.video_info = {} # emoty video info if the video instance is deleted


@receiver(post_save, sender=Lecture)
def after_save(instance, created=False, **kwargs):
    if created:
        lectures = Lecture.objects \
            .filter(section=instance.section).count() + 1
        
        instance.position = lectures
        instance.save()
