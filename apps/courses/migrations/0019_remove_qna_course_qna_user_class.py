# Generated by Django 4.1.4 on 2023-03-21 11:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0012_alter_order_code'),
        ('courses', '0018_note_type'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='qna',
            name='course',
        ),
        migrations.AddField(
            model_name='qna',
            name='user_class',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='qna', to='users.userclass'),
            preserve_default=False,
        ),
    ]