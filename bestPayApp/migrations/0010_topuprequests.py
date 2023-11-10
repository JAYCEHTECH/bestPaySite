# Generated by Django 4.2.4 on 2023-11-09 13:41

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bestPayApp', '0009_mtnbundletransaction_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='TopUpRequests',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.PositiveIntegerField(blank=True, null=True)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('previous_balance', models.PositiveIntegerField(blank=True, null=True)),
                ('current_balance', models.PositiveIntegerField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]