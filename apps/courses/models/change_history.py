from django.db import models
from apps.status import FieldCourseInReview
from apps.status.mixins import AutoCreatedUpdatedMixin
from django.utils.functional import cached_property
from django.contrib.auth import get_user_model
from copy import copy

# Define model for course in-review feedback

class CourseChangeHistory(AutoCreatedUpdatedMixin):
    class Meta:
        db_table = 'course_change_history'
        verbose_name_plural = 'Course Feedback/Change History'
    
    user = models.ForeignKey(get_user_model(), related_name="course_inreview_feedbacks", null=True, on_delete=models.SET_NULL)
    course = models.ForeignKey('courses.Course', related_name="inreview_feedbacks", on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=FieldCourseInReview.choices)
    # Other sub modules
    section = models.ForeignKey('courses.Section', related_name="course_section_feedbacks", null=True, on_delete=models.SET_NULL)
    lecture = models.ForeignKey('courses.Lecture', related_name="course_lecture_feedbacks", null=True, on_delete=models.SET_NULL)
    assignment =  models.ForeignKey('courses.Assignment', related_name="course_assignment_feedbacks", null=True, blank=True, on_delete=models.CASCADE)
    quiz =  models.ForeignKey('courses.Quiz', related_name="course_quiz_feedbacks", null=True, blank=True, on_delete=models.CASCADE)
    quiz_question = models.ForeignKey('courses.QuizQuestion', related_name="course_quizq_feedbacks", null=True, on_delete=models.SET_NULL)
    assignment_question = models.ForeignKey('courses.AssignmentQuestion', related_name="course_aq_feedbacks", null=True, on_delete=models.SET_NULL)
    pricing = models.ForeignKey('courses.CoursePrice', related_name="course_price_feedbacks", null=True, on_delete=models.SET_NULL)
    # Feedback message    
    message = models.TextField()
    required = models.BooleanField(default=False)
    # Change history
    current_value = models.TextField(blank=True, null=True)

    intended_learners = models.IntegerField(default=0) # intended_learners holds the id
    
    unread = models.BooleanField(default=True)

    resolved = models.BooleanField(default=False)
    
    def __str__(self) -> str:
        return f"<CourseInReviewFeedback>: {self.id} - {self.type}"
    
    def restore_version(self, currenct_user):
        # Create a entry of current version
        current_value = getattr(self.course, self.type)
        obj = copy(self)
        obj.id = None
        obj.current_value = current_value
        obj.user = currenct_user
        obj.save()
        # Update course with last version by checking fields
        course = self.course
        if self.type == 'sections':
            pass
            # TODO: Update course fields
        elif self.type == 'lecture':
            pass
            # TODO: Update course fields
        elif self.type == 'quiz_question':
            pass
            # TODO: Update course fields
        else:
            setattr(course, self.type, self.current_value)
        course.save()

