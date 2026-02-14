from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from decimal import Decimal
from .models import (
    ActivityTemplate,
    BookedActivity,
    Client,
    ClientPayments,
    SupplierPayments,
    Suppliers,
    TravelContract,
    Traveler,
    TravelRequirements,
)

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = '__all__'

    def validate_phone(self, value):
        cleaned = value.strip()
        if len(cleaned) < 7 or len(cleaned) > 15:
            raise serializers.ValidationError('Phone number must be between 7 and 15 characters.')
        return cleaned

class TravelContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = TravelContract
        fields = '__all__'

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

        return attrs

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

        return attrs

class SupplierPaymentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierPayments
        fields = '__all__'

    def validate(self, attrs):
        instance = getattr(self, 'instance', None)
        booked_activity = attrs.get('booked_activity', getattr(instance, 'booked_activity', None))
        supplier = attrs.get('supplier', getattr(instance, 'supplier', None))
        amount_paid = attrs.get('amount_paid', getattr(instance, 'amount_paid', None))
        payment_date = attrs.get('payment_date', getattr(instance, 'payment_date', None))

        if amount_paid is not None and amount_paid <= Decimal('0.00'):
            raise serializers.ValidationError({'amount_paid': 'Supplier payment amount must be greater than zero.'})

        if booked_activity and supplier and booked_activity.activity.supplier_id and supplier.id != booked_activity.activity.supplier_id:
            raise serializers.ValidationError({'supplier': 'Supplier must match the booked activity supplier.'})

        if booked_activity and payment_date and payment_date < booked_activity.contract.contract_signed_date:
            raise serializers.ValidationError(
                {'payment_date': 'Supplier payment date cannot be before contract signed date.'}
            )

        if booked_activity and amount_paid is not None:
            queryset = SupplierPayments.objects.filter(booked_activity=booked_activity)
            if instance:
                queryset = queryset.exclude(pk=instance.pk)

            already_paid = sum(payment.amount_paid for payment in queryset)
            if already_paid + amount_paid > booked_activity.total_price:
                raise serializers.ValidationError(
                    {'amount_paid': 'Supplier payments cannot exceed the booked activity total price.'}
                )

        return attrs

class SuppliersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Suppliers
        fields = '__all__'

    def validate(self, attrs):
        instance = getattr(self, 'instance', None)
        phone = attrs.get('phone', getattr(instance, 'phone', None))
        email = attrs.get('email', getattr(instance, 'email', None))

        if not phone and not email:
            raise serializers.ValidationError('Provide at least one supplier contact: phone or email.')

        if phone:
            cleaned = phone.strip()
            if len(cleaned) < 7 or len(cleaned) > 15:
                raise serializers.ValidationError({'phone': 'Phone number must be between 7 and 15 characters.'})
            attrs['phone'] = cleaned

        return attrs

# class BookedSuppliersSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = BookedSuppliers
#         fields = '__all__'

class ClientPaymentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientPayments
        fields = '__all__'

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
        request = self.context.get('request')
        password = validated_data.pop('password')
        role = validated_data.get('role', 'viewer')
        user = get_user_model().objects.create_user(
            password=password,
            role=role,
            is_active=False,
            **validated_data,
        )

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        if request:
            verify_url = request.build_absolute_uri(f'/api/auth/verify-email/?uid={uid}&token={token}')
        else:
            verify_url = f'http://127.0.0.1:8000/api/auth/verify-email/?uid={uid}&token={token}'

        subject = "Verify your LED Travel and Tours account"
        message = (
            "Your account was created by an administrator.\n\n"
            "Please verify your email to activate your account:\n"
            f"{verify_url}\n\n"
            "If you did not expect this, contact support."
        )

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception as email_error:
            user.delete()
            raise ValidationError({'email': f'Failed to send verification email: {email_error}'})

        return user


class AdminUserManageSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('id', 'email', 'role', 'is_active', 'created_at')
        read_only_fields = ('id', 'created_at')


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
        fields = '__all__'

    def validate(self, attrs):
        quantity_adult = attrs.get('quantity_adult', 0)
        quantity_child = attrs.get('quantity_child', 0)
        quantity_infant = attrs.get('quantity_infant', 0)

        if quantity_adult + quantity_child + quantity_infant <= 0:
            raise serializers.ValidationError(
                {'quantity_adult': 'At least one traveler quantity must be greater than zero.'}
            )

        return attrs


