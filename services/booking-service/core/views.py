"""Views for the booking service."""

from __future__ import annotations

from uuid import UUID

from drf_spectacular.utils import extend_schema
from ilb_common.permissions import IsClientOwner, IsStaff
from rest_framework import generics
from rest_framework import status as http_status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Booking
from core.serializers import (
    BookingApproveSerializer,
    BookingCreateSerializer,
    BookingSerializer,
    PublicBookingSerializer,
)
from core.services import scope_bookings, set_status
from core.throttling import PublicBookingIPRateThrottle


def _role(request: Request) -> str:
    value = getattr(request.user, "role", "")
    return value if isinstance(value, str) else ""


def _company_id(request: Request) -> str | None:
    value = getattr(request.user, "company_id", None)
    return str(value) if value else None


def _validated_datetime_param(request: Request, *names: str):
    for name in names:
        value = request.query_params.get(name)
        if value:
            field = BookingCreateSerializer().fields["start_time"]
            try:
                return field.run_validation(value)
            except Exception as exc:
                raise ValidationError({name: "Must be a valid ISO-8601 datetime."}) from exc
    return None


def _validated_uuid_param(request: Request, name: str) -> UUID | None:
    value = request.query_params.get(name)
    if value is None:
        return None
    try:
        return UUID(str(value))
    except ValueError as exc:
        raise ValidationError({name: "Must be a valid UUID."}) from exc


class HealthView(APIView):
    authentication_classes = ()
    permission_classes = ()

    @extend_schema(
        responses={
            200: {
                "type": "object",
                "properties": {"status": {"type": "string", "example": "ok"}},
            }
        }
    )
    def get(self, request: Request) -> Response:
        return Response({"status": "ok"})


class BookingListCreateView(generics.ListCreateAPIView):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):  # type: ignore[override]
        return scope_bookings(self.request.user)

    def get_serializer_class(self):  # type: ignore[override]
        if self.request.method == "POST":
            return BookingCreateSerializer
        return BookingSerializer

    def perform_create(self, serializer: BookingCreateSerializer) -> None:
        user = self.request.user
        role = getattr(user, "role", None)
        if role == "Client":
            company_id = getattr(user, "company_id", None)
            if company_id is None:
                raise ValidationError("Client users must be bound to a company")
        elif role in {"Staff", "Director"}:
            company_id = serializer.validated_data.get("company_id")
            if company_id is None:
                raise ValidationError("staff bookings require company_id")
        else:
            raise ValidationError("Unsupported role")

        serializer.save(
            created_by_user_id=user.id,
            created_by_role=role,
            company_id=company_id,
            is_public=False,
        )


class PublicBookingCreateView(APIView):
    authentication_classes = ()
    permission_classes = ()
    throttle_classes = [PublicBookingIPRateThrottle]

    @extend_schema(request=PublicBookingSerializer, responses={201: BookingSerializer})
    def post(self, request: Request) -> Response:
        serializer = PublicBookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        booking = Booking.objects.create(
            **data,
            created_by_user_id=None,
            created_by_role="Public",
            is_public=True,
            status=Booking.Status.PENDING,
        )
        output = BookingSerializer(booking)
        return Response(output.data, status=http_status.HTTP_201_CREATED)


class BookingDetailView(generics.RetrieveAPIView):
    serializer_class = BookingSerializer
    lookup_url_kwarg = "booking_id"
    permission_classes = [IsAuthenticated]

    def get_queryset(self):  # type: ignore[override]
        return scope_bookings(self.request.user)


class BookingApproveView(APIView):
    permission_classes = [IsAuthenticated, IsStaff]

    @extend_schema(responses={200: BookingSerializer})
    def patch(self, request: Request, booking_id: str) -> Response:
        payload = BookingApproveSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        booking = Booking.objects.get(id=booking_id)
        update_fields = []
        if "quoted_price" in payload.validated_data:
            booking.quoted_price = payload.validated_data["quoted_price"]
            update_fields.append("quoted_price")
        if "company_id" in payload.validated_data:
            booking.company_id = payload.validated_data["company_id"]
            update_fields.append("company_id")
        if "equipment_ids" in payload.validated_data:
            booking.equipment_ids = [
                str(value) for value in payload.validated_data["equipment_ids"]
            ]
            update_fields.append("equipment_ids")
        if update_fields:
            booking.save(update_fields=[*update_fields, "updated_at"])
        if booking.company_id is None:
            raise ValidationError("Approved bookings require company_id")
        if booking.quoted_price is None:
            raise ValidationError("Approved bookings require quoted_price")
        set_status(booking, Booking.Status.APPROVED)
        return Response(BookingSerializer(booking).data)


