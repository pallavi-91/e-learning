# Generated by Django 4.1.4 on 2023-02-22 17:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0007_remove_coursereview_reports_reportedcoursereview'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='icon',
            field=models.CharField(blank=True, max_length=10),
        ),
    ]
