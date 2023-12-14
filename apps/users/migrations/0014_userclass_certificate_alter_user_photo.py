# Generated by Django 4.1.4 on 2023-04-15 07:31

import apps.users.models.classes
import apps.users.models.users
import core.store.storage_backends
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0013_subscribednewslater'),
    ]

    operations = [
        migrations.AddField(
            model_name='userclass',
            name='certificate',
            field=models.FileField(blank=True, null=True, storage=core.store.storage_backends.PrivateMediaStorage(), upload_to=apps.users.models.classes.course_certificate_media),
        ),
        migrations.AlterField(
            model_name='user',
            name='photo',
            field=models.ImageField(blank=True, null=True, storage=core.store.storage_backends.PrivateMediaStorage(), upload_to=apps.users.models.users.avatar_upload_location),
        ),
    ]