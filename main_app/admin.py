from django.contrib import admin
from .models import UserProfile, Vehicle, Appointment, ServiceRecord, MaintenanceAlert

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'phone', 'dealership_name']
    list_filter = ['role']

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'owner', 'current_mileage', 'created_at']
    search_fields = ['make', 'model', 'owner__username', 'vin']

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'status', 'date', 'time', 'advisor']
    list_filter = ['status', 'date']
    search_fields = ['customer__username', 'vehicle__make']

@admin.register(ServiceRecord)
class ServiceRecordAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'customer', 'cost', 'completed_at']

@admin.register(MaintenanceAlert)
class MaintenanceAlertAdmin(admin.ModelAdmin):
    list_display = ['vehicle', 'alert_type', 'message', 'is_active']
    list_filter = ['is_active', 'alert_type']
# Register your models here.
