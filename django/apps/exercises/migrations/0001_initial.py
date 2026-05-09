from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Exercise",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("slug", models.SlugField(max_length=80, unique=True)),
                ("title", models.CharField(max_length=160)),
                ("language", models.CharField(choices=[("python", "Python"), ("web", "HTML / CSS / JS")], max_length=12)),
                ("level", models.CharField(choices=[("easy", "Easy"), ("medium", "Medium"), ("hard", "Hard")], max_length=10)),
                ("prompt_md", models.TextField(help_text="Problem statement, markdown allowed")),
                ("starter_code", models.TextField(blank=True)),
                ("reference_solution", models.TextField(blank=True)),
                ("hints", models.JSONField(blank=True, default=list)),
                ("tags", models.JSONField(blank=True, default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ("language", "level", "title"),
                "indexes": [models.Index(fields=["language", "level"], name="exercises_e_languag_e6b4c1_idx")],
            },
        ),
        migrations.CreateModel(
            name="TestCase",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=120)),
                ("stdin", models.TextField(blank=True)),
                ("expected_stdout", models.TextField(blank=True)),
                ("assertions", models.JSONField(blank=True, default=list)),
                ("is_hidden", models.BooleanField(default=False)),
                ("weight", models.PositiveSmallIntegerField(default=1)),
                ("ordering", models.PositiveSmallIntegerField(default=0)),
                ("exercise", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="test_cases", to="exercises.exercise")),
                # assignment FK added in a later migration to avoid circular dep at create-time
            ],
            options={"ordering": ("ordering", "id")},
        ),
    ]
