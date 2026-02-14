from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import generics
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import ActivityTemplate, BookedActivity, Client, TravelContract, ClientPayments, Traveler, SupplierPayments, Suppliers, TravelRequirements
from .serializers import (
    AdminUserCreateSerializer,
    AdminUserManageSerializer,
    ActivityBookedClientsSerializer,
    ActivityTemplateSerializer,
    BookedActivitySerializer,
    ClientSerializer,
    TravelContractSerializer,
    ClientPaymentsSerializer,
    TravelerSerializer,
    SupplierPaymentsSerializer,
    SuppliersSerializer,
    TravelRequirementsSerializer,
    CustomTokenObtainPairSerializer,
    CurrentUserSerializer,
)
from .permissions import IsAdmin, IsAdminOrReadOnly


class ClientListAPIView(generics.ListCreateAPIView):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsAdminOrReadOnly]


class ClientDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsAdminOrReadOnly]


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


class SupplierPaymentsListAPIView(generics.ListCreateAPIView):
    queryset = SupplierPayments.objects.all()
    serializer_class = SupplierPaymentsSerializer
    permission_classes = [IsAdminOrReadOnly]


class SupplierPaymentsDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SupplierPayments.objects.all()
    serializer_class = SupplierPaymentsSerializer
    permission_classes = [IsAdminOrReadOnly]


class SuppliersListAPIView(generics.ListCreateAPIView):
    queryset = Suppliers.objects.all()
    serializer_class = SuppliersSerializer
    permission_classes = [IsAdminOrReadOnly]


class SuppliersDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Suppliers.objects.all()
    serializer_class = SuppliersSerializer
    permission_classes = [IsAdminOrReadOnly]


class TravelRequirementsListAPIView(generics.ListCreateAPIView):
    queryset = TravelRequirements.objects.all()
    serializer_class = TravelRequirementsSerializer
    permission_classes = [IsAdminOrReadOnly]


class TravelRequirementsDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = TravelRequirements.objects.all()
    serializer_class = TravelRequirementsSerializer
    permission_classes = [IsAdminOrReadOnly]


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
        return Response(
            {
                'message': 'User created. Verification email sent.',
                'user': AdminUserManageSerializer(user).data,
            },
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


class ActivityBookingsAPIView(generics.ListAPIView):
    queryset = ActivityTemplate.objects.prefetch_related('bookedactivity_set__contract__client')
    serializer_class = ActivityBookedClientsSerializer
    permission_classes = [IsAdminOrReadOnly]


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
