# Generated by Django 4.2.6 on 2024-01-17 20:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0003_student_help_subject'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='note_to_tutor',
            field=models.TextField(blank=True, null=True),
        ),
    ]