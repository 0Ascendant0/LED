from rest_framework import serializers
from .models import Client, TravelContract, Traveler, TravelRequirements, SupplierPayments, Suppliers, BookedSuppliers, ClientPayments

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

class BookedSuppliersSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookedSuppliers
        fields = '__all__'

class ClientPaymentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientPayments
        fields = '__all__'


