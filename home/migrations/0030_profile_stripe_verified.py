# Generated by Django 4.2.6 on 2024-05-20 21:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0029_remove_testimonial_language'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='stripe_verified',
            field=models.BooleanField(default=False),
        ),
    ]
