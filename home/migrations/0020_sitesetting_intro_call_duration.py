# Generated by Django 4.2.6 on 2024-02-11 12:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0019_profile_stripe_connect_account_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesetting',
            name='intro_call_duration',
            field=models.IntegerField(blank=True, default=15, null=True),
        ),
    ]
