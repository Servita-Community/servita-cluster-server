# Generated by Django 5.1.2 on 2024-11-11 19:44

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0004_devicestatus_ffmpeg_pid_and_more"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="devicestatus",
            constraint=models.UniqueConstraint(
                condition=models.Q(("stream_id__isnull", False)),
                fields=("stream_id",),
                name="unique_stream_id",
            ),
        ),
    ]
