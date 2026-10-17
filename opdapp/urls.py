from django.urls import path
from . import views


urlpatterns = [
    
    path('login/', views.user_login, name='login'),
    
    path('register/', views.user_register, name='register'),
    
    path('logout/', views.logout_confirm, name='logout'),    # opens confirm page
    
    path('logout/confirm/', views.user_logout, name='logout_confirm'),
    
    path('profile/', views.profile, name='profile'),
    
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    
    path('', views.recommend_hospitals, name='home'),  # homepage
    
    path('recommend/', views.recommend_hospitals, name='recommend'),

    path('doctors/<int:hospital_id>/', views.hospital_doctors, name='hospital_doctors'),
    
    path('book/<int:doctor_id>/', views.book_appointment, name='book_appointment'),
    
    path('success/<int:appointment_id>/', views.success_page, name='success'),
    
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    
    path('cancel-appointment/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    
    path('complete-appointment/<int:appointment_id>/', views.complete_appointment, name='complete_appointment'),
    
    path('admin_login/', views.admin_login, name='admin_login'),
    
    path('admin_logout/', views.admin_logout, name='admin_logout'),
    
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    
    path('symptom-check/', views.symptom_checker, name='symptom_checker'),
    
    path('mark-leave/', views.mark_doctor_leave, name='mark_doctor_leave'),
    
    path('remove-leave/', views.remove_doctor_leave, name='remove_doctor_leave'),
    
    path('test-sms/', views.test_sms),
    
    path('notifications/', views.notifications, name='notifications'),
    
    path('my-appointments/', views.patient_dashboard, name='patient_dashboard'),
    
    path("search-suggestions/", views.search_suggestions, name="search_suggestions"),
    
    path("departments/<int:hospital_id>/", views.hospital_departments, name="hospital_departments"),
    
    path('miss-appointment/<int:appointment_id>/',views.miss_appointment,name='miss_appointment'),

    path('admin-cancel-appointment/<int:appointment_id>/',views.cancel_appointment_admin,name='cancel_appointment_admin'),

    path('rate/<int:appointment_id>/',views.rate_appointment,name='rate_appointment'),
    
    path("chatbot/",views.chatbot,name="chatbot"),

    path("chatbot-api/",views.chatbot_api,name="chatbot_api"),
    
    path(
    "admin-panel/hospitals/",
    views.hospital_management,
    name="hospital_management",
),

path(
    "admin-panel/hospitals/add/",
    views.hospital_add,
    name="hospital_add",
),

path(
    "admin-panel/hospitals/edit/<int:id>/",
    views.hospital_edit,
    name="hospital_edit",
),

path(
    "admin-panel/hospitals/delete/<int:id>/",
    views.hospital_delete,
    name="hospital_delete",
),
   
path(
    "admin-panel/departments/",
    views.department_management,
    name="department_management",
),

path(
    "admin-panel/departments/add/",
    views.department_add,
    name="department_add",
),

path(
    "admin-panel/departments/edit/<int:id>/",
    views.department_edit,
    name="department_edit",
),

path(
    "admin-panel/departments/delete/<int:id>/",
    views.department_delete,
    name="department_delete",
),

path(
    "admin-panel/doctors/",
    views.doctor_management,
    name="doctor_management",
),

path(
    "admin-panel/doctors/add/",
    views.doctor_add,
    name="doctor_add",
),

path(
    "admin-panel/doctors/edit/<int:id>/",
    views.doctor_edit,
    name="doctor_edit",
),

path(
    "admin-panel/doctors/delete/<int:id>/",
    views.doctor_delete,
    name="doctor_delete",
),

path(
    "admin-panel/schedules/",
    views.schedule_management,
    name="schedule_management",
),

path(
    "admin-panel/schedules/add/",
    views.schedule_add,
    name="schedule_add",
),

path(
    "admin-panel/schedules/edit/<int:id>/",
    views.schedule_edit,
    name="schedule_edit",
),

path(
    "admin-panel/schedules/delete/<int:id>/",
    views.schedule_delete,
    name="schedule_delete",
),  

path(
    "admin-panel/appointments/",
    views.appointment_management,
    name="appointment_management",
),

path(
    "admin-panel/ratings/",
    views.rating_management,
    name="rating_management",
),

path(
    "admin-panel/ratings/delete/<int:id>/",
    views.rating_delete,
    name="rating_delete",
),

path(
    "admin-panel/notifications/",
    views.notification_management,
    name="notification_management",
),

path(
    "admin-panel/notifications/delete/<int:id>/",
    views.notification_delete,
    name="notification_delete",
),

path(
    "doctor/login/",
    views.doctor_login,
    name="doctor_login",
),

path(
    "doctor/dashboard/",
    views.doctor_dashboard,
    name="doctor_dashboard",
),

path(
    "doctor/profile/",
    views.doctor_profile,
    name="doctor_profile",
),

path(
    "doctor/profile/edit/",
    views.doctor_edit_profile,
    name="doctor_edit_profile",
),

path(
    "doctor/change-password/",
    views.doctor_change_password,
    name="doctor_change_password",
),

path(
    "doctor/appointment/<int:appointment_id>/complete/",
    views.doctor_complete_appointment,
    name="doctor_complete_appointment",
),

path(
    "doctor/appointment/<int:appointment_id>/missed/",
    views.doctor_miss_appointment,
    name="doctor_miss_appointment",
),

path(
    "doctor/logout/",
    views.doctor_logout,
    name="doctor_logout",
),

]
