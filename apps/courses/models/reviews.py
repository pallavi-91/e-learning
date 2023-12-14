from django.db import models
from django.utils.translation import gettext as _
from django.core.validators import MaxValueValidator, MinValueValidator
from apps.status.mixins import AutoCreatedUpdatedMixin
from django.utils.functional import cached_property
from django.contrib.auth import get_user_model
from apps.utils.slugify import unique_slugify


class CourseReview(AutoCreatedUpdatedMixin):
    class Meta:
        db_table = 'course_reviews'
        
    rate = models.IntegerField(validators=[MinValueValidator(1),MaxValueValidator(5)],default=0)
    user = models.ForeignKey(get_user_model(),related_name='course_reviews',on_delete=models.CASCADE)
    course = models.ForeignKey('courses.Course',related_name='reviews',on_delete=models.CASCADE)
    content = models.TextField(default='')
    likes = models.ManyToManyField(get_user_model(),related_name='likes')
    dislikes = models.ManyToManyField(get_user_model(),related_name='dislikes')

    @cached_property
    def calc_likes(self):
        likes = self.likes.select_related('likes').count()
        dislikes = self.dislikes.select_related('dislikes').count()
        return likes - dislikes

    @cached_property
    def is_reported(self):
        return self.reports.exists()

class ReportedCourseReview(AutoCreatedUpdatedMixin):
    class Meta:
        db_table = 'reported_course_reviews'
        
    user = models.ForeignKey(get_user_model(),related_name='reported_reviews',on_delete=models.CASCADE)
    review = models.ForeignKey(CourseReview, related_name='reports',on_delete=models.CASCADE)
    issue = models.CharField(max_length=200)
    description = models.TextField(default='')
    
    def __str__(self):
        return f"<ReportedCourseReview>: {self.id} - {self.issue}"