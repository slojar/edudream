# Generated by Django 4.2.6 on 2024-01-03 08:10

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tutor', '0004_classroom_accepted_classroom_decline_reason'),
    ]

    operations = [
        migrations.CreateModel(
            name='Dispute',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('dispute_type', models.CharField(choices=[('payment', 'Payment'), ('student', 'Student'), ('others', 'Others')], default='payment', max_length=100)),
                ('content', models.TextField()),
                ('status', models.CharField(choices=[('open', 'Open'), ('resolved', 'Resolved')], default='open', max_length=100)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('submitted_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
