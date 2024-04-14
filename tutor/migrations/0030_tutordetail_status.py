# Generated by Django 4.2.6 on 2024-04-03 18:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tutor', '0029_dispute_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='tutordetail',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('declined', 'Declined')], default='pending', max_length=50),
        ),
    ]