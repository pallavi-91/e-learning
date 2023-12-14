from django.db import models, transaction
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils.translation import gettext as _
from apps.courses.models.lectures import Lecture
from apps.courses.models.quizs import Assignment, Quiz
from apps.status import CourseLectureType
from apps.status.mixins import AutoCreatedUpdatedMixin
from apps.utils.cloudflare import CloudflareStream
from django.utils.functional import cached_property
from django.contrib.auth import get_user_model
from django.db.models import Func, F, FloatField, Sum, Q, Case, When, Count
from django.db.models.expressions import Value
from django.db.models.functions import Cast, Coalesce

class Section(AutoCreatedUpdatedMixin):
    """ course section 
    """
    class Meta:
        db_table = 'course_sectios'
        verbose_name_plural = "Sections"
        
    course = models.ForeignKey('courses.Course',
        related_name="sections", on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    position = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.title}"

    @property
    def duration(self):
        text = Func(F('lecture__video_info'), Value('duration'), function='jsonb_extract_path_text')
        floatfield = Cast(text, FloatField())
        subs = self.subsections.select_related('lecture').aggregate(duration=Sum(floatfield, filter=(Q(type=SubSection.LECTURE)&Q(lecture__type=CourseLectureType.VIDEO))))
        return subs.get('duration') if subs.get('duration') else 0

    @transaction.atomic
    def update_subsection_position(self):
        index = 0
        for sub in self.subsections.order_by('position'):
            index += 1
            sub.position = index
            sub.save()
        return self

    class Meta:
        ordering = ['position']


class SubSection(AutoCreatedUpdatedMixin):
    LECTURE = "lecture"
    QUIZ = "quiz"
    ASSIGNMENT = "assignment"
    SUB_SECTION_TYPES = (
        (LECTURE, LECTURE.capitalize()),
        (QUIZ, QUIZ.capitalize()),
        (ASSIGNMENT, ASSIGNMENT.capitalize()),
    )

    class Meta:
        db_table = 'course_subsections'
        verbose_name_plural = "SubSections"
        ordering = ['position']
        
    type = models.CharField(default=LECTURE,max_length=255, choices=SUB_SECTION_TYPES)
    position = models.IntegerField(default=1)
    quiz =  models.ForeignKey('courses.Quiz',null=True,blank=True,on_delete=models.CASCADE,related_name='subsections')
    lecture =  models.ForeignKey('courses.Lecture',null=True,blank=True,on_delete=models.CASCADE,related_name='subsections')
    assignment =  models.ForeignKey('courses.Assignment',null=True,blank=True,on_delete=models.CASCADE,related_name='subsections')
    section = models.ForeignKey(Section,on_delete=models.CASCADE,related_name="subsections")

    def __str__(self) -> str:
        return f"<SubSection> : {self.type}"
    
    @cached_property
    def preview(self):
        return self.lecture and self.lecture.preview
    
    @cached_property
    def duration(self):
        if self.type == SubSection.LECTURE:
            self.lecture.duration
        return 0
    

class SubsectionProgress(AutoCreatedUpdatedMixin):
    class Meta:
        db_table = 'course_student_progress'
        verbose_name_plural = "Video Classes progress"
        
    user = models.ForeignKey(get_user_model(), related_name='class_progress',on_delete=models.CASCADE)
    subsection = models.ForeignKey(SubSection, related_name='progress',on_delete=models.CASCADE)
    position = models.PositiveBigIntegerField(default=0) # position of video NOTE: applicable for video type of lecture
    is_completed = models.BooleanField(default=False)
    watched_duration = models.FloatField(default=0)
    
    def __str__(self) -> str:
        return f"<SubsectionProgress> : {self.id}"
    

@receiver(post_save, sender=Section)
def after_save(instance, created=False, **kwargs):
    if created:
        # automatically set the position
        instance.position = instance.course.sections.count() + 1
        instance.save()


@receiver(post_delete, sender=Section)
def after_delete_section(instance, created=False, **kwargs):
    instance.course.update_section_position()


@receiver(post_delete, sender=SubSection)
@transaction.atomic
def handle_deleted_subsection(sender, instance, **kwargs):
    instance.section.update_subsection_position()

    try:
        if instance.lecture and instance.lecture.id:
            instance.lecture.delete()
        if instance.assignment and instance.assignment.id:
            instance.assignment.delete()
        if instance.quiz and instance.quiz.id:
            instance.quiz.delete()
    except Assignment.DoesNotExist: pass
    except Lecture.DoesNotExist: pass
    except Quiz.DoesNotExist: pass