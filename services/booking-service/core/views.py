"""Views for the booking service."""

from __future__ import annotations

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


def _role(request: Request) -> str:
    value = getattr(request.user, "role", "")
    return value if isinstance(value, str) else ""


def _company_id(request: Request) -> str | None:
    value = getattr(request.user, "company_id", None)
    return str(value) if value else None


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

    @extend_schema(request=PublicBookingSerializer, responses={201: BookingSerializer})
    def post(self, request: Request) -> Response:
        serializer = PublicBookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking = Booking.objects.create(
            **serializer.validated_data,
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
        if _role(request) == "Client" and (
            company_id is None or str(booking.company_id) != str(company_id)
        ):
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
        queryset = scope_bookings(request.user)
        payload = []
        for booking in queryset.filter(status=Booking.Status.APPROVED).order_by("start_time"):
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


class MyBookingsView(generics.ListAPIView):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated, IsClientOwner]

    def get_queryset(self):  # type: ignore[override]
        return Booking.objects.filter(company_id=self.request.user.company_id)
