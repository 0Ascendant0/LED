from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from .views import ClientListAPIView, ClientDetailAPIView, TravelContractAPIView, ClientPaymentsAPIView, TravelerAPIView, SupplierPaymentsAPIView, SuppliersAPIView, TravelRequirementsAPIView, CustomTokenObtainPairView, CurrentUserAPIView

urlpatterns = [
    path('auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('auth/me/', CurrentUserAPIView.as_view(), name='current_user'),

    path('clients/', ClientListAPIView.as_view(), name='client_list'),
    path('client/<int:pk>/', ClientDetailAPIView.as_view(), name='client_profile'),
    path('travel_contracts/<uuid:pk>/', TravelContractAPIView.as_view(), name="travel_contracts"),
    path('client_payments/<int:pk>/', ClientPaymentsAPIView.as_view(), name="client_payments"),
    path('traveler/<int:pk>/', TravelerAPIView.as_view(), name="traveler"),
    # path('booked_suppliers/<int:pk>/', BookedSuppliersAPIView.as_view(), name="booked_suppliers"),
    path('supplier_payments/<int:pk>/', SupplierPaymentsAPIView.as_view(), name="supplier_payments"),
    path('suppliers/<int:pk>/', SuppliersAPIView.as_view(), name="suppliers"),
    path('travel_requirements/<int:pk>/', TravelRequirementsAPIView.as_view(), name="travel_requirements"),
]
