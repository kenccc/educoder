# Generated for bug fix: idempotent XP awarding.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('submissions', '0003_rename_submissions_attempt_e4d3b9_idx_submissions_attempt_5d1ca4_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='submission',
            name='xp_awarded',
            field=models.BooleanField(default=False),
        ),
    ]
