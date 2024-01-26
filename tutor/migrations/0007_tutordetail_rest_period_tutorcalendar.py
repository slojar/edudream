# Generated by Django 4.2.6 on 2024-01-14 16:50

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tutor', '0006_remove_classroom_accepted_remove_classroom_completed_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='tutordetail',
            name='rest_period',
            field=models.IntegerField(default=10),
        ),
        migrations.CreateModel(
            name='TutorCalendar',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day_of_the_week', models.CharField(choices=[('0', 'Sunday'), ('1', 'Monday'), ('2', 'Tuesday'), ('3', 'Wednesday'), ('4', 'Thursday'), ('5', 'Friday'), ('6', 'Saturday')], default='mon', max_length=200)),
                ('time_from', models.TimeField(blank=True, null=True)),
                ('time_to', models.TimeField(blank=True, null=True)),
                ('status', models.CharField(choices=[('available', 'Available'), ('not_available', 'Not Available')], default='available', max_length=100)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]