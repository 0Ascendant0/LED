from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
import uuid

# Create your models here.
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, role = "viewer", **extra_fields):
        if not email:
            raise ValueError('Email must be set!')
        email = self.normalize_email(email)
        user = self.model(email = email, role = role, **extra_fields)
        user.set_password(password)
        user.save(using = self._db)
        return user 
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

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
    created_at = models.DateTimeField(auto_now_add=True)

    objects = CustomUserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    @property
    def is_staff(self):
        return self.role == 'admin'
    
    def __str__(self):
        return f'{self.email} ({self.role})'
    

class Client(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
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
    total_package_price = models.DecimalField(max_digits=12, decimal_places=2)
    final_payment_due_date = models.DateField()
    contract_signed_date = models.DateField()
    status = models.CharField(max_length=30, choices=STATUS_CHOICES)

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

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.contract.destination})'

class ClientPayments(models.Model):
    contract = models.ForeignKey(TravelContract, on_delete=models.CASCADE)
    payment_number = models.IntegerField()
    receipt_number = models.CharField(max_length=100, unique=True)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField()

    def __str__(self):
        return f'{self.contract.client.first_name} ({self.payment_date})'
    
class Suppliers(models.Model):
    SUPPLIER_TYPE = (
        ('flight','Flight'),
        ('insurance', 'Insurance'),
        ('accommodation', 'Accommodation'),
        ('activity', 'Activity'), 
        ('transfer', 'Airport transfer'),
    )
    name = models.CharField(max_length=200)
    supplier_type = models.CharField(max_length=100, choices=SUPPLIER_TYPE)
    phone = models.CharField(max_length=15, null=True)
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return f'{self.name} ({self.supplier_type})'
    
# class BookedSuppliers(models.Model):
#     contract = models.ForeignKey(TravelContract, on_delete=models.CASCADE)
#     supplier = models.ForeignKey(Suppliers, on_delete=models.CASCADE)
#     description = models.TextField()
#     total_cost = models.DecimalField(max_digits=12, decimal_places=2)
#     is_paid = models.BooleanField(default=False)

#check on refference number


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

class ActivityTemplate(models.Model):
    name = models.CharField(max_length=200)
    supplier = models.ForeignKey(Suppliers, on_delete=models.SET_NULL, null=True)
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
    quantity_adult = models.PositiveIntegerField(default=0)
    quantity_child = models.PositiveIntegerField(default=0)
    quantity_infant = models.PositiveIntegerField(default=0)

    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        self.total_price = ((self.activity.price_adult * self.quantity_adult) + (self.activity.price_infant * self.quantity_infant) + (self.activity.price_child * self.quantity_child))
        super().save(*args, **kwargs)
        

# Confirm on Refference #
class SupplierPayments(models.Model):
    # booking = models.ForeignKey(BookedSuppliers, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Suppliers, on_delete=models.CASCADE)
    booked_activity = models.ForeignKey(BookedActivity, on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField()
    reference_number = models.CharField(max_length=100)
