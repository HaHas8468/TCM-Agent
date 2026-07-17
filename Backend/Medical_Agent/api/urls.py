from django.urls import path, include
from rest_framework.authtoken.views import obtain_auth_token
from .views import (
    LoginViewSet, PatientViewSet, DoctorViewSet, DepartmentViewSet,
    ScheduleViewSet, OrderViewSet, ClinicRecordViewSet, NotificationViewSet, AdminViewSet
)

urlpatterns = [
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
    
    path('auth/register', LoginViewSet.as_view({'post': 'register'}), name='patient_register'),
    path('auth/login', LoginViewSet.as_view({'post': 'login'}), name='patient_login'),
    
    path('patient/profile', PatientViewSet.as_view({'get': 'profile', 'put': 'update_profile'}), name='patient_profile'),
    path('patient/diagnosis-history', PatientViewSet.as_view({'get': 'diagnosis_history'}), name='patient_diagnosis_history'),
    path('patient/latest-diagnosis', PatientViewSet.as_view({'get': 'latest_diagnosis'}), name='patient_latest_diagnosis'),
    path('patient/<str:pk>/history', PatientViewSet.as_view({'get': 'history'}), name='patient_history'),
    
    path('doctor/auth/login', DoctorViewSet.as_view({'post': 'login'}), name='doctor_login'),
    path('doctor/profile', DoctorViewSet.as_view({'get': 'profile', 'put': 'update_profile'}), name='doctor_profile'),
    path('doctor/queue', DoctorViewSet.as_view({'get': 'queue'}), name='doctor_queue'),
    
    path('departments', DepartmentViewSet.as_view({'get': 'list_with_doctors'}), name='department_list'),
    path('doctors/<str:doctor_id>/slots', ScheduleViewSet.as_view({'get': 'slots_by_doctor'}), name='doctor_slots'),
    
    path('orders', OrderViewSet.as_view({'post': 'create'}), name='create_order'),
    path('orders/<str:pk>/start', OrderViewSet.as_view({'put': 'start'}), name='order_start'),
    path('orders/<str:pk>/finish', OrderViewSet.as_view({'put': 'finish'}), name='order_finish'),
    path('orders/<str:pk>/save', OrderViewSet.as_view({'put': 'save'}), name='order_save'),
    path('orders/<str:pk>/diagnosis', OrderViewSet.as_view({'post': 'diagnosis'}), name='order_diagnosis'),
    path('orders/<str:pk>', OrderViewSet.as_view({'get': 'detail'}), name='order_detail'),
    
    path('records', ClinicRecordViewSet.as_view({'get': 'search'}), name='record_search'),
    path('records/<str:pk>', ClinicRecordViewSet.as_view({'get': 'record_detail'}), name='record_detail'),
    
    path('patient/notifications', NotificationViewSet.as_view({'get': 'list_notifications'}), name='patient_notifications'),
    
    path('admin/users', AdminViewSet.as_view({'get': 'users'}), name='admin_users'),
]