from django.db import models
from django.contrib.auth.models import User


# ----------------------------
# 1️⃣ Hospital Model
# ----------------------------
class Hospital(models.Model):
    name = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    address = models.TextField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    rating = models.FloatField(default=0.0)
    total_reviews = models.IntegerField(default=0)
    location_name = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to='hospital_images/', blank=True, null=True)
    
    def __str__(self):
        return self.name


# ----------------------------
# 2️⃣ Department Model
# ----------------------------
class Department(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


# ----------------------------
# 3️⃣ HospitalDepartment (Junction Table)
# ----------------------------
class HospitalDepartment(models.Model):
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.hospital.name} - {self.department.name}"


# ----------------------------
# 4️⃣ Doctor Model
# ----------------------------
class Doctor(models.Model):
    user = models.OneToOneField(
    User,
    on_delete=models.CASCADE,
    null=True,
    blank=True
)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    qualification = models.CharField(max_length=200)
    experience_years = models.PositiveIntegerField()
    rating = models.FloatField(default=0.0)
    fee = models.FloatField()
    phone = models.CharField(
    max_length=15,
    blank=True
)
    email = models.EmailField(
    blank=True
)
    image = models.ImageField(
    upload_to="doctor_images/",
    blank=True,
    null=True
)
    is_active = models.BooleanField(default=True)
    is_on_leave = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if self.pk:
            old = Doctor.objects.get(pk=self.pk)

            if not old.is_on_leave and self.is_on_leave:
                from .views import handle_doctor_leave
                handle_doctor_leave(self)

        super().save(*args, **kwargs)


# ----------------------------
# 5️⃣ Patient Model
# ----------------------------
class Patient(models.Model):
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True)
    city = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# ----------------------------
# 6️⃣ DoctorSchedule Model
# ----------------------------
class DoctorSchedule(models.Model):

    doctor = models.ForeignKey(
        'Doctor',
        on_delete=models.CASCADE
    )

    DAY_CHOICES = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ]

    day_of_week = models.CharField(
        max_length=10,
        choices=DAY_CHOICES
    )

    start_time = models.TimeField()

    end_time = models.TimeField()

    slot_duration = models.PositiveIntegerField(
        help_text="Duration of each appointment in minutes."
    )

    class Meta:
        unique_together = ("doctor", "day_of_week")
        ordering = ["doctor", "day_of_week"]

    def __str__(self):
        return f"{self.doctor.name} - {self.day_of_week}"

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.end_time <= self.start_time:
            raise ValidationError(
                "End time must be later than start time."
            )

        if self.slot_duration <= 0:
            raise ValidationError(
                "Slot duration must be greater than zero."
            )

    @property
    def total_slots(self):
        from datetime import datetime

        start = datetime.combine(datetime.today(), self.start_time)
        end = datetime.combine(datetime.today(), self.end_time)

        minutes = (end - start).seconds // 60

        return minutes // self.slot_duration


# ----------------------------
# 7️⃣ Doctor Leave Model
# ----------------------------
class DoctorLeave(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    leave_date = models.DateField()
    reason = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.doctor.name} - {self.leave_date}"


# ----------------------------
# 8️⃣ Appointment Model
# ----------------------------
class Appointment(models.Model):
    STATUS_CHOICES = [
        ('Booked', 'Booked'),
        ('Cancelled', 'Cancelled'),
        ('Completed', 'Completed'),
        ("Missed","Missed"),
        ('Rescheduled', 'Rescheduled'), 
    ]

    rescheduled_from = models.DateField(null=True, blank=True)
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True) 
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)

    appointment_date = models.DateField()
    time_slot = models.TimeField()
    token_number = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Booked')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient.name} - {self.doctor.name}"


# ----------------------------
# 9️⃣ Feedback Model
# ----------------------------
class Feedback(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE)
    rating = models.IntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback - {self.appointment.id}"


# ----------------------------
# 🔟 MessageLog Model
# ----------------------------
class MessageLog(models.Model):
    MESSAGE_TYPES = [
        ('Confirmation', 'Confirmation'),
        ('Reminder', 'Reminder'),
        ('Reschedule', 'Reschedule'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, null=True, blank=True)

    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES)
    content = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.message_type} - {self.patient.name}"
  
 #----------------------------  
 # 11-Notification model
 #---------------------------   
class Notification(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE
    )

    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    message = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    NOTIFICATION_TYPES = [
    ("Booking", "Booking"),
    ("Cancelled", "Cancelled"),
    ("Rescheduled", "Rescheduled"),
    ("Reminder", "Reminder"),
    ]

    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES
    )
    def __str__(self):
        return f"{self.patient.name} - {self.message[:30]}" 
    
#-------------------------------
# 12-User Profile
#-------------------------------
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15)

    def __str__(self):
        return self.user.username

#-------------------------------
# rating feature
#-------------------------------

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Rating(models.Model):

    appointment = models.OneToOneField(
        'Appointment',
        on_delete=models.CASCADE,
        related_name='rating'
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    doctor = models.ForeignKey(
        'Doctor',
        on_delete=models.CASCADE,
        related_name='reviews'
    )

    rating = models.IntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5)
        ]
    )

    review = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.doctor.name} - {self.rating}★"