# Generated by Django 4.2.6 on 2024-03-20 22:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tutor', '0028_alter_tutordetail_discipline_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='dispute',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='dispute-images'),
        ),
    ]
