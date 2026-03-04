from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Q
from .models import Vehicle, Appointment, ServiceRecord, MaintenanceAlert
from .forms import VehicleForm, AppointmentForm, AppointmentAssignForm, ServiceRecordForm, CustomerRegistrationForm, StaffRegistrationForm, ProfileUpdateForm
import datetime



def get_profile(user):
    """Safely get or create a profile for any user."""
    from .models import UserProfile
    profile, _ = UserProfile.objects.get_or_create(user=user, defaults={'role': 'customer'})
    return profile


def staff_required(view_func):
    """Decorator: only advisors and owners can access."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not hasattr(request.user, 'profile') or not request.user.profile.is_staff_member():
            messages.error(request, 'Access denied. Staff only.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def owner_required(view_func):
    """Decorator: only owners can access."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not hasattr(request.user, 'profile') or not request.user.profile.is_owner():
            messages.error(request, 'Access denied. Owners only.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
def dashboard(request):
    today = timezone.now().date()
    profile = get_profile(request.user)

    if profile and profile.is_staff_member():
        # Staff dashboard
        today_appointments = Appointment.objects.filter(
            date=today
        ).select_related('customer', 'vehicle', 'advisor')

        upcoming_appointments = Appointment.objects.filter(
            date__gt=today,
            status__in=['scheduled', 'pending']
        ).select_related('customer', 'vehicle', 'advisor').order_by('date', 'time')[:10]

        total_customers = User.objects.filter(profile__role='customer').count()

        current_month = today.month
        current_year = today.year
        month_revenue = ServiceRecord.objects.filter(
            completed_at__month=current_month,
            completed_at__year=current_year
        ).aggregate(total=Sum('cost'))['total'] or 0

        services_completed = ServiceRecord.objects.filter(
            completed_at__month=current_month,
            completed_at__year=current_year
        ).count()

        maintenance_alerts = MaintenanceAlert.objects.filter(
            is_active=True
        ).select_related('vehicle', 'vehicle__owner').order_by('-created_at')[:5]

        context = {
            'today_appointments': today_appointments,
            'upcoming_appointments': upcoming_appointments,
            'total_customers': total_customers,
            'month_revenue': month_revenue,
            'services_completed': services_completed,
            'maintenance_alerts': maintenance_alerts,
            'is_staff': True,
        }
    else:
        # Customer dashboard
        my_vehicles = Vehicle.objects.filter(owner=request.user)
        my_appointments = Appointment.objects.filter(
            customer=request.user,
            date__gte=today
        ).select_related('vehicle', 'advisor').order_by('date', 'time')[:5]

        my_service_history = ServiceRecord.objects.filter(
            customer=request.user
        ).select_related('vehicle').order_by('-completed_at')[:5]

        my_alerts = MaintenanceAlert.objects.filter(
            vehicle__owner=request.user,
            is_active=True
        ).select_related('vehicle')

        context = {
            'my_vehicles': my_vehicles,
            'my_appointments': my_appointments,
            'my_service_history': my_service_history,
            'my_alerts': my_alerts,
            'is_staff': False,
        }

    return render(request, 'dashboard.html', context)


# --- VEHICLE VIEWS ---

@login_required
def vehicle_list(request):
    if get_profile(request.user).is_staff_member():
        vehicles = Vehicle.objects.all().select_related('owner')
    else:
        vehicles = Vehicle.objects.filter(owner=request.user)
    return render(request, 'vehicles.html', {'vehicles': vehicles})


@login_required
def vehicle_create(request):
    form = VehicleForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        vehicle = form.save(commit=False)
        vehicle.owner = request.user
        vehicle.save()
        messages.success(request, f'{vehicle} added successfully!')
        return redirect('vehicle_list')
    return render(request, 'vehicle_form.html', {'form': form, 'title': 'Add Vehicle'})


@login_required
def vehicle_edit(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    if not get_profile(request.user).is_staff_member() and vehicle.owner != request.user:
        messages.error(request, 'You can only edit your own vehicles.')
        return redirect('vehicle_list')
    form = VehicleForm(request.POST or None, instance=vehicle)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Vehicle updated!')
        return redirect('vehicle_list')
    return render(request, 'vehicle_form.html', {'form': form, 'title': 'Edit Vehicle', 'vehicle': vehicle})


@login_required
def vehicle_delete(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    if not get_profile(request.user).is_staff_member() and vehicle.owner != request.user:
        messages.error(request, 'You can only delete your own vehicles.')
        return redirect('vehicle_list')
    if request.method == 'POST':
        vehicle.delete()
        messages.success(request, 'Vehicle removed.')
        return redirect('vehicle_list')
    return render(request, 'confirm_delete.html', {'object': vehicle, 'type': 'vehicle'})


# --- APPOINTMENT VIEWS ---

@login_required
def appointment_list(request):
    if get_profile(request.user).is_staff_member():
        appointments = Appointment.objects.all().select_related('customer', 'vehicle', 'advisor')
    else:
        appointments = Appointment.objects.filter(customer=request.user).select_related('vehicle', 'advisor')

    status_filter = request.GET.get('status', '')
    if status_filter:
        appointments = appointments.filter(status=status_filter)

    return render(request, 'appointments.html', {
        'appointments': appointments,
        'status_filter': status_filter,
        'status_choices': Appointment.STATUS_CHOICES,
    })


@login_required
def appointment_create(request):
    form = AppointmentForm(user=request.user, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        appt = form.save(commit=False)
        appt.customer = request.user
        appt.status = 'pending'
        appt.save()
        messages.success(request, 'Appointment requested! Awaiting confirmation.')
        return redirect('appointment_list')
    return render(request, 'appointment_form.html', {'form': form, 'title': 'Book Appointment'})


@login_required
def appointment_detail(request, pk):
    appt = get_object_or_404(Appointment, pk=pk)
    can_edit = (
        get_profile(request.user).is_staff_member() or
        appt.customer == request.user
    )
    return render(request, 'appointment_detail.html', {'appt': appt, 'can_edit': can_edit})


@login_required
@staff_required
def appointment_assign(request, pk):
    appt = get_object_or_404(Appointment, pk=pk)
    form = AppointmentAssignForm(request.POST or None, instance=appt)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Appointment updated.')
        return redirect('appointment_list')
    return render(request, 'appointment_assign.html', {'form': form, 'appt': appt})


@login_required
@staff_required
def appointment_complete(request, pk):
    appt = get_object_or_404(Appointment, pk=pk)
    form = ServiceRecordForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        record = form.save(commit=False)
        record.appointment = appt
        record.vehicle = appt.vehicle
        record.customer = appt.customer
        record.advisor = request.user
        record.save()

        # Update vehicle mileage
        if record.mileage_at_service > appt.vehicle.current_mileage:
            appt.vehicle.current_mileage = record.mileage_at_service
            appt.vehicle.save()

        appt.status = 'completed'
        appt.actual_cost = record.cost
        appt.save()

        # Create maintenance alert if needed
        if record.next_service_mileage:
            MaintenanceAlert.objects.create(
                vehicle=appt.vehicle,
                alert_type='oil_change',
                message=f"Service due at {record.next_service_mileage:,} miles",
                mileage_threshold=record.next_service_mileage,
            )

        messages.success(request, 'Service completed and record saved.')
        return redirect('appointment_list')

    return render(request, 'appointment_complete.html', {'form': form, 'appt': appt})


# --- CUSTOMER VIEWS (staff only) ---

@login_required
@staff_required
def customer_list(request):
    customers = User.objects.filter(profile__role='customer').select_related('profile')
    return render(request, 'customers.html', {'customers': customers})


@login_required
@staff_required
def customer_detail(request, pk):
    customer = get_object_or_404(User, pk=pk, profile__role='customer')
    vehicles = Vehicle.objects.filter(owner=customer)
    appointments = Appointment.objects.filter(customer=customer).order_by('-date')[:10]
    service_records = ServiceRecord.objects.filter(customer=customer).order_by('-completed_at')[:10]
    return render(request, 'customer_detail.html', {
        'customer': customer,
        'vehicles': vehicles,
        'appointments': appointments,
        'service_records': service_records,
    })


# --- SERVICE HISTORY ---

@login_required
def service_history(request):
    if get_profile(request.user).is_staff_member():
        records = ServiceRecord.objects.all().select_related('vehicle', 'customer', 'advisor')
    else:
        records = ServiceRecord.objects.filter(customer=request.user).select_related('vehicle', 'advisor')

    return render(request, 'service_history.html', {'records': records})


# --- AUTH VIEWS ---

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        messages.success(request, f'Welcome back, {user.first_name}!')
        return redirect('dashboard')
    return render(request, 'login.html', {'form': form})


def register_customer(request):
    form = CustomerRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Account created! Welcome.')
        return redirect('dashboard')
    return render(request, 'register.html', {'form': form, 'role': 'customer'})


def register_staff(request):
    form = StaffRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Staff account created!')
        return redirect('dashboard')
    return render(request, 'register.html', {'form': form, 'role': 'staff'})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def profile_view(request):
    profile = get_profile(request.user)
    form = ProfileUpdateForm(request.POST or None, instance=profile)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.user.first_name = form.cleaned_data['first_name']
        obj.user.last_name = form.cleaned_data['last_name']
        obj.user.email = form.cleaned_data['email']
        obj.user.save()
        obj.save()
        messages.success(request, 'Profile updated.')
        return redirect('profile')
    return render(request, 'profile.html', {'form': form, 'profile': profile})