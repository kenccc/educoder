"""Channels consumers — live student events + teacher dashboards."""
from __future__ import annotations

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer


class ClassroomConsumer(AsyncJsonWebsocketConsumer):
    """Per-classroom feed: teacher dashboards subscribe; students push presence."""

    group_name: str | None = None

    async def connect(self):
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close(code=4401)
            return

        self.classroom_id = int(self.scope["url_route"]["kwargs"]["classroom_id"])
        self.user = user

        if not await self._is_member(self.classroom_id, user.id):
            await self.close(code=4403)
            return

        self.group_name = f"classroom_{self.classroom_id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        await self._record_presence(True)

        await self.channel_layer.group_send(
            self.group_name,
            {"type": "classroom.event", "payload": {
                "kind": "presence",
                "student": user.username,
                "online": True,
            }},
        )

    async def disconnect(self, code):
        if not self.group_name:
            return
        user = self.scope.get("user")
        if user and user.is_authenticated:
            try:
                await self._record_presence(False)
                await self.channel_layer.group_send(
                    self.group_name,
                    {"type": "classroom.event", "payload": {
                        "kind": "presence",
                        "student": user.username,
                        "online": False,
                    }},
                )
            except Exception:
                pass
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    @database_sync_to_async
    def _record_presence(self, online: bool) -> None:
        from apps.classrooms.models import Classroom
        from apps.realtime.models import EventType
        from services.events import EventService
        try:
            classroom = Classroom.objects.get(pk=self.classroom_id)
        except Classroom.DoesNotExist:
            return
        # Only students get presence events recorded; teacher self-views
        # would otherwise spam every dashboard refresh.
        if classroom.teacher_id == self.user.id:
            return
        EventService.record(
            user=self.user,
            classroom=classroom,
            type=(EventType.PRESENCE_ONLINE if online else EventType.PRESENCE_OFFLINE).value,
        )

    async def receive_json(self, content, **kwargs):
        # Server emits real events via group_send. Client-sent payloads are
        # discarded — otherwise students could forge cheat/submission events
        # to other classroom dashboards.
        return

    async def classroom_event(self, event):
        await self.send_json(event["payload"])

    @database_sync_to_async
    def _is_member(self, classroom_id: int, user_id: int) -> bool:
        from apps.classrooms.models import Classroom, Membership
        try:
            classroom = Classroom.objects.get(pk=classroom_id, is_archived=False)
        except Classroom.DoesNotExist:
            return False
        if classroom.teacher_id == user_id:
            return True
        return Membership.objects.filter(
            classroom_id=classroom_id, student_id=user_id
        ).exists()


class AttemptConsumer(AsyncJsonWebsocketConsumer):
    """Per-attempt channel: anti-cheat events from the student's IDE."""

    group_name: str | None = None

    async def connect(self):
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close(code=4401)
            return

        self.attempt_id = int(self.scope["url_route"]["kwargs"]["attempt_id"])
        self.user = user

        ok = await self._check_membership()
        if not ok:
            await self.close(code=4403)
            return

        self.group_name = f"attempt_{self.attempt_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if not self.group_name:
            return
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        kind = (content or {}).get("kind")
        if not kind:
            return
        await self._record_event(kind, content)

    async def attempt_event(self, event):
        await self.send_json(event["payload"])

    @database_sync_to_async
    def _check_membership(self) -> bool:
        from apps.assignments.models import AssignmentAttempt
        try:
            attempt = AssignmentAttempt.objects.select_related("student").get(pk=self.attempt_id)
        except AssignmentAttempt.DoesNotExist:
            return False
        return attempt.student_id == self.user.id

    @database_sync_to_async
    def _record_event(self, kind: str, content: dict):
        from apps.assignments.models import AssignmentAttempt
        from apps.realtime.models import CheatEvent, CheatKind, EventType
        from services.events import EventService

        try:
            attempt = AssignmentAttempt.objects.get(pk=self.attempt_id)
        except AssignmentAttempt.DoesNotExist:
            return

        if kind not in CheatKind.values:
            kind = CheatKind.SUSPECT

        evt = CheatEvent.objects.create(
            attempt=attempt,
            student=attempt.student,
            kind=kind,
            payload=content,
            severity=int(content.get("severity", 1)),
        )

        attempt.cheat_event_count = (attempt.cheat_event_count or 0) + 1
        attempt.save(update_fields=["cheat_event_count"])

        # Mirror into ClassroomEvent (most CheatKind ↔ EventType slugs match;
        # rename a few divergent ones below).
        cheat_to_event = {
            CheatKind.FULLSCREEN.value: EventType.FULLSCREEN_EXIT.value,
            CheatKind.TAB_BLUR.value:   EventType.BLUR.value,
            CheatKind.CUT.value:        EventType.COPY.value,
        }
        et = cheat_to_event.get(kind, kind)
        if et not in EventType.values:
            et = EventType.SUSPECT.value
        EventService.record(
            user=attempt.student,
            assignment=attempt.assignment,
            attempt=attempt,
            type=et,
            payload={"severity": evt.severity, **(content or {})},
        )

        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer
        layer = get_channel_layer()
        if layer is None:
            return
        if attempt.assignment.classroom_id is None:
            return
        async_to_sync(layer.group_send)(
            f"classroom_{attempt.assignment.classroom_id}",
            {"type": "classroom.event", "payload": {
                "kind": "cheat",
                "student": attempt.student.username,
                "attempt_id": attempt.id,
                "assignment_id": attempt.assignment_id,
                "event": kind,
                "severity": evt.severity,
                "at": evt.occurred_at.isoformat(),
            }},
        )


# Backwards compat for existing imports
SubmissionConsumer = ClassroomConsumer
