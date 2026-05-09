from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("assignments", "0003_extend_assignment_and_attempt"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="CheatEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("kind", models.CharField(max_length=20, choices=[
                    ("paste", "Paste"), ("copy", "Copy"), ("cut", "Cut"),
                    ("contextmenu", "Right-click menu"), ("key_combo", "Forbidden key combo"),
                    ("devtools", "DevTools opened"), ("dom_tamper", "DOM tampered"),
                    ("fullscreen", "Left fullscreen"), ("tab_blur", "Tab/window blurred"),
                    ("visibility", "Page hidden"), ("network_open", "Window opened"),
                    ("suspect", "Suspicious activity"),
                ])),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("severity", models.PositiveSmallIntegerField(default=1)),
                ("occurred_at", models.DateTimeField(auto_now_add=True)),
                ("attempt", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="cheat_events", to="assignments.assignmentattempt")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="cheat_events", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ("-occurred_at",),
                "indexes": [
                    models.Index(fields=["attempt"], name="realtime_ch_attempt_d7c0f1_idx"),
                    models.Index(fields=["kind"], name="realtime_ch_kind_2bc491_idx"),
                ],
            },
        ),
    ]
