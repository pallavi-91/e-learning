# Generated by Django 4.1.4 on 2023-03-26 18:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0021_alter_qna_upvoted_users'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lecture',
            name='video_info',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
