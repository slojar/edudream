# Generated by Django 4.2.6 on 2024-04-27 23:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tutor', '0032_remove_classroom_student_joined_at_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='classroom',
            name='student_complete_check',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='classroom',
            name='tutor_complete_check',
            field=models.BooleanField(default=False),
        ),
    ]
