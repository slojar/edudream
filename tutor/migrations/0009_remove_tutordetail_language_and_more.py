# Generated by Django 4.2.6 on 2024-01-17 20:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tutor', '0008_tutorlanguage_tutordetail_diploma_grade_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tutordetail',
            name='language',
        ),
        migrations.RemoveField(
            model_name='tutordetail',
            name='proficiency_test_type',
        ),
        migrations.DeleteModel(
            name='TutorLanguage',
        ),
    ]