class BookingRejectView(APIView):
    permission_classes = [IsAuthenticated, IsStaff]

    @extend_schema(responses={200: BookingSerializer})
    def patch(self, request: Request, booking_id: str) -> Response:
        booking = Booking.objects.get(id=booking_id)
        set_status(booking, Booking.Status.REJECTED)
        return Response(BookingSerializer(booking).data)


class BookingCancelView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: BookingSerializer})
    def patch(self, request: Request, booking_id: str) -> Response:
        booking = Booking.objects.get(id=booking_id)
        company_id = _company_id(request)
        if _role(request) == "Client":
            owns_company = company_id is not None and str(booking.company_id) == str(company_id)
            owns_booking = str(booking.created_by_user_id) == str(request.user.id)
            if not owns_company or not owns_booking:
                return Response({"detail": "Forbidden"}, status=http_status.HTTP_403_FORBIDDEN)
        set_status(booking, Booking.Status.CANCELLED)
        return Response(BookingSerializer(booking).data)


class BookingCompleteView(APIView):
    permission_classes = [IsAuthenticated, IsStaff]

    @extend_schema(responses={200: BookingSerializer})
    def patch(self, request: Request, booking_id: str) -> Response:
        booking = Booking.objects.get(id=booking_id)
        set_status(booking, Booking.Status.COMPLETED)
        return Response(BookingSerializer(booking).data)


class BookingCalendarView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: list[dict]})
    def get(self, request: Request) -> Response:
        queryset = scope_bookings(request.user).filter(status=Booking.Status.APPROVED)
        space_id = _validated_uuid_param(request, "space_id") or _validated_uuid_param(
            request, "spaceId"
        )
        if space_id:
            queryset = queryset.filter(space_id=space_id)

        starts_before = _validated_datetime_param(request, "end", "end_time", "to")
        ends_after = _validated_datetime_param(request, "start", "start_time", "from")
        if starts_before:
            queryset = queryset.filter(start_time__lt=starts_before)
        if ends_after:
            queryset = queryset.filter(end_time__gt=ends_after)

        payload = []
        for booking in queryset.order_by("start_time"):
            if (
                _role(request) == "Client"
                and _company_id(request)
                and str(booking.company_id) != str(_company_id(request))
            ):
                continue
            payload.append(
                {
                    "id": str(booking.id),
                    "company_id": str(booking.company_id),
                    "space_id": str(booking.space_id),
                    "start_time": booking.start_time,
                    "end_time": booking.end_time,
                }
            )
        return Response(payload)


class PublicBookingCalendarView(APIView):
    authentication_classes = ()
    permission_classes = ()

    @extend_schema(responses={200: list[dict]})
    def get(self, request: Request) -> Response:
        queryset = Booking.objects.filter(
            status__in=[Booking.Status.PENDING, Booking.Status.APPROVED],
        )
        space_id = _validated_uuid_param(request, "space_id") or _validated_uuid_param(
            request, "spaceId"
        )
        if space_id:
            queryset = queryset.filter(space_id=space_id)

        starts_before = _validated_datetime_param(request, "end", "end_time", "to")
        ends_after = _validated_datetime_param(request, "start", "start_time", "from")
        if starts_before:
            queryset = queryset.filter(start_time__lt=starts_before)
        if ends_after:
            queryset = queryset.filter(end_time__gt=ends_after)

        return Response(
            [
                {
                    "id": str(booking.id),
                    "space_id": str(booking.space_id),
                    "start_time": booking.start_time,
                    "end_time": booking.end_time,
                    "status": booking.status,
                }
                for booking in queryset.order_by("start_time")
            ]
        )


class MyBookingsView(generics.ListAPIView):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated, IsClientOwner]

    def get_queryset(self):  # type: ignore[override]
        return Booking.objects.filter(company_id=self.request.user.company_id)


class MetricsView(APIView):
    """Minimal operational metrics endpoint for local demos and probes."""

    authentication_classes = ()
    permission_classes = ()

    @extend_schema(
        responses={
            200: {
                "type": "object",
                "properties": {
                    "service": {"type": "string", "example": "booking-service"},
                    "status": {"type": "string", "example": "ok"},
                    "metrics": {"type": "object"},
                },
            }
        }
    )
    def get(self, request: Request) -> Response:
        return Response({"service": "booking-service", "status": "ok", "metrics": {}})
