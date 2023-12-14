# Generated by Django 4.1.4 on 2023-03-29 12:12

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('courses', '0024_alter_courseinreviewfeedback_quiz_question_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='courseinreviewfeedback',
            name='type',
            field=models.CharField(choices=[('title', 'Title'), ('subtitle', 'Subtitle'), ('desc', 'Detail'), ('image', 'Image'), ('promo_video', 'Promo Video'), ('topics', 'Topics'), ('description', 'Description'), ('skill_level', 'Skill Level'), ('category_id', 'Category'), ('subcategory_id', 'Subcategory'), ('language', 'Language'), ('objectives', 'Objectives'), ('requirements', 'Requirements'), ('video_info', 'Video Thumbnail'), ('sections', 'Section'), ('subsections', 'Subsection'), ('questions', 'Quiz Question')], max_length=20),
        ),
        migrations.CreateModel(
            name='ReportedQnaReply',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('date_updated', models.DateTimeField(auto_now=True, db_index=True)),
                ('issue', models.CharField(max_length=200)),
                ('description', models.TextField(default='')),
                ('reply', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reports', to='courses.qnareplys')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reported_gnareply', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'reported_qna_reply',
            },
        ),
    ]
