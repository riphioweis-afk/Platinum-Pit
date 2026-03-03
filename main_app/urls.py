from django.urls import path
from . import views # Import views to connect routes to view functions


urlpatterns = [
    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_customer, name='register_customer'),
    path('register/staff/', views.register_staff, name='register_staff'),
    path('profile/', views.profile_view, name='profile'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Vehicles
    path('vehicles/', views.vehicle_list, name='vehicle_list'),
    path('vehicles/add/', views.vehicle_create, name='vehicle_create'),
    path('vehicles/<int:pk>/edit/', views.vehicle_edit, name='vehicle_edit'),
    path('vehicles/<int:pk>/delete/', views.vehicle_delete, name='vehicle_delete'),

    # Appointments
    path('appointments/', views.appointment_list, name='appointment_list'),
    path('appointments/book/', views.appointment_create, name='appointment_create'),
    path('appointments/<int:pk>/', views.appointment_detail, name='appointment_detail'),
    path('appointments/<int:pk>/assign/', views.appointment_assign, name='appointment_assign'),
    path('appointments/<int:pk>/complete/', views.appointment_complete, name='appointment_complete'),

    # Customers (staff only)
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/<int:pk>/', views.customer_detail, name='customer_detail'),

    # Service History
    path('service-history/', views.service_history, name='service_history'),
]
