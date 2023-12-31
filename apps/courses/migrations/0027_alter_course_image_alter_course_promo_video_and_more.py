# Generated by Django 4.1.4 on 2023-04-05 10:53

import apps.courses.models.courses
import apps.courses.models.lectures
import core.store.storage_backends
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0026_alter_courseinreviewfeedback_type_value'),
    ]

    operations = [
        migrations.AlterField(
            model_name='course',
            name='image',
            field=models.ImageField(blank=True, null=True, storage=core.store.storage_backends.PrivateMediaStorage(), upload_to=apps.courses.models.courses.course_main_media),
        ),
        migrations.AlterField(
            model_name='course',
            name='promo_video',
            field=models.FileField(blank=True, null=True, storage=core.store.storage_backends.CoursesMediaStorage(), upload_to=apps.courses.models.courses.course_main_media),
        ),
        migrations.AlterField(
            model_name='lecture',
            name='video',
            field=models.FileField(blank=True, null=True, storage=core.store.storage_backends.CoursesMediaStorage(), upload_to=apps.courses.models.lectures.course_lecture_media),
        ),
    ]
