from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from .views import (
    ClientListAPIView,
    ClientDetailAPIView,
    ClientSupplierChecklistAPIView,
    TravelContractListAPIView,
    TravelContractDetailAPIView,
    ClientPaymentsListAPIView,
    ClientPaymentsDetailAPIView,
    TravelerListAPIView,
    TravelerDetailAPIView,
    
    
    TravelRequirementsListAPIView,
    TravelRequirementsDetailAPIView,
    ContractRequirementStatusAPIView,
    ActivityBookingsAPIView,
    ActivityTemplateListAPIView,
    ActivityTemplateDetailAPIView,
    BookedActivityListAPIView,
    BookedActivityDetailAPIView,
    AccommodationBookingListAPIView,
    AccommodationBookingDetailAPIView,
    FlightBookingListAPIView,
    FlightBookingDetailAPIView,
    AirportTransferListAPIView,
    AirportTransferDetailAPIView,
    AdminUserCreateAPIView,
    AdminUserDetailAPIView,
    VerifyEmailAPIView,
    CustomTokenObtainPairView,
    CurrentUserAPIView,
)

urlpatterns = [
    path('auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('auth/me/', CurrentUserAPIView.as_view(), name='current_user'),
    path('auth/users/', AdminUserCreateAPIView.as_view(), name='admin_user_create'),
    path('auth/users/<uuid:pk>/', AdminUserDetailAPIView.as_view(), name='admin_user_detail'),
    path('auth/verify-email/', VerifyEmailAPIView.as_view(), name='verify_email'),
    path('activity-bookings/', ActivityBookingsAPIView.as_view(), name='activity_bookings'),
    path('activity-templates/', ActivityTemplateListAPIView.as_view(), name='activity_template_list'),
    path('activity-templates/<int:pk>/', ActivityTemplateDetailAPIView.as_view(), name='activity_template_detail'),
    path('booked-activities/', BookedActivityListAPIView.as_view(), name='booked_activity_list'),
    path('booked-activities/<int:pk>/', BookedActivityDetailAPIView.as_view(), name='booked_activity_detail'),
    path('accommodation-bookings/', AccommodationBookingListAPIView.as_view(), name='accommodation_booking_list'),
    path('accommodation-bookings/<int:pk>/', AccommodationBookingDetailAPIView.as_view(), name='accommodation_booking_detail'),
    path('flight-bookings/', FlightBookingListAPIView.as_view(), name='flight_booking_list'),
    path('flight-bookings/<int:pk>/', FlightBookingDetailAPIView.as_view(), name='flight_booking_detail'),
    path('airport-transfers/', AirportTransferListAPIView.as_view(), name='airport_transfer_list'),
    path('airport-transfers/<int:pk>/', AirportTransferDetailAPIView.as_view(), name='airport_transfer_detail'),

    path('clients/', ClientListAPIView.as_view(), name='client_list'),
    path('clients/<int:pk>/', ClientDetailAPIView.as_view(), name='client_detail'),
    path('clients/<int:pk>/supplier-checklist/', ClientSupplierChecklistAPIView.as_view(), name='client_supplier_checklist'),
    path('travel-contracts/', TravelContractListAPIView.as_view(), name='travel_contract_list'),
    path('travel-contracts/<uuid:pk>/', TravelContractDetailAPIView.as_view(), name='travel_contract_detail'),
    path('client-payments/', ClientPaymentsListAPIView.as_view(), name='client_payment_list'),
    path('client-payments/<int:pk>/', ClientPaymentsDetailAPIView.as_view(), name='client_payment_detail'),
    path('travelers/', TravelerListAPIView.as_view(), name='traveler_list'),
    path('travelers/<int:pk>/', TravelerDetailAPIView.as_view(), name='traveler_detail'),
    # Removed supplier payments endpoints
    # Removed supplier endpoints
    path('travel-requirements/', TravelRequirementsListAPIView.as_view(), name='travel_requirement_list'),
    path('travel-requirements/<int:pk>/', TravelRequirementsDetailAPIView.as_view(), name='travel_requirement_detail'),
    path('travel-contracts/<uuid:contract_id>/requirements/', ContractRequirementStatusAPIView.as_view(), name='contract_requirement_status'),

    # Legacy aliases (kept for backward compatibility)
    path('client/<int:pk>/', ClientDetailAPIView.as_view(), name='client_profile_legacy'),
    path('travel_contracts/<uuid:pk>/', TravelContractDetailAPIView.as_view(), name='travel_contracts_legacy'),
    path('client_payments/<int:pk>/', ClientPaymentsDetailAPIView.as_view(), name='client_payments_legacy'),
    path('traveler/<int:pk>/', TravelerDetailAPIView.as_view(), name='traveler_legacy'),
    # Removed supplier payments legacy endpoint
    path('travel_requirements/<int:pk>/', TravelRequirementsDetailAPIView.as_view(), name='travel_requirements_legacy'),
]
