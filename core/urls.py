from django.urls import path
from .views import ClientListAPIView, ClientDetailAPIView, TravelContractAPIView, ClientPaymentsAPIView, TravelerAPIView, BookedSuppliersAPIView, SupplierPaymentsAPIView, SuppliersAPIView, TravelRequirementsAPIView

urlpatterns = [
    path('clients/', ClientListAPIView.as_view(), name='client_list'),
    path('client/<int:pk>/', ClientDetailAPIView.as_view, name='client_profile'),
    path('travel_contracts/<int:pk>/', TravelContractAPIView.as_view(), name="travel_contracts"),
    path('client_payments/<int:pk>/', ClientPaymentsAPIView.as_view(), name="client_payments"),
    path('traveler/<int:pk>/', TravelerAPIView.as_view(), name="traveler"),
    path('booked_suppliers/<int:pk>/', BookedSuppliersAPIView.as_view(), name="booked_suppliers"),
    path('supplier_payments/<int:pk>/', SupplierPaymentsAPIView.as_view(), name="supplier_payments"),
    path('suppliers/<int:pk>/', SuppliersAPIView.as_view(), name="suppliers"),
    path('travel_requirements/<int:pk>/', TravelRequirementsAPIView.as_view(), name="travel_requirements"),
]
