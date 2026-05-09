# Generated for bug fix: prevent duplicate concurrent active attempts.

from django.db import migrations, models


def _expire_duplicate_active_attempts(apps, schema_editor):
    """Older builds could create >1 ACTIVE attempt per (assignment, student)
    due to a race in AttemptService.get_or_create. Keep the most recent;
    mark the rest EXPIRED so the unique constraint can be applied."""
    AssignmentAttempt = apps.get_model('assignments', 'AssignmentAttempt')
    seen = set()
    duplicates = []
    for attempt in (
        AssignmentAttempt.objects
        .filter(status='active')
        .order_by('assignment_id', 'student_id', '-started_at')
    ):
        key = (attempt.assignment_id, attempt.student_id)
        if key in seen:
            duplicates.append(attempt.pk)
        else:
            seen.add(key)
    if duplicates:
        AssignmentAttempt.objects.filter(pk__in=duplicates).update(status='expired')


class Migration(migrations.Migration):

    dependencies = [
        ('assignments', '0005_assignment_solo_owner_alter_assignment_classroom'),
    ]

    operations = [
        migrations.RunPython(
            _expire_duplicate_active_attempts,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.AddConstraint(
            model_name='assignmentattempt',
            constraint=models.UniqueConstraint(
                fields=('assignment', 'student'),
                condition=models.Q(status='active'),
                name='unique_active_attempt_per_student',
            ),
        ),
    ]
