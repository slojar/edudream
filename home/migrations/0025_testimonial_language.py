# Generated by Django 4.2.6 on 2024-02-21 17:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0024_profile_otp'),
    ]

    operations = [
        migrations.AddField(
            model_name='testimonial',
            name='language',
            field=models.CharField(default='english', max_length=100),
        ),
    ]
