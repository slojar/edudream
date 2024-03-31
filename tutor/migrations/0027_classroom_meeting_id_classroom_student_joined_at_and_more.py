# Generated by Django 4.2.6 on 2024-03-18 10:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tutor', '0026_remove_tutorcalendar_classroom_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='classroom',
            name='meeting_id',
            field=models.CharField(blank=True, max_length=300, null=True),
        ),
        migrations.AddField(
            model_name='classroom',
            name='student_joined_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='classroom',
            name='student_left_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='classroom',
            name='tutor_joined_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='classroom',
            name='tutor_left_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]