# Generated by Django 4.2.6 on 2024-03-07 15:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tutor', '0022_classroom_class_type_tutorcalendar_classroom'),
    ]

    operations = [
        migrations.AddField(
            model_name='tutordetail',
            name='proficiency_test_type',
            field=models.CharField(blank=True, default='', max_length=100, null=True),
        ),
    ]