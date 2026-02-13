# Generated migration to make start_time and end_time optional in Exam model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),  # Replace with your latest migration
    ]

    operations = [
        migrations.AlterField(
            model_name='exam',
            name='start_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='exam',
            name='end_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
