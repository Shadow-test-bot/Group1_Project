# Generated by Django 5.1.2 on 2025-06-21 15:48

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0008_group_allow_invites_group_invite_code_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='invite_code',
            field=models.UUIDField(blank=True, default=uuid.uuid4, editable=False, null=True, unique=True),
        ),
    ]
