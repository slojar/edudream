# Generated by Django 4.2.6 on 2024-02-13 13:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0020_sitesetting_intro_call_duration'),
    ]

    operations = [
        migrations.AddField(
            model_name='paymentplan',
            name='descripttion',
            field=models.CharField(blank=True, max_length=300, null=True),
        ),
    ]
