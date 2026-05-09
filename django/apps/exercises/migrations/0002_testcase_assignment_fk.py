from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("exercises", "0001_initial"),
        ("assignments", "0003_extend_assignment_and_attempt"),
    ]

    operations = [
        migrations.AddField(
            model_name="testcase",
            name="assignment",
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="custom_test_cases",
                to="assignments.assignment",
            ),
        ),
    ]
