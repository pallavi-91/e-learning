from django.db import models
from django.utils.translation import gettext as _
from apps.status.mixins import AutoCreatedUpdatedMixin
from django.contrib.auth import get_user_model
from apps.users.models import UserClass


class QnA(AutoCreatedUpdatedMixin):
    class Meta:
        db_table = 'question_answer'
        verbose_name_plural = "Qustion and Answer"
        
    user = models.ForeignKey(get_user_model(), related_name='qna_users',on_delete=models.CASCADE)
    user_class = models.ForeignKey(UserClass,related_name='qna',on_delete=models.CASCADE)
    subsection = models.ForeignKey('courses.SubSection', related_name='qna',on_delete=models.CASCADE)
    title = models.CharField(max_length=60)
    description = models.TextField(null=True, blank=True)
    approved = models.BooleanField(default=False)
    upvoted_users = models.ManyToManyField(get_user_model(), related_name='upvoted_qna', blank=True)

    def __str__(self) -> str:
        return f"<QnA> : {self.id}"
    
class QnAReplys(AutoCreatedUpdatedMixin):
    class Meta:
        db_table = 'question_answer_replys'
        verbose_name_plural = "Qustion and Answer Replys"
        
    qna = models.ForeignKey(QnA, related_name='qnas',on_delete=models.CASCADE)
    user = models.ForeignKey(get_user_model(), related_name='qna_reply_users',on_delete=models.CASCADE)
    comment = models.TextField(null=True, blank=True)
    upvoted_users = models.ManyToManyField(get_user_model(), related_name='upvoted_qna_reply', blank=True)

    def __str__(self) -> str:
        return f"<QnAReplys> : {self.id}"


    @property
    def reported(self):
        return self.reports.exists()

class ReportedQnaReply(AutoCreatedUpdatedMixin):
    class Meta:
        db_table = 'reported_qna_reply'
        
    user = models.ForeignKey(get_user_model(),related_name='reported_gnareply',on_delete=models.CASCADE)
    reply = models.ForeignKey(QnAReplys, related_name='reports',on_delete=models.CASCADE)
    issue = models.CharField(max_length=200)
    description = models.TextField(default='')
    
    def __str__(self):
        return f"<ReportedQnaReply>: {self.id} - {self.issue}"