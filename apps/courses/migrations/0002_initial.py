# Generated by Django 4.1.4 on 2023-02-05 17:55

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('courses', '0001_initial'),
        ('currency', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='subsectionprogress',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='class_progress', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='subsection',
            name='assignment',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='subsections', to='courses.assignment'),
        ),
        migrations.AddField(
            model_name='subsection',
            name='lecture',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='subsections', to='courses.lecture'),
        ),
        migrations.AddField(
            model_name='subsection',
            name='quiz',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='subsections', to='courses.quiz'),
        ),
        migrations.AddField(
            model_name='subsection',
            name='section',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subsections', to='courses.section'),
        ),
        migrations.AddField(
            model_name='subcategory',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subcategories', to='courses.category'),
        ),
        migrations.AddField(
            model_name='studentquizanswer',
            name='answer',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='courses.quizanswer'),
        ),
        migrations.AddField(
            model_name='studentquizanswer',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='student_answers', to='courses.quizquestion'),
        ),
        migrations.AddField(
            model_name='studentquizanswer',
            name='student_quiz',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='student_answers', to='courses.studentquiz'),
        ),
        migrations.AddField(
            model_name='studentquiz',
            name='quiz',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='student_quizzes', to='courses.quiz'),
        ),
        migrations.AddField(
            model_name='studentquiz',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='student_quizzes', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='studentassignmentanswer',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='student_answers', to='courses.assignmentquestion'),
        ),
        migrations.AddField(
            model_name='studentassignmentanswer',
            name='student_assignment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='student_answers', to='courses.studentassignment'),
        ),
        migrations.AddField(
            model_name='studentassignment',
            name='assignment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='student_assignments', to='courses.assignment'),
        ),
        migrations.AddField(
            model_name='studentassignment',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='student_assignments', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='section',
            name='course',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sections', to='courses.course'),
        ),
        migrations.AddField(
            model_name='scope',
            name='course',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='scope', to='courses.course'),
        ),
        migrations.AddField(
            model_name='quizquestion',
            name='lecture',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='courses.lecture'),
        ),
        migrations.AddField(
            model_name='quizquestion',
            name='quiz',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='courses.quiz'),
        ),
        migrations.AddField(
            model_name='quizanswer',
            name='quiz_question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='courses.quizquestion'),
        ),
        migrations.AddField(
            model_name='quiz',
            name='section',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quizzes', to='courses.section'),
        ),
        migrations.AddField(
            model_name='note',
            name='subsection',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notes', to='courses.subsection'),
        ),
        migrations.AddField(
            model_name='note',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notes', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='note',
            name='user_class',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notes', to='users.userclass'),
        ),
        migrations.AddField(
            model_name='lectureresource',
            name='lecture',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='resources', to='courses.lecture'),
        ),
        migrations.AddField(
            model_name='lecture',
            name='section',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lectures', to='courses.section'),
        ),
        migrations.AddField(
            model_name='courseview',
            name='course',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='views', to='courses.course'),
        ),
        migrations.AddField(
            model_name='courseview',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='viewed_courses', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='coursereview',
            name='course',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='courses.course'),
        ),
        migrations.AddField(
            model_name='coursereview',
            name='dislikes',
            field=models.ManyToManyField(related_name='dislikes', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='coursereview',
            name='likes',
            field=models.ManyToManyField(related_name='likes', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='coursereview',
            name='reports',
            field=models.ManyToManyField(related_name='review_reports', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='coursereview',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='course_reviews', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='coursereject',
            name='course',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rejects', to='courses.course'),
        ),
        migrations.AddField(
            model_name='coursereject',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='course_rejects', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='courseprice',
            name='currency',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pricing_tiers', to='currency.Currency'),
        ),
        migrations.AddField(
            model_name='courseannouncement',
            name='course',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='announcements', to='courses.course'),
        ),
        migrations.AddField(
            model_name='courseannouncement',
            name='seen',
            field=models.ManyToManyField(blank=True, related_name='seen_announcements', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='courseannouncement',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='course_announcements', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='course',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='courses', to='courses.category'),
        ),
        migrations.AddField(
            model_name='course',
            name='currency',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='currency.Currency'),
        ),
        migrations.AddField(
            model_name='course',
            name='pricing',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='courses.courseprice'),
        ),
        migrations.AddField(
            model_name='course',
            name='subcategory',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='courses', to='courses.subcategory'),
        ),
        migrations.AddField(
            model_name='course',
            name='topics',
            field=models.ManyToManyField(blank=True, related_name='courses', to='courses.topic'),
        ),
        migrations.AddField(
            model_name='course',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='courses', to=settings.AUTH_USER_MODEL, verbose_name='Instructor'),
        ),
        migrations.AddField(
            model_name='assignmentquestion',
            name='assignment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='courses.assignment'),
        ),
        migrations.AddField(
            model_name='assignment',
            name='lecture',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='courses.lecture'),
        ),
        migrations.AddField(
            model_name='assignment',
            name='section',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignments', to='courses.section'),
        ),
    ]
