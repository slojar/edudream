# Generated by Django 4.2.6 on 2024-04-19 09:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tutor', '0030_tutordetail_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='classroom',
            name='pending_balance_paid',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='classroom',
            name='tutor_paid',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='classroom',
            name='tutor_payment_expected',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
