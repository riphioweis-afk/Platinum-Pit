from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile, Vehicle, Appointment, ServiceRecord


class CustomerRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=20, required=False, label='Phone (optional)')

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user, role='customer',
                phone=self.cleaned_data.get('phone', '')
            )
        return user


class StaffRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=20, required=False, label='Phone (optional)')
    role = forms.ChoiceField(choices=[('advisor', 'Service Advisor'), ('owner', 'Dealership Owner')])
    dealership_name = forms.CharField(max_length=100, required=False)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                role=self.cleaned_data['role'],
                phone=self.cleaned_data.get('phone', ''),
                dealership_name=self.cleaned_data.get('dealership_name', '')
            )
        return user


class ProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    email = forms.EmailField()

    class Meta:
        model = UserProfile
        fields = ['phone', 'dealership_name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email


class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ['make', 'model', 'year', 'vin', 'license_plate', 'current_mileage', 'color']
        widgets = {
            'year': forms.NumberInput(attrs={'min': 1900, 'max': 2030}),
            'current_mileage': forms.NumberInput(attrs={'min': 0}),
        }


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['vehicle', 'service_type', 'date', 'time', 'notes', 'estimated_cost']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['vehicle'].queryset = Vehicle.objects.filter(owner=user)


class AppointmentAssignForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['advisor', 'status', 'estimated_cost', 'notes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        advisors = User.objects.filter(profile__role__in=['advisor', 'owner'])
        self.fields['advisor'].queryset = advisors
        self.fields['advisor'].label_from_instance = lambda u: u.get_full_name() or u.username


class ServiceRecordForm(forms.ModelForm):
    class Meta:
        model = ServiceRecord
        fields = ['service_type', 'description', 'mileage_at_service', 'cost',
                  'next_service_mileage', 'parts_used']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'parts_used': forms.Textarea(attrs={'rows': 2}),
        }