from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver


# ─── USER PROFILE ────────────────────────────────────────────────────────────

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('advisor', 'Service Advisor'),
        ('owner', 'Dealership Owner'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    phone = models.CharField(max_length=20, blank=True)
    dealership_name = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.role})"

    def is_customer(self):
        return self.role == 'customer'

    def is_advisor(self):
        return self.role == 'advisor'

    def is_owner(self):
        return self.role == 'owner'

    def is_staff_member(self):
        return self.role in ['advisor', 'owner']


# ─── VEHICLE ─────────────────────────────────────────────────────────────────

class Vehicle(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vehicles')
    make = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    year = models.IntegerField()
    vin = models.CharField(max_length=17, blank=True)
    license_plate = models.CharField(max_length=20, blank=True)
    current_mileage = models.IntegerField(default=0)
    color = models.CharField(max_length=30, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.year} {self.make} {self.model}"


# ─── APPOINTMENT ─────────────────────────────────────────────────────────────

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    SERVICE_CHOICES = [
        ('oil_change', 'Oil Change'),
        ('tire_rotation', 'Tire Rotation'),
        ('brake_inspection', 'Brake Inspection'),
        ('transmission', 'Transmission Service'),
        ('annual_inspection', 'Annual Inspection'),
        ('engine_diagnostic', 'Engine Diagnostic'),
        ('ac_service', 'A/C Service'),
        ('battery_replacement', 'Battery Replacement'),
        ('other', 'Other'),
    ]

    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='appointments')
    advisor = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_appointments'
    )
    service_type = models.CharField(max_length=50, choices=SERVICE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    date = models.DateField()
    time = models.TimeField()
    notes = models.TextField(blank=True)
    estimated_cost = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    actual_cost = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date', 'time']

    def __str__(self):
        return f"{self.customer.get_full_name()} - {self.get_service_type_display()} on {self.date}"

    def is_today(self):
        return self.date == timezone.now().date()


# ─── SERVICE RECORD ──────────────────────────────────────────────────────────

class ServiceRecord(models.Model):
    appointment = models.OneToOneField(
        Appointment, on_delete=models.CASCADE,
        related_name='service_record', null=True, blank=True
    )
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='service_records')
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='service_records')
    advisor = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='completed_services'
    )
    service_type = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    mileage_at_service = models.IntegerField(default=0)
    cost = models.DecimalField(max_digits=8, decimal_places=2)
    completed_at = models.DateTimeField(default=timezone.now)
    next_service_mileage = models.IntegerField(null=True, blank=True)
    parts_used = models.TextField(blank=True)

    class Meta:
        ordering = ['-completed_at']

    def __str__(self):
        return f"{self.vehicle} - {self.service_type} on {self.completed_at.date()}"


# ─── MAINTENANCE ALERT ───────────────────────────────────────────────────────

class MaintenanceAlert(models.Model):
    ALERT_TYPE_CHOICES = [
        ('oil_change', 'Oil Change Due'),
        ('tire_rotation', 'Tire Rotation Due'),
        ('major_service', 'Major Service Due'),
        ('inspection', 'Inspection Due'),
        ('custom', 'Custom Alert'),
    ]

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPE_CHOICES)
    message = models.CharField(max_length=200)
    mileage_threshold = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.vehicle} - {self.message}"
    
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance, defaults={'role': 'customer'})