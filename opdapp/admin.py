from django.contrib import admin
from .models import *
from .models import DoctorSchedule
from .models import Notification
from .models import Rating

admin.site.register(DoctorSchedule)
admin.site.register(Hospital)
admin.site.register(Department)
admin.site.register(HospitalDepartment)
admin.site.register(Doctor)
admin.site.register(Patient)
admin.site.register(DoctorLeave)
admin.site.register(Appointment)
admin.site.register(Feedback)
admin.site.register(MessageLog)
admin.site.register(Notification)
admin.site.register(Rating)