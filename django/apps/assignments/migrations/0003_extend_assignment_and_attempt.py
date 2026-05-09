from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("assignments", "0002_initial"),
        ("exercises", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ---- Drop columns no longer in the model ----
        migrations.RemoveField(model_name="assignment", name="expected_stdout"),

        # ---- Update language choices (web added) ----
        migrations.AlterField(
            model_name="assignment",
            name="language",
            field=models.CharField(
                choices=[("python", "Python"), ("web", "HTML / CSS / JS")],
                default="python",
                max_length=12,
            ),
        ),
        # ---- New fields ----
        migrations.AddField(
            model_name="assignment",
            name="exercise",
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="assignments",
                to="exercises.exercise",
            ),
        ),
        migrations.AddField(
            model_name="assignment",
            name="level",
            field=models.CharField(blank=True, default="", max_length=10),
        ),
        migrations.AddField(
            model_name="assignment",
            name="start_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="assignment",
            name="time_limit_minutes",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="assignment",
            name="strict_mode",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="assignment",
            name="max_attempts",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="assignment",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),

        # ---- AssignmentAttempt ----
        migrations.CreateModel(
            name="AssignmentAttempt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("ended_at", models.DateTimeField(blank=True, null=True)),
                ("status", models.CharField(
                    choices=[("active", "Active"), ("submitted", "Submitted"), ("expired", "Expired"), ("terminated", "Terminated")],
                    default="active", max_length=12,
                )),
                ("cheat_event_count", models.PositiveIntegerField(default=0)),
                ("submission_count", models.PositiveIntegerField(default=0)),
                ("best_score", models.PositiveIntegerField(default=0)),
                ("is_correct", models.BooleanField(default=False)),
                ("assignment", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attempts", to="assignments.assignment")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attempts", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ("-started_at",),
                "indexes": [
                    models.Index(fields=["assignment", "student"], name="assignments_assignm_a4f7d3_idx"),
                    models.Index(fields=["status"], name="assignments_status_8d3e91_idx"),
                ],
            },
        ),
    ]
