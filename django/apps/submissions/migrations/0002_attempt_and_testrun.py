from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("submissions", "0001_initial"),
        ("assignments", "0003_extend_assignment_and_attempt"),
        ("exercises", "0002_testcase_assignment_fk"),
    ]

    operations = [
        migrations.AddField(
            model_name="submission",
            name="attempt",
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="submissions",
                to="assignments.assignmentattempt",
            ),
        ),
        migrations.AddField(
            model_name="submission",
            name="passed_count",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="submission",
            name="total_count",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddIndex(
            model_name="submission",
            index=models.Index(fields=["attempt"], name="submissions_attempt_e4d3b9_idx"),
        ),
        migrations.CreateModel(
            name="TestRun",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=120)),
                ("is_hidden", models.BooleanField(default=False)),
                ("passed", models.BooleanField(default=False)),
                ("actual_stdout", models.TextField(blank=True)),
                ("expected_stdout", models.TextField(blank=True)),
                ("error", models.TextField(blank=True)),
                ("runtime_ms", models.PositiveIntegerField(blank=True, null=True)),
                ("submission", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="test_runs", to="submissions.submission")),
                ("test_case", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="runs", to="exercises.testcase")),
            ],
            options={"ordering": ("id",)},
        ),
    ]
