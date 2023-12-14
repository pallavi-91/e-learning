from django.db import models
from django.utils.translation import gettext as _
from apps.status.mixins import AutoCreatedUpdatedMixin
from django.contrib.auth import get_user_model


class Quiz(AutoCreatedUpdatedMixin):
    class Meta:
        db_table = 'course_quiz'
        verbose_name_plural = "Quizzes"
        
    title = models.CharField(max_length=512)
    section = models.ForeignKey('courses.Section',on_delete=models.CASCADE,related_name='quizzes')

    def __str__(self):
        return f"<Quiz> : {self.title}"


class QuizQuestion(AutoCreatedUpdatedMixin):
    class Meta:
        db_table = 'course_quiz_questions'
        verbose_name_plural = "Quiz Questions"
        
    lecture = models.ForeignKey('courses.Lecture',on_delete=models.CASCADE,null=True,blank=True,related_name='questions')
    quiz = models.ForeignKey(Quiz,on_delete=models.CASCADE,related_name='questions')
    question = models.TextField()
    
    def __str__(self):
        return f"<QuizQuestion> : {self.question}"


class QuizAnswer(AutoCreatedUpdatedMixin):
    class Meta:
        db_table = 'course_quiz_answers'
        verbose_name_plural = "Quiz Answers"
        
    quiz_question = models.ForeignKey(QuizQuestion,related_name='answers',on_delete=models.CASCADE)
    answer = models.CharField(max_length=512)
    is_correct = models.BooleanField(default=False) 
    expected = models.CharField(max_length=512,null=True,blank=True)
    def __str__(self):
        return f"<QuizAnswer> : {self.answer}"


class StudentQuizAnswer(AutoCreatedUpdatedMixin):
    class Meta:
        db_table = 'course_student_quiz_answers'
        verbose_name_plural = "Student Quiz Answers"
        
    student_quiz = models.ForeignKey('StudentQuiz',related_name="student_answers",on_delete=models.CASCADE)
    question = models.ForeignKey(QuizQuestion, related_name='student_answers', on_delete=models.CASCADE)
    answer = models.ForeignKey(QuizAnswer, null=True, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"<StudentQuizAnswer> : {self.id}"


class StudentQuiz(AutoCreatedUpdatedMixin):
    class Meta:
        db_table = 'course_student_quiz'
        verbose_name_plural = "Student Quiz"
        
    user = models.ForeignKey(get_user_model(), related_name='student_quizzes',on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz,related_name='student_quizzes',on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"<StudentQuiz> : {self.id}"
    
# ===================  Course Assignments ========================

class Assignment(AutoCreatedUpdatedMixin):
    class Meta:
        db_table = 'course_assignments'
        verbose_name_plural = "Assignments"
        
    lecture = models.ForeignKey('courses.Lecture',null=True,blank=True,on_delete=models.CASCADE)
    title = models.CharField(max_length=512)
    section = models.ForeignKey('courses.Section',on_delete=models.CASCADE,related_name='assignments')
    
    def __str__(self) -> str:
        return f"<Assignment> : {self.title}"


class AssignmentQuestion(AutoCreatedUpdatedMixin):
    class Meta:
        db_table = 'course_assignment_questions'
        verbose_name_plural = "Assignment Questions"
        
    assignment = models.ForeignKey(Assignment,on_delete=models.CASCADE,related_name='questions')
    question = models.TextField()
    expected = models.TextField(blank=True,null=True)

    def __str__(self) -> str:
        return f"<AssignmentQuestion> : {self.id}"

class StudentAssignmentAnswer(AutoCreatedUpdatedMixin):
    class Meta:
        db_table = 'course_student_assignment_answers'
        verbose_name_plural = "Student Assignment Answers"
        
    student_assignment = models.ForeignKey('StudentAssignment',related_name="student_answers",on_delete=models.CASCADE)
    question = models.ForeignKey(AssignmentQuestion, related_name='student_answers', on_delete=models.CASCADE)
    answer = models.TextField(default="")
    feedback = models.TextField(default='')

    def __str__(self) -> str:
        return f"<StudentAssignmentAnswer> : {self.id}"

class StudentAssignment(AutoCreatedUpdatedMixin):
    class Meta:
        db_table = 'course_student_assignment'
        verbose_name_plural = "Student Assignment"
        
    DRAFT = 'draft'
    PUBLISH = 'publish'
    TYPES = (
        (DRAFT, DRAFT.capitalize()),
        (PUBLISH, PUBLISH.capitalize())
    )
    type = models.CharField(max_length=20,choices=TYPES, default=DRAFT)
    user = models.ForeignKey(get_user_model(), related_name='student_assignments',on_delete=models.CASCADE)
    assignment = models.ForeignKey(Assignment,related_name='student_assignments',on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"<StudentAssignment> : {self.id}"



