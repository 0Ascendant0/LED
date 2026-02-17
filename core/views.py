from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.db import transaction
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import generics
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import (
    AccommodationBooking,
    ActivityTemplate,
    AirportTransfer,
    BookedActivity,
    Client,
    ClientPayments,
    FlightBooking,
    TravelContract,
    Traveler,
    TravelRequirements,
)
from .serializers import (
    AccommodationBookingSerializer,
    AdminUserCreateSerializer,
    AdminUserManageSerializer,
    AirportTransferSerializer,
    ActivityTemplateSerializer,
    BookedActivitySerializer,
    FlightBookingSerializer,
    ClientSerializer,
    TravelContractSerializer,
    ClientPaymentsSerializer,
    TravelerSerializer,
    TravelRequirementsSerializer,
    CustomTokenObtainPairSerializer,
    CurrentUserSerializer,
)
from .permissions import IsAdmin, IsAdminOrReadOnly
from django.shortcuts import render
from django.http import JsonResponse

def health(request):
    return JsonResponse({"status": "ok"})

def react_app(request):
    return render(request, "index.html")


class ClientListAPIView(generics.ListCreateAPIView):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsAdminOrReadOnly]


class ClientDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsAdminOrReadOnly]


class ClientSupplierChecklistAPIView(APIView):
    permission_classes = [IsAdminOrReadOnly]

    def _build_items(self, client_id):
        contracts = list(TravelContract.objects.filter(client_id=client_id))
        contract_ids = [contract.id for contract in contracts]

        items = []
        flights_by_contract = {}
        transfers_by_contract = {}

        for booking in AccommodationBooking.objects.filter(contract_id__in=contract_ids):
            is_confirmed = booking.status == 'confirmed'
            items.append({
                'entity_type': 'accommodation',
                'entity_id': booking.id,
                'contract_id': str(booking.contract_id),
                'supplier_name': booking.supplier_name,
                'label': f'Accommodation - {booking.supplier_name or "N/A"}',
                'is_paid': is_confirmed,
                'is_editable': False,
            })

        for booking in FlightBooking.objects.filter(contract_id__in=contract_ids):
            flights_by_contract.setdefault(str(booking.contract_id), 0)
            flights_by_contract[str(booking.contract_id)] += 1
            items.append({
                'entity_type': 'flight',
                'entity_id': booking.id,
                'contract_id': str(booking.contract_id),
                'supplier_name': booking.supplier_name,
                'label': f'Flight - {booking.supplier_name or "N/A"}',
                'is_paid': booking.is_supplier_paid,
                'is_editable': True,
            })

        for booking in BookedActivity.objects.select_related('activity').filter(contract_id__in=contract_ids):
            activity_label = (
                (booking.activity_name or '').strip()
                or (booking.activity.name if booking.activity else '')
                or 'N/A'
            )
            items.append({
                'entity_type': 'activity',
                'entity_id': booking.id,
                'contract_id': str(booking.contract_id),
                'supplier_name': booking.supplier_name,
                'label': f'Activity - {activity_label}',
                'is_paid': booking.is_supplier_paid,
                'is_editable': True,
            })

        for booking in AirportTransfer.objects.filter(contract_id__in=contract_ids):
            transfers_by_contract.setdefault(str(booking.contract_id), 0)
            transfers_by_contract[str(booking.contract_id)] += 1
            items.append({
                'entity_type': 'transfer',
                'entity_id': booking.id,
                'contract_id': str(booking.contract_id),
                'supplier_name': booking.supplier_name,
                'label': f'Airport Transfer - {booking.supplier_name or "N/A"}',
                'is_paid': booking.is_supplier_paid,
                'is_editable': True,
            })

        for contract in contracts:
            contract_id_str = str(contract.id)
            if contract.has_flight_included and not flights_by_contract.get(contract_id_str):
                items.append({
                    'entity_type': 'flight',
                    'entity_id': None,
                    'contract_id': contract_id_str,
                    'supplier_name': 'Not added',
                    'label': f'Flight - Not added yet ({contract.destination})',
                    'is_paid': False,
                    'is_editable': False,
                })
            if contract.has_airport_transfer and not transfers_by_contract.get(contract_id_str):
                items.append({
                    'entity_type': 'transfer',
                    'entity_id': None,
                    'contract_id': contract_id_str,
                    'supplier_name': 'Not added',
                    'label': f'Airport Transfer - Not added yet ({contract.destination})',
                    'is_paid': False,
                    'is_editable': False,
                })
            if contract.has_travel_insurance:
                items.append({
                    'entity_type': 'insurance',
                    'entity_id': str(contract.id),
                    'contract_id': str(contract.id),
                    'supplier_name': 'Travel Insurance',
                    'label': f'Travel Insurance - {contract.destination}',
                    'is_paid': contract.is_travel_insurance_paid,
                    'is_editable': True,
                })

        return items

    def get(self, request, pk):
        try:
            client = Client.objects.get(pk=pk)
        except Client.DoesNotExist:
            return Response({'detail': 'Client not found.'}, status=status.HTTP_404_NOT_FOUND)

        return Response(
            {
                'client_id': client.id,
                'items': self._build_items(client.id),
            },
            status=status.HTTP_200_OK,
        )

    @transaction.atomic
    def patch(self, request, pk):
        if not request.user or request.user.role != 'admin':
            return Response({'detail': 'Only admins can update supplier checklist.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            Client.objects.get(pk=pk)
        except Client.DoesNotExist:
            return Response({'detail': 'Client not found.'}, status=status.HTTP_404_NOT_FOUND)

        payload_items = request.data.get('items')
        if not isinstance(payload_items, list):
            return Response({'detail': '"items" must be a list.'}, status=status.HTTP_400_BAD_REQUEST)

        allowed_types = {'accommodation', 'flight', 'activity', 'transfer', 'insurance'}

        for item in payload_items:
            entity_type = item.get('entity_type')
            entity_id = item.get('entity_id')
            is_paid = item.get('is_paid')
            is_editable = item.get('is_editable', True)

            if not is_editable:
                continue

            if entity_type not in allowed_types:
                return Response({'detail': f'Invalid entity_type: {entity_type}'}, status=status.HTTP_400_BAD_REQUEST)
            if entity_id in (None, ''):
                return Response({'detail': 'entity_id is required for every item.'}, status=status.HTTP_400_BAD_REQUEST)
            if not isinstance(is_paid, bool):
                return Response({'detail': 'is_paid must be boolean for every item.'}, status=status.HTTP_400_BAD_REQUEST)

            if entity_type == 'accommodation':
                booking = AccommodationBooking.objects.filter(pk=entity_id, contract__client_id=pk).first()
                if not booking:
                    updated = 0
                else:
                    expected_paid = booking.status == 'confirmed'
                    if is_paid != expected_paid:
                        return Response(
                            {'detail': 'Accommodation supplier payment is automatic: confirmed bookings are paid; unconfirmed bookings are unpaid.'},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    if booking.is_supplier_paid != expected_paid:
                        AccommodationBooking.objects.filter(pk=booking.pk).update(is_supplier_paid=expected_paid)
                        booking.contract.sync_status()
                    updated = 1
            elif entity_type == 'flight':
                updated = FlightBooking.objects.filter(pk=entity_id, contract__client_id=pk).update(is_supplier_paid=is_paid)
            elif entity_type == 'activity':
                updated = BookedActivity.objects.filter(pk=entity_id, contract__client_id=pk).update(is_supplier_paid=is_paid)
            elif entity_type == 'transfer':
                updated = AirportTransfer.objects.filter(pk=entity_id, contract__client_id=pk).update(is_supplier_paid=is_paid)
            else:
                updated = TravelContract.objects.filter(pk=entity_id, client_id=pk, has_travel_insurance=True).update(is_travel_insurance_paid=is_paid)

            if updated == 0:
                return Response(
                    {'detail': f'Item not found or does not belong to client: {entity_type} ({entity_id})'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response({'items': self._build_items(pk)}, status=status.HTTP_200_OK)


class TravelContractListAPIView(generics.ListCreateAPIView):
    queryset = TravelContract.objects.all()
    serializer_class = TravelContractSerializer
    permission_classes = [IsAdminOrReadOnly]


class TravelContractDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = TravelContract.objects.all()
    serializer_class = TravelContractSerializer
    permission_classes = [IsAdminOrReadOnly]


class ClientPaymentsListAPIView(generics.ListCreateAPIView):
    queryset = ClientPayments.objects.all()
    serializer_class = ClientPaymentsSerializer
    permission_classes = [IsAdminOrReadOnly]


class ClientPaymentsDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ClientPayments.objects.all()
    serializer_class = ClientPaymentsSerializer
    permission_classes = [IsAdminOrReadOnly]


class TravelerListAPIView(generics.ListCreateAPIView):
    queryset = Traveler.objects.all()
    serializer_class = TravelerSerializer
    permission_classes = [IsAdminOrReadOnly]


class TravelerDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Traveler.objects.all()
    serializer_class = TravelerSerializer
    permission_classes = [IsAdminOrReadOnly]


# class SupplierPaymentsListAPIView(generics.ListCreateAPIView):
#     queryset = SupplierPayments.objects.all()
#     serializer_class = SupplierPaymentsSerializer
#     permission_classes = [IsAdminOrReadOnly]


# class SupplierPaymentsDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
#     queryset = SupplierPayments.objects.all()
#     serializer_class = SupplierPaymentsSerializer
#     permission_classes = [IsAdminOrReadOnly]





class TravelRequirementsListAPIView(generics.ListCreateAPIView):
    queryset = TravelRequirements.objects.all()
    serializer_class = TravelRequirementsSerializer
    permission_classes = [IsAdminOrReadOnly]


class TravelRequirementsDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = TravelRequirements.objects.all()
    serializer_class = TravelRequirementsSerializer
    permission_classes = [IsAdminOrReadOnly]


class ContractRequirementStatusAPIView(APIView):
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request, contract_id):
        try:
            contract = TravelContract.objects.get(pk=contract_id)
        except TravelContract.DoesNotExist:
            return Response({'detail': 'Contract not found.'}, status=status.HTTP_404_NOT_FOUND)

        existing = {
            req.requirement_type: req
            for req in TravelRequirements.objects.filter(contract=contract)
        }
        all_requirements = []
        for key, label in TravelRequirements.REQUIREMENT_TYPES:
            req = existing.get(key)
            all_requirements.append({
                'id': req.id if req else None,
                'contract': str(contract.id),
                'requirement_type': key,
                'requirement_label': label,
                'is_required': req.is_required if req else False,
                'status': req.status if req else 'pending',
                'is_submitted': req.is_submitted if req else False,
            })

        return Response(all_requirements, status=status.HTTP_200_OK)

    def patch(self, request, contract_id):
        if not request.user or request.user.role != 'admin':
            return Response({'detail': 'Only admins can update requirement states.'}, status=status.HTTP_403_FORBIDDEN)

        requirement_type = request.data.get('requirement_type')
        status_value = request.data.get('status', 'pending')
        is_required = request.data.get('is_required', True)

        if requirement_type not in dict(TravelRequirements.REQUIREMENT_TYPES):
            return Response({'detail': 'Invalid requirement type.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            contract = TravelContract.objects.get(pk=contract_id)
        except TravelContract.DoesNotExist:
            return Response({'detail': 'Contract not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not is_required:
            status_value = 'pending'

        requirement, _ = TravelRequirements.objects.get_or_create(
            contract=contract,
            requirement_type=requirement_type,
            defaults={
                'is_required': bool(is_required),
                'status': 'pending',
                'is_submitted': False,
            },
        )

        serializer = TravelRequirementsSerializer(
            requirement,
            data={
                'contract': str(contract.id),
                'requirement_type': requirement_type,
                'is_required': is_required,
                'status': status_value,
            },
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class CurrentUserAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = CurrentUserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminUserCreateAPIView(generics.ListCreateAPIView):
    queryset = get_user_model().objects.all().order_by('-created_at')
    permission_classes = [IsAdmin]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AdminUserCreateSerializer
        return AdminUserManageSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        response_payload = {
            'message': 'User created.',
            'user': AdminUserManageSerializer(user).data,
        }
        return Response(
            response_payload,
            status=status.HTTP_201_CREATED,
        )


class AdminUserDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = AdminUserManageSerializer
    permission_classes = [IsAdmin]

    def perform_destroy(self, instance):
        if instance.id == self.request.user.id:
            raise ValidationError({'detail': 'You cannot delete your own account.'})
        super().perform_destroy(instance)


class VerifyEmailAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        uid = request.query_params.get('uid')
        token = request.query_params.get('token')

        if not uid or not token:
            return Response({'detail': 'Missing verification parameters.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = get_user_model().objects.get(pk=user_id)
        except Exception:
            return Response({'detail': 'Invalid verification link.'}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response({'detail': 'Verification link is invalid or expired.'}, status=status.HTTP_400_BAD_REQUEST)

        if not user.is_active:
            user.is_active = True
            user.save(update_fields=['is_active'])

        return Response({'detail': 'Email verified. Account is now active.'}, status=status.HTTP_200_OK)


class ActivityBookingsAPIView(APIView):
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request):
        grouped = {}
        bookings = BookedActivity.objects.select_related('contract__client').all()

        for booking in bookings:
            name = (booking.activity_name or '').strip() or 'Unnamed Activity'
            key = name.lower()
            if key not in grouped:
                grouped[key] = {
                    'id': key,
                    'name': name,
                    'clients': [],
                    '_client_ids': set(),
                }

            client = booking.contract.client
            if client.id in grouped[key]['_client_ids']:
                continue

            grouped[key]['_client_ids'].add(client.id)
            grouped[key]['clients'].append({
                'id': client.id,
                'first_name': client.first_name,
                'last_name': client.last_name,
                'email': client.email,
                'phone': client.phone,
            })

        payload = []
        for item in grouped.values():
            item.pop('_client_ids', None)
            payload.append(item)

        return Response(payload, status=status.HTTP_200_OK)


class ActivityTemplateListAPIView(generics.ListCreateAPIView):
    queryset = ActivityTemplate.objects.all()
    serializer_class = ActivityTemplateSerializer
    permission_classes = [IsAdminOrReadOnly]


class ActivityTemplateDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ActivityTemplate.objects.all()
    serializer_class = ActivityTemplateSerializer
    permission_classes = [IsAdminOrReadOnly]


class BookedActivityListAPIView(generics.ListCreateAPIView):
    queryset = BookedActivity.objects.all()
    serializer_class = BookedActivitySerializer
    permission_classes = [IsAdminOrReadOnly]


class BookedActivityDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = BookedActivity.objects.all()
    serializer_class = BookedActivitySerializer
    permission_classes = [IsAdminOrReadOnly]


class AccommodationBookingListAPIView(generics.ListCreateAPIView):
    queryset = AccommodationBooking.objects.all()
    serializer_class = AccommodationBookingSerializer
    permission_classes = [IsAdminOrReadOnly]


class AccommodationBookingDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = AccommodationBooking.objects.all()
    serializer_class = AccommodationBookingSerializer
    permission_classes = [IsAdminOrReadOnly]


class FlightBookingListAPIView(generics.ListCreateAPIView):
    queryset = FlightBooking.objects.all()
    serializer_class = FlightBookingSerializer
    permission_classes = [IsAdminOrReadOnly]


class FlightBookingDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = FlightBooking.objects.all()
    serializer_class = FlightBookingSerializer
    permission_classes = [IsAdminOrReadOnly]


class AirportTransferListAPIView(generics.ListCreateAPIView):
    queryset = AirportTransfer.objects.all()
    serializer_class = AirportTransferSerializer
    permission_classes = [IsAdminOrReadOnly]


class AirportTransferDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = AirportTransfer.objects.all()
    serializer_class = AirportTransferSerializer
    permission_classes = [IsAdminOrReadOnly]
