# Generated by Django 4.2 on 2023-07-13 14:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webapp', '0002_alter_account_balance'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customers',
            name='address',
            field=models.CharField(default='No Address', max_length=250),
        ),
        migrations.AlterField(
            model_name='customers',
            name='phone',
            field=models.CharField(default='None', max_length=25),
        ),
    ]