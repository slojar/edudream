# Generated by Django 4.2.6 on 2024-04-27 21:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tutor', '0031_classroom_pending_balance_paid_classroom_tutor_paid_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='classroom',
            name='student_joined_at',
        ),
        migrations.RemoveField(
            model_name='classroom',
            name='student_left_at',
        ),
        migrations.RemoveField(
            model_name='classroom',
            name='tutor_joined_at',
        ),
        migrations.RemoveField(
            model_name='classroom',
            name='tutor_left_at',
        ),
    ]
