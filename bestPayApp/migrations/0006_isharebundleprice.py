# Generated by Django 4.2.5 on 2023-09-13 22:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bestPayApp', '0005_payment_payment_visited'),
    ]

    operations = [
        migrations.CreateModel(
            name='IshareBundlePrice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price', models.FloatField()),
                ('bundle_volume', models.FloatField()),
            ],
        ),
    ]