# Generated by Django 4.1 on 2023-06-16 09:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bestPayApp', '0004_site'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='payment_visited',
            field=models.BooleanField(null=True),
        ),
    ]
