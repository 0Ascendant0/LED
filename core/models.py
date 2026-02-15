from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db.models import Sum
from django.db.models.functions import Coalesce
from decimal import Decimal
import uuid

# Create your models here.
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, role = "viewer", **extra_fields):
        if not email:
            raise ValueError('Email must be set!')
        email = self.normalize_email(email)
        # Keep role and is_admin consistent for legacy schema compatibility.
        extra_fields.setdefault('is_admin', role == 'admin')
        user = self.model(email = email, role = role, **extra_fields)
        user.set_password(password)
        user.save(using = self._db)
        return user 
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_admin', True)

        if extra_fields.get('role') != 'admin':
            raise ValueError('Superuser must have role=admin.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, role="admin", **extra_fields)
    
class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('viewer', 'Viewer'),
    )

    id = models.UUIDField(primary_key = True, default= uuid.uuid4, editable = False)
    email = models.EmailField(unique = True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='viewer')
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = CustomUserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def save(self, *args, **kwargs):
        if self.role == 'admin':
            self.is_admin = True
        super().save(*args, **kwargs)

    @property
    def is_staff(self):
        return self.is_admin or self.role == 'admin'
    
    def __str__(self):
        return f'{self.email} ({self.role})'
    

class Client(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    national_id_or_passport_number = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return f'{self.last_name}'
    
#add total number of travelers    
class TravelContract(models.Model):
    STATUS_CHOICES = (
        ('incomplete_payment', 'CLient Still Paying'),
        ('paid_not_settled', 'Client paid but suppliers not paid'),
        ('fully_settled', 'All paid'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    destination = models.CharField(max_length=255)
    departure_date = models.DateField()
    return_date = models.DateField()
    total_package_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    final_payment_due_date = models.DateField()
    contract_signed_date = models.DateField()
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='incomplete_payment')
    has_flight_included = models.BooleanField(default=False)
    has_airport_transfer = models.BooleanField(default=False)
    airport_transfer_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    has_travel_insurance = models.BooleanField(default=False)
    is_travel_insurance_paid = models.BooleanField(default=False)

    def _is_fully_paid(self):
        total_paid = self.clientpayments_set.aggregate(
            total=Coalesce(Sum('amount_paid'), Decimal('0.00'))
        )['total']
        return total_paid >= self.total_package_price

    def _is_supplier_checklist_complete(self):
        incomplete_supplier_payments = (
            self.bookedactivity_set.filter(is_supplier_paid=False).exists()
            or self.accommodationbooking_set.filter(is_supplier_paid=False).exists()
            or self.flightbooking_set.filter(is_supplier_paid=False).exists()
            or self.airporttransfer_set.filter(is_supplier_paid=False).exists()
        )

        insurance_incomplete = self.has_travel_insurance and not self.is_travel_insurance_paid
        return not incomplete_supplier_payments and not insurance_incomplete

    def sync_status(self):
        if not self._is_fully_paid():
            next_status = 'incomplete_payment'
        elif not self._is_supplier_checklist_complete():
            next_status = 'paid_not_settled'
        else:
            next_status = 'fully_settled'

        if self.status != next_status:
            self.status = next_status
            TravelContract.objects.filter(pk=self.pk).update(status=next_status)

    def sync_total_from_travelers(self):
        traveler_total = self.traveler_set.aggregate(total=Coalesce(Sum('price'), Decimal('0.00')))['total']
        transfer_total = self.airport_transfer_price if self.has_airport_transfer else Decimal('0.00')
        total = traveler_total + transfer_total
        if self.total_package_price != total:
            self.total_package_price = total
            TravelContract.objects.filter(pk=self.pk).update(total_package_price=total)
        self.sync_status()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.sync_status()

    def __str__(self):
        return f'{self.client.first_name} ({self.destination})'
    

class Traveler(models.Model):
    TRAVELER_TYPE = (
        ('adult', 'Adult'),
        ('child', 'Child'),
        ('infant', 'Infant'),
    )

    contract = models.ForeignKey(TravelContract, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    traveller_type = models.CharField(max_length=20, choices=TRAVELER_TYPE)
    price = models.DecimalField(max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.contract.sync_total_from_travelers()

    def delete(self, *args, **kwargs):
        contract = self.contract
        super().delete(*args, **kwargs)
        contract.sync_total_from_travelers()

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.contract.destination})'

class ClientPayments(models.Model):
    contract = models.ForeignKey(TravelContract, on_delete=models.CASCADE)
    payment_number = models.IntegerField(blank=True, null=True)
    receipt_number = models.CharField(max_length=100, unique=True)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.contract.sync_status()

    def delete(self, *args, **kwargs):
        contract = self.contract
        super().delete(*args, **kwargs)
        contract.sync_status()

    def __str__(self):
        return f'{self.contract.client.first_name} ({self.payment_date})'
    
class TravelRequirements(models.Model):
    REQUIREMENT_TYPES = (
        ('passport_photo', 'Passport photo'),
        ('passport', 'Passport'),
        ('visa', 'Visa'),
        ('birth_certificate', 'Birth Certificate'),
        ('police_clearance', 'Police Clearance'),
        ('bank_statement', 'Bank Statement'),
    )

    contract = models.ForeignKey(TravelContract, on_delete=models.CASCADE)
    requirement_type = models.CharField(max_length=50, choices=REQUIREMENT_TYPES)
    is_required = models.BooleanField(default=True)
    is_submitted = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20,
        choices=(
            ('pending', 'Pending'),
            ('submitted', 'Submitted'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ),
        default='pending',
    )

    def save(self, *args, **kwargs):
        self.is_submitted = self.status in ('submitted', 'approved')
        super().save(*args, **kwargs)

class ActivityTemplate(models.Model):
    name = models.CharField(max_length=200)
    supplier_name = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank = True)
    price_adult = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    price_child = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    price_infant =models.DecimalField(max_digits = 10, decimal_places=2, default=0)

    def __str__(self):
        return self.name

class BookedActivity(models.Model):
    # client = models.ForeignKey(Client, on_delete=models.CASCADE)
    contract = models.ForeignKey(TravelContract, on_delete=models.CASCADE)
    activity = models.ForeignKey(ActivityTemplate, on_delete=models.CASCADE)
    # date = models.DateField()
    supplier_name = models.CharField(max_length=200, blank=True)
    is_supplier_paid = models.BooleanField(default=False)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        if not self.supplier_name:
            self.supplier_name = self.activity.supplier_name
        self.total_price = self.activity.price_adult
        super().save(*args, **kwargs)
        self.contract.sync_status()

    def delete(self, *args, **kwargs):
        contract = self.contract
        super().delete(*args, **kwargs)
        contract.sync_status()
        




class AccommodationBooking(models.Model):
    MEAL_PLAN_CHOICES = (
        ('breakfast', 'Breakfast'),
        ('half_board', 'Half Board'),
        ('full_board', 'Full Board'),
    )
    ROOM_TYPE_CHOICES = (
        ('single', 'Single Room'),
        ('double', 'Double Room'),
        ('twin', 'Twin Room'),
        ('family', 'Family Room'),
    )
    STATUS_CHOICES = (
        ('not_confirmed', 'Not Confirmed'),
        ('confirmed', 'Confirmed'),
    )

    contract = models.ForeignKey(TravelContract, on_delete=models.CASCADE)
    supplier_name = models.CharField(max_length=200)
    is_supplier_paid = models.BooleanField(default=False)
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    meal_plan = models.CharField(max_length=20, choices=MEAL_PLAN_CHOICES)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPE_CHOICES)
    confirmation_number = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_confirmed')

    def save(self, *args, **kwargs):
        has_confirmation = bool((self.confirmation_number or '').strip())
        self.status = 'confirmed' if has_confirmation else 'not_confirmed'
        # Supplier payment is derived from confirmation state for accommodation.
        self.is_supplier_paid = has_confirmation
        super().save(*args, **kwargs)
        self.contract.sync_status()

    def delete(self, *args, **kwargs):
        contract = self.contract
        super().delete(*args, **kwargs)
        contract.sync_status()

    def __str__(self):
        return f'{self.contract.client.first_name} - {self.supplier_name} ({self.room_type})'


class FlightBooking(models.Model):
    contract = models.ForeignKey(TravelContract, on_delete=models.CASCADE)
    supplier_name = models.CharField(max_length=200)
    is_supplier_paid = models.BooleanField(default=False)
    flight_date = models.DateField()
    flight_number = models.CharField(max_length=30)
    departure_airport = models.CharField(max_length=120)
    arrival_airport = models.CharField(max_length=120)
    departure_time = models.TimeField(blank=True, null=True)
    arrival_time = models.TimeField(blank=True, null=True)

    def __str__(self):
        return f'{self.flight_number} ({self.departure_airport} -> {self.arrival_airport})'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.contract.sync_status()

    def delete(self, *args, **kwargs):
        contract = self.contract
        super().delete(*args, **kwargs)
        contract.sync_status()


class AirportTransfer(models.Model):
    contract = models.ForeignKey(TravelContract, on_delete=models.CASCADE)
    supplier_name = models.CharField(max_length=200)
    is_supplier_paid = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.contract.client.first_name} transfer ({self.supplier_name})'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.contract.sync_status()

    def delete(self, *args, **kwargs):
        contract = self.contract
        super().delete(*args, **kwargs)
        contract.sync_status()
