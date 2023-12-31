# Generated by Django 4.1.4 on 2023-03-13 07:32

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('courses', '0011_subsectionprogress_watched_duration'),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseInReviewFeedback',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('date_updated', models.DateTimeField(auto_now=True, db_index=True)),
                ('type', models.CharField(choices=[('title', 'Title'), ('subtitle', 'Subtitle'), ('desc', 'Detail'), ('image', 'Image'), ('promo_video', 'Promo Video'), ('topics', 'Topics'), ('description', 'Description'), ('skill_level', 'Skill Level'), ('category', 'Category'), ('subcategory', 'Subcategory'), ('language', 'Language'), ('objectives', 'Objectives'), ('requirements', 'Requirements'), ('video_info', 'Video Thumbnail'), ('sections', 'Section'), ('subsections', 'Subsection'), ('questions', 'Quiz Question')], max_length=20)),
                ('message', models.TextField()),
                ('required', models.BooleanField(default=False)),
                ('type_value', models.Field()),
                ('index', models.IntegerField(default=0)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inreview_feedbacks', to='courses.course')),
                ('quiz_question', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='course_question_feedbacks', to=settings.AUTH_USER_MODEL)),
                ('section', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='course_section_feedbacks', to=settings.AUTH_USER_MODEL)),
                ('subsection', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='course_subsection_feedbacks', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='course_inreview_feedbacks', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'course_inreview_feedback',
            },
        ),
    ]
