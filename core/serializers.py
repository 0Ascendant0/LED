from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Client, TravelContract, Traveler, TravelRequirements, SupplierPayments, Suppliers, ClientPayments

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = '__all__'

class TravelContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = TravelContract
        fields = '__all__'

class TravelerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Traveler
        fields = '__all__'

class TravelRequirementsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TravelRequirements
        fields = '__all__'

class SupplierPaymentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierPayments
        fields = '__all__'

class SuppliersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Suppliers
        fields = '__all__'

# class BookedSuppliersSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = BookedSuppliers
#         fields = '__all__'

class ClientPaymentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientPayments
        fields = '__all__'


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


