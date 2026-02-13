from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Client, TravelContract, ClientPayments, Traveler, BookedSuppliers, SupplierPayments, Suppliers, TravelRequirements
from .serializers import ClientSerializer, TravelContractSerializer, ClientPaymentsSerializer, TravelerSerializer, BookedSuppliersSerializer, SupplierPaymentsSerializer, SuppliersSerializer, TravelRequirementsSerializer

class ClientListAPIView(APIView):

    def get(self, request):
        clients = Client.objects.all()
        serializer = ClientSerializer(clients, many = True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = ClientSerializer(data = request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class ClientDetailAPIView(APIView):

    def get(self, pk):
        client = Client.objects.get(pk=pk)
        serializer = ClientSerializer(client)
        return Response(serializer.data)
    
    def put(self, request, pk):
        client = Client.objects.get(pk=pk)
        serializer = ClientSerializer(client, data = request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status= status.HTTP_201_CREATED)
        return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)
    
    def delete(self, pk):
        client = Client.objects.get(pk=pk)
        client.delete()
        return Response(status = status.HTTP_204_NO_CONTENT)
    
class TravelContractAPIView(APIView):
    def get(self, pk):
        contract = TravelContract.objects.get(pk=pk)
        serializer = TravelContractSerializer(contract)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = TravelContractSerializer(data = request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, pk):
        contract = TravelContract.objects.get(pk=pk)
        serializer = TravelContractSerializer(contract, data = request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, pk):
        contract = TravelContract.objects.get(pk=pk)
        contract.delete
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class ClientPaymentsAPIView(APIView):
    def get(self, pk):
        payment = ClientPayments.objects.get(pk=pk)
        serializer = ClientPaymentsSerializer(payment)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = ClientPaymentsSerializer(data= request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request):
        payment = ClientPayments.objects.get(pk=pk)
        serializer = ClientPaymentsSerializer(payment, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, pk):
        payment = ClientPayments.objects.get(pk=pk)
        payment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class TravelerAPIView(APIView):
    def get(self, pk):
        payment = Traveler.objects.get(pk=pk)
        serializer = TravelerSerializer(payment)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = TravelerSerializer(data= request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request):
        payment = Traveler.objects.get(pk=pk)
        serializer = TravelerSerializer(payment, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, pk):
        payment = Traveler.objects.get(pk=pk)
        payment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class BookedSuppliersAPIView(APIView):
    def get(self, pk):
        payment = BookedSuppliers.objects.get(pk=pk)
        serializer = BookedSuppliersSerializer(payment)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = BookedSuppliersSerializer(data= request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request):
        payment = BookedSuppliers.objects.get(pk=pk)
        serializer = BookedSuppliersSerializer(payment, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, pk):
        payment = BookedSuppliers.objects.get(pk=pk)
        payment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

class SupplierPaymentsAPIView(APIView):
    def get(self, pk):
        payment = SupplierPayments.objects.get(pk=pk)
        serializer = SupplierPaymentsSerializer(payment)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = SupplierPaymentsSerializer(data= request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request):
        payment = SupplierPayments.objects.get(pk=pk)
        serializer = SupplierPaymentsSerializer(payment, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, pk):
        payment = SupplierPayments.objects.get(pk=pk)
        payment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class SuppliersAPIView(APIView):
    def get(self, pk):
        payment = Suppliers.objects.get(pk=pk)
        serializer = SuppliersSerializer(payment)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = SuppliersSerializer(data= request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request):
        payment = Suppliers.objects.get(pk=pk)
        serializer = SuppliersSerializer(payment, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, pk):
        payment = Suppliers.objects.get(pk=pk)
        payment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

class TravelRequirementsAPIView(APIView):
    def get(self, pk):
        payment = TravelRequirements.objects.get(pk=pk)
        serializer = TravelRequirementsSerializer(payment)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = TravelRequirementsSerializer(data= request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request):
        payment = TravelRequirements.objects.get(pk=pk)
        serializer = TravelRequirementsSerializer(payment, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, pk):
        payment = TravelRequirements.objects.get(pk=pk)
        payment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)\
        

