# Generated by Django 4.2.6 on 2024-01-16 18:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0008_rename_trasaction_type_transaction_transaction_type_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='referral_code',
            field=models.CharField(default='c5b731d0', max_length=50, unique=True),
        ),
    ]
