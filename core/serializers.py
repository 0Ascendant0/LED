from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from decimal import Decimal
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

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = '__all__'

    def validate(self, attrs):
        national_id = attrs.get(
            'national_id_or_passport_number',
            getattr(self.instance, 'national_id_or_passport_number', None),
        )
        cleaned_national_id = (national_id or '').strip()
        if not cleaned_national_id:
            raise serializers.ValidationError(
                {'national_id_or_passport_number': 'National ID/Passport Number is required.'}
            )
        attrs['national_id_or_passport_number'] = cleaned_national_id
        return attrs

    def validate_phone(self, value):
        cleaned = ''.join(value.split())
        if len(cleaned) < 7 or len(cleaned) > 15:
            raise serializers.ValidationError('Phone number must be between 7 and 15 characters.')
        return cleaned

class TravelContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = TravelContract
        fields = '__all__'
        read_only_fields = ('total_package_price', 'status')

    def validate(self, attrs):
        instance = getattr(self, 'instance', None)
        departure_date = attrs.get('departure_date', getattr(instance, 'departure_date', None))
        return_date = attrs.get('return_date', getattr(instance, 'return_date', None))
        final_payment_due_date = attrs.get(
            'final_payment_due_date',
            getattr(instance, 'final_payment_due_date', None),
        )
        contract_signed_date = attrs.get(
            'contract_signed_date',
            getattr(instance, 'contract_signed_date', None),
        )
        has_flight_included = attrs.get(
            'has_flight_included',
            getattr(instance, 'has_flight_included', False),
        )
        has_airport_transfer = attrs.get(
            'has_airport_transfer',
            getattr(instance, 'has_airport_transfer', False),
        )
        airport_transfer_price = attrs.get(
            'airport_transfer_price',
            getattr(instance, 'airport_transfer_price', Decimal('0.00')),
        )

        if departure_date and return_date and return_date < departure_date:
            raise serializers.ValidationError({'return_date': 'Return date cannot be before departure date.'})

        if departure_date and final_payment_due_date and final_payment_due_date > departure_date:
            raise serializers.ValidationError(
                {'final_payment_due_date': 'Final payment due date cannot be after departure date.'}
            )

        if departure_date and contract_signed_date and contract_signed_date > departure_date:
            raise serializers.ValidationError(
                {'contract_signed_date': 'Contract signed date cannot be after departure date.'}
            )

        if has_airport_transfer and not has_flight_included:
            raise serializers.ValidationError(
                {'has_airport_transfer': 'Airport transfer can only be enabled when flight is included.'}
            )

        if airport_transfer_price is not None and airport_transfer_price < Decimal('0.00'):
            raise serializers.ValidationError(
                {'airport_transfer_price': 'Airport transfer price cannot be negative.'}
            )

        if not has_airport_transfer:
            attrs['airport_transfer_price'] = Decimal('0.00')

        return attrs

    def create(self, validated_data):
        instance = super().create(validated_data)
        instance.sync_total_from_travelers()
        return instance

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        instance.sync_total_from_travelers()
        return instance

class TravelerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Traveler
        fields = '__all__'

    def validate_price(self, value):
        if value < Decimal('0.00'):
            raise serializers.ValidationError('Traveler price cannot be negative.')
        return value

class TravelRequirementsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TravelRequirements
        fields = '__all__'

    def validate(self, attrs):
        contract = attrs.get('contract', getattr(self.instance, 'contract', None))
        requirement_type = attrs.get('requirement_type', getattr(self.instance, 'requirement_type', None))
        queryset = TravelRequirements.objects.filter(contract=contract, requirement_type=requirement_type)

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if contract and requirement_type and queryset.exists():
            raise serializers.ValidationError(
                {'requirement_type': 'This requirement type already exists for the selected contract.'}
            )

        status_value = attrs.get('status', getattr(self.instance, 'status', 'pending'))
        if status_value in ('submitted', 'approved'):
            attrs['is_submitted'] = True
        elif status_value in ('pending', 'rejected'):
            attrs['is_submitted'] = False

        return attrs





# class BookedSuppliersSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = BookedSuppliers
#         fields = '__all__'

class ClientPaymentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientPayments
        fields = '__all__'
        extra_kwargs = {
            'payment_number': {'required': False, 'allow_null': True},
        }

    def create(self, validated_data):
        contract = validated_data['contract']
        if validated_data.get('payment_number') in (None, 0):
            latest_payment_number = (
                ClientPayments.objects.filter(contract=contract)
                .order_by('-payment_number')
                .values_list('payment_number', flat=True)
                .first()
            ) or 0
            validated_data['payment_number'] = latest_payment_number + 1
        return super().create(validated_data)

    def validate(self, attrs):
        instance = getattr(self, 'instance', None)
        contract = attrs.get('contract', getattr(instance, 'contract', None))
        payment_number = attrs.get('payment_number', getattr(instance, 'payment_number', None))
        amount_paid = attrs.get('amount_paid', getattr(instance, 'amount_paid', None))
        payment_date = attrs.get('payment_date', getattr(instance, 'payment_date', None))

        if payment_number is not None and payment_number <= 0:
            raise serializers.ValidationError({'payment_number': 'Payment number must be greater than zero.'})

        if amount_paid is not None and amount_paid <= Decimal('0.00'):
            raise serializers.ValidationError({'amount_paid': 'Amount paid must be greater than zero.'})

        if contract and payment_date and payment_date < contract.contract_signed_date:
            raise serializers.ValidationError({'payment_date': 'Payment date cannot be before contract signed date.'})

        if contract and payment_number is not None:
            queryset = ClientPayments.objects.filter(contract=contract, payment_number=payment_number)
            if instance:
                queryset = queryset.exclude(pk=instance.pk)
            if queryset.exists():
                raise serializers.ValidationError(
                    {'payment_number': 'This payment number already exists for the selected contract.'}
                )

        if contract and amount_paid is not None:
            queryset = ClientPayments.objects.filter(contract=contract)
            if instance:
                queryset = queryset.exclude(pk=instance.pk)

            total_paid = sum(payment.amount_paid for payment in queryset)
            if total_paid + amount_paid > contract.total_package_price:
                raise serializers.ValidationError(
                    {'amount_paid': 'Total client payments cannot exceed the total package price.'}
                )

        return attrs


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['role'] = user.role
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = {
            'id': str(self.user.id),
            'email': self.user.email,
            'role': self.user.role,
        }
        return data


class CurrentUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('id', 'email', 'role', 'is_active', 'created_at')


class AdminUserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = get_user_model()
        fields = ('id', 'email', 'password', 'role', 'is_active', 'created_at')
        read_only_fields = ('id', 'created_at')

    def create(self, validated_data):
        password = validated_data.pop('password')
        role = validated_data.pop('role', 'viewer')
        user = get_user_model().objects.create_user(
            password=password,
            role=role,
            is_active=True,
            **validated_data,
        )
        return user


class AdminUserManageSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('id', 'email', 'role', 'is_active', 'created_at')
        read_only_fields = ('id', 'created_at')


class AccommodationBookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccommodationBooking
        fields = '__all__'
        read_only_fields = ('status',)

    def validate(self, attrs):
        check_in = attrs.get('check_in_date', getattr(self.instance, 'check_in_date', None))
        check_out = attrs.get('check_out_date', getattr(self.instance, 'check_out_date', None))

        if check_in and check_out and check_out < check_in:
            raise serializers.ValidationError({'check_out_date': 'Check-out date cannot be before check-in date.'})

        return attrs


class FlightBookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = FlightBooking
        fields = '__all__'

    def validate(self, attrs):
        return attrs


class AirportTransferSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirportTransfer
        fields = '__all__'

    def validate(self, attrs):
        return attrs


class ActivityBookedClientsSerializer(serializers.ModelSerializer):
    clients = serializers.SerializerMethodField()

    class Meta:
        model = ActivityTemplate
        fields = ('id', 'name', 'clients')

    def get_clients(self, obj):
        client_map = {}
        for booking in obj.bookedactivity_set.all():
            client = booking.contract.client
            client_map[client.id] = {
                'id': client.id,
                'first_name': client.first_name,
                'last_name': client.last_name,
                'email': client.email,
                'phone': client.phone,
            }
        return list(client_map.values())


class ActivityTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityTemplate
        fields = '__all__'


class BookedActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = BookedActivity
        fields = ('id', 'contract', 'activity', 'supplier_name', 'is_supplier_paid', 'total_price')
        read_only_fields = ('total_price',)
