"""EventService: write to ClassroomEvent and (selectively) broadcast to teacher dashboards."""
from __future__ import annotations

import logging
from typing import Any, Optional

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from apps.assignments.models import Assignment, AssignmentAttempt
from apps.classrooms.models import Classroom

logger = logging.getLogger(__name__)


class EventService:
    @staticmethod
    def record(
        *,
        user,
        type: str,
        payload: Optional[dict[str, Any]] = None,
        classroom: Optional[Classroom] = None,
        assignment: Optional[Assignment] = None,
        attempt: Optional[AssignmentAttempt] = None,
    ):
        """Persist a ClassroomEvent and (if listed in BROADCAST_EVENT_TYPES) push to channel.

        Backfills classroom/assignment from attempt when omitted.
        """
        from apps.realtime.models import (
            BROADCAST_EVENT_TYPES,
            ClassroomEvent,
            EventType,
        )

        if attempt is not None:
            assignment = assignment or attempt.assignment
        if assignment is not None and classroom is None and assignment.classroom_id:
            classroom = assignment.classroom

        if type not in EventType.values:
            logger.warning("EventService.record: unknown type %r — coercing to suspect", type)
            type = EventType.SUSPECT.value

        evt = ClassroomEvent.objects.create(
            classroom=classroom,
            assignment=assignment,
            attempt=attempt,
            user=user,
            type=type,
            payload=payload or {},
        )

        if type in BROADCAST_EVENT_TYPES and classroom is not None:
            EventService._broadcast(classroom, evt)
        return evt

    @staticmethod
    def _broadcast(classroom: Classroom, evt) -> None:
        layer = get_channel_layer()
        if layer is None:
            return
        try:
            async_to_sync(layer.group_send)(
                f"classroom_{classroom.id}",
                {
                    "type": "classroom.event",
                    "payload": {
                        "kind": "event",
                        "event_type": evt.type,
                        "student": evt.user.username,
                        "user_id": evt.user_id,
                        "assignment_id": evt.assignment_id,
                        "attempt_id": evt.attempt_id,
                        "payload": evt.payload,
                        "at": evt.created_at.isoformat(),
                    },
                },
            )
        except Exception:
            logger.exception("EventService broadcast failed")

    @staticmethod
    def broadcast_status(student_status) -> None:
        """Push a StudentStatus change to the classroom dashboard channel."""
        if student_status.classroom_id is None:
            return
        layer = get_channel_layer()
        if layer is None:
            return
        try:
            async_to_sync(layer.group_send)(
                f"classroom_{student_status.classroom_id}",
                {
                    "type": "classroom.event",
                    "payload": {
                        "kind": "status_change",
                        "user_id": student_status.student_id,
                        "student": student_status.student.username,
                        "status": student_status.status,
                        "stuck_score": student_status.stuck_score,
                        "progress": student_status.progress,
                        "last_activity": student_status.last_activity.isoformat() if student_status.last_activity else None,
                    },
                },
            )
        except Exception:
            logger.exception("EventService.broadcast_status failed")
