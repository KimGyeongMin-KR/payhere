# Generated by Django 4.1.5 on 2023-01-23 21:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='age',
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
    ]