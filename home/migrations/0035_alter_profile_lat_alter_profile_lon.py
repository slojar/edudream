# Generated by Django 4.2.6 on 2024-09-21 22:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0034_profile_lat_profile_lon'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='lat',
            field=models.CharField(default='0', max_length=100),
        ),
        migrations.AlterField(
            model_name='profile',
            name='lon',
            field=models.CharField(default='0', max_length=100),
        ),
    ]
