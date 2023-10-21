# Generated by Django 4.2.5 on 2023-10-20 20:33

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('bestPayApp', '0007_rename_isharebundleprice_mtnbundleprice_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='site',
            name='ishare_status',
            field=models.CharField(choices=[('Active', 'Active'), ('Inactive', 'Inactive')], default='Active', max_length=200),
        ),
        migrations.AlterField(
            model_name='payment',
            name='transaction_date',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
