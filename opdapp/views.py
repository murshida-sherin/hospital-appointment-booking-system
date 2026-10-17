from django.shortcuts import render, get_object_or_404
from .models import HospitalDepartment, Doctor, Appointment, Patient,Hospital
from datetime import datetime, timedelta
import math
from .forms import DepartmentForm, DoctorForm, HospitalForm, DoctorScheduleForm
from .models import (Department,HospitalDepartment,Doctor,)
from django.db.models import Count
from geopy.geocoders import Nominatim
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import DoctorProfileForm
from django.shortcuts import get_object_or_404
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
import os
account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
twilio_number = os.environ.get("TWILIO_PHONE_NUMBER")

#----------------------------------------
# calculate distance
#---------------------------------------
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in KM

    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c

#--------------------------------------------
#   symptom prediction AI
#--------------------------------------------
def predict_department(symptoms):
    symptoms = symptoms.lower()

    keyword_map = {
        # ❤️ Cardiology
        "chest pain": "Cardiology",
        "heart": "Cardiology",
        "bp": "Cardiology",
        "palpitations": "Cardiology",

        # 🫁 Pulmonology
        "breathing": "Pulmonology",
        "cough": "Pulmonology",
        "asthma": "Pulmonology",
        "lungs": "Pulmonology",

        # 🧠 Neurology
        "headache": "Neurology",
        "migraine": "Neurology",
        "seizure": "Neurology",
        "brain": "Neurology",
        "nerves": "Neurology",
        "dizziness": "Neurology",

        # 🍽 Gastroenterology
        "stomach": "Gastroenterology",
        "gas": "Gastroenterology",
        "acidity": "Gastroenterology",
        "vomiting": "Gastroenterology",
        "digestion": "Gastroenterology",
        "bloating": "Gastroenterology",

        # 🦴 Orthopedics
        "bone": "Orthopedics",
        "fracture": "Orthopedics",
        "joint": "Orthopedics",
        "back pain": "Orthopedics",
        "swelling of joints": "Orthopedics",

        # 👩 Gynecology
        "pregnancy": "Gynecology",
        "period": "Gynecology",
        "menstrual": "Gynecology",
        "uterus": "Gynecology",

        # 👶 Pediatrics
        "child": "Pediatrics",
        "baby": "Pediatrics",
        "infant": "Pediatrics",

        # 🧑‍⚕️ General Medicine
        "fever": "General Medicine",
        "cold": "General Medicine",
        "weakness": "General Medicine",
        "infection": "General Medicine",
        "fatigue": "General Medicine",
        "weight loss": "General Medicine",
        "weight gain": "General Medicine",

        # 👂 ENT
        "ear": "ENT",
        "nose": "ENT",
        "throat": "ENT",
        "sinus": "ENT",

        # 🧴 Dermatology
        "skin": "Dermatology",
        "rash": "Dermatology",
        "pimple": "Dermatology",
        "itching": "Dermatology",
        "nail":"Dermatology",
        "hair":"Dermatology",
    }

    matches = []

    for key, dept in keyword_map.items():
        if key in symptoms:
            matches.append(dept)

    # ✅ remove duplicates
    matches = list(set(matches))

    return matches,keyword_map

#--------------------------------------------
# Hospital Recommendation
#--------------------------------------------
from .models import Department,Doctor

def recommend_hospitals(request):
    

    query = request.GET.get('query')
    name = request.GET.get("name")
    
    # ✅ NEW: control variable
    recommended = None
    searched_doctor = None
    searched_department = None

    # 🔹 Get user location
    user_lat = request.GET.get("lat")
    user_lon = request.GET.get("lon")

    user_lat = float(user_lat) if user_lat else None
    user_lon = float(user_lon) if user_lon else None
    
    departments = Department.objects.all()
    selected_department = request.GET.get("department")

    # 🔹 STEP 1: GET HOSPITALS

    if query:

        hospital_match = Hospital.objects.filter(
            name__icontains=query
        )

        department_match = Hospital.objects.filter(
            hospitaldepartment__department__name__icontains=query
        )

        doctor_match = Hospital.objects.filter(
            doctor__name__icontains=query
        )

        hospitals = (
            hospital_match |
            department_match |
            doctor_match
        ).distinct()
        
        matched_doctor = Doctor.objects.filter(
            name__icontains=query
        ).first()

        if matched_doctor:

            searched_doctor = matched_doctor.name
            searched_department = matched_doctor.department.name
        
        # 🔥 SYMPTOM SEARCH CHECK

        predicted_departments, keyword_map = predict_department(query)

        is_symptom_search = any(
            key in query.lower()
            for key in keyword_map.keys()
        )

        if is_symptom_search:

            hospitals = Hospital.objects.filter(
            hospitaldepartment__department__name__in=predicted_departments
        ).distinct()

        recommended = predicted_departments[0] if predicted_departments else None

    else:
        hospitals = Hospital.objects.all()
        
        if selected_department:
            hospitals = hospitals.filter(
        hospitaldepartment__department__name=selected_department
        ).distinct()
    
        recommended = None   # important
        predicted_departments = []
        
    # 🔹 STEP 2: CONVERT → CLEAN → RANK

    hospital_list = list({h.id: h for h in hospitals}.values())

    if user_lat is not None and user_lon is not None:

        for h in hospital_list:
            if h.latitude and h.longitude:
                h.distance = haversine(user_lat, user_lon, h.latitude, h.longitude)
            else:
                h.distance = 9999

            h.rank_score = (h.rating * 2) - (h.distance * 0.5)

        hospital_list.sort(key=lambda x: x.rank_score, reverse=True)

    else:
        hospital_list.sort(key=lambda x: x.rating, reverse=True)
        
    print("DEBUG recommended:", recommended)

    return render(request, 'recommend.html', {
    'hospitals': hospital_list,
    'query': query,
    "username": name,
    "recommended": recommended,
    "lat": user_lat,
    "lon": user_lon,
    'departments': departments,
    'searched_doctor': searched_doctor,
    'searched_department': searched_department,
})
    
#------------------------------------------
#hospital departments
#------------------------------------------

def hospital_departments(request, hospital_id):
    hospital = Hospital.objects.get(id=hospital_id)

    departments = HospitalDepartment.objects.filter(
        hospital=hospital
    ).select_related("department")

    # ✅ ONLY take from URL (no AI here)
    recommended = request.GET.get("recommended")
    query = request.GET.get("query")

    departments = list(departments)

    # ✅ Safe comparison (case-insensitive)
    if recommended:
        departments.sort(
            key=lambda d: d.department.name.lower() != recommended.lower()
        )

    return render(request, "departments.html", {
        "hospital": hospital,
        "departments": departments,
        "recommended": recommended,
        "query": query,
        "lat": request.GET.get("lat"),
        "lon": request.GET.get("lon"),
    })
    
    
# ----------------------------
# Doctor Recommendation
# ----------------------------
def hospital_doctors(request, hospital_id):

    department = request.GET.get('department')

    if department:
        doctors = Doctor.objects.filter(
            hospital_id=hospital_id,
            department__name__icontains=department
        ).order_by('-rating')

    else:
        doctors = Doctor.objects.filter(
            hospital_id=hospital_id
        ).order_by('-rating')

    return render(request, 'doctors.html', {
        'doctors': doctors,
        'department': department
    })


# ----------------------------
# Appointment Booking
# ----------------------------
from django.shortcuts import render, get_object_or_404, redirect
from .models import Doctor, DoctorSchedule, Appointment, Patient
from datetime import datetime, date, timedelta
from django.contrib import messages
from .models import DoctorLeave
from .models import Notification
from django.contrib.auth.decorators import login_required

@login_required(login_url='/login/')

def book_appointment(request, doctor_id):
    
    doctor = get_object_or_404(Doctor, id=doctor_id)
    
    selected_date = request.GET.get("date") or request.POST.get("date")
    
    if doctor.is_on_leave:
        messages.error(request, "Doctor is on leave. Please select another doctor.")
        return redirect("hospital_doctors", hospital_id=doctor.hospital.id)
    
    # Get doctor schedules
    schedules = DoctorSchedule.objects.filter(doctor=doctor)
    available_days = [s.day_of_week for s in schedules]

    selected_date = request.GET.get("date") or request.POST.get("date")

    slots = []
    schedule = None
    

    # 🔹 STEP 1: Generate slots
    if selected_date:
        try:
            selected_date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
            
            # 🔴 CHECK IF DOCTOR IS ON LEAVE
            is_on_leave = DoctorLeave.objects.filter(
                doctor=doctor,
                leave_date=selected_date_obj
            ).exists()

            if is_on_leave:
                messages.error(request, "Doctor is on leave on this day. Please choose another date.")
                return redirect(f"/book/{doctor.id}/")

            if selected_date_obj < date.today():
                error = "You cannot book past dates."

            else:
                day_name = selected_date_obj.strftime("%A")

                schedule = DoctorSchedule.objects.filter(
                    doctor=doctor,
                    day_of_week__iexact=day_name
                ).first()

            if schedule:
                start_time = schedule.start_time
                end_time = schedule.end_time

                current = datetime.combine(datetime.today(), start_time)
                end = datetime.combine(datetime.today(), end_time)

                # ✅ STEP 1: Generate ALL slots
                while current < end:
                    slots.append(current.strftime("%H:%M"))
                    current += timedelta(minutes=30)

                # ✅ STEP 2: Get booked slots ONCE
                booked_slots = Appointment.objects.filter(
                    doctor=doctor,
                    appointment_date=selected_date_obj,
                    status__in=["Booked", "Completed", "Rescheduled"]
                ).values_list('time_slot', flat=True)

                booked_slots = [t.strftime("%H:%M") for t in booked_slots]

                # ✅ STEP 3: Filter available slots
                slots = [slot for slot in slots if slot not in booked_slots]

                # ✅ STEP 4: Check if full
                if not slots:
                    messages.error(request, "Booking is full for this day. Please choose another date.")
                    return redirect(f"/book/{doctor.id}/")

            else:
                messages.error(request, "Doctor is not available on this day.")
                return redirect(f"/book/{doctor.id}/")

        except Exception as e:
            print("Date Error:", e)
            messages.error(request, "Invalid date selected.")
            return redirect(f"/book/{doctor.id}/")
   
    # 🔹 STEP 2: Booking
    if request.method == "POST":
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        time = request.POST.get("time")

    # ✅ Validate time
        if not time:
            messages.error(request, "Please select a time slot.")
            return redirect(f"/book/{doctor.id}/")

    # ✅ Validate schedule
        if not schedule:
            messages.error(request, "Doctor is not available on this day.")
            return redirect(f"/book/{doctor.id}/")
        try:
            selected_date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
            
            # 🔴 LIMIT: Only 2 names per phone per doctor per day
            # Normalize phone
            phone = phone.strip()
            if not phone.startswith("+"):
                phone = "+91" + phone

                names_for_phone = Appointment.objects.filter(
                    doctor=doctor,
                    appointment_date=selected_date_obj,
                    patient__phone=phone,
                    status__in=["Booked", "Rescheduled"]
                ).values_list('patient__name', flat=True).distinct()

            if len(names_for_phone) >= 3 and name not in names_for_phone:
                messages.error(
                request,
                "Only 3 different patients can be booked with this phone number for this doctor on this day."
                )
                return redirect(f"/book/{doctor.id}/")
        
            patient, created = Patient.objects.get_or_create(
                phone=phone,
                name=name
            )

            # 🔴 Prevent duplicate booking (same person same day)
            exists = Appointment.objects.filter(
                patient=patient,
                doctor=doctor,
                appointment_date=selected_date_obj
            ).exists()

            if exists:
                messages.error(request, "You already have a booking on this day.")
                return redirect(f"/book/{doctor.id}/")

            # ✅ Convert time safely
            try:
                time_obj = datetime.strptime(time, "%H:%M").time()
                
                # 🔴 CHECK: slot already booked?
                slot_taken = Appointment.objects.filter(
                    doctor=doctor,
                    appointment_date=selected_date_obj,
                    time_slot=time_obj,
                    status__in=["Booked", "Completed","Rescheduled"]
                    ).exists()

                if slot_taken:
                    messages.error(request, "This time slot is already booked. Please choose another.")
                    return redirect(f"/book/{doctor.id}/")
            except:
                messages.error(request, "Invalid time selected.")
                return redirect(f"/book/{doctor.id}/")

            # ✅ Generate token
            day_name = selected_date_obj.strftime("%A")

            schedule = DoctorSchedule.objects.get(
                doctor=doctor,
                day_of_week__iexact=day_name
            )

            start_time = schedule.start_time
            end_time = schedule.end_time

            current = datetime.combine(datetime.today(), start_time)
            end = datetime.combine(datetime.today(), end_time)

            all_slots = []

            while current < end:
                all_slots.append(current.strftime("%H:%M"))
                current += timedelta(minutes=30)

            token = all_slots.index(time) + 1

            # ✅ Create appointment
            appointment = Appointment.objects.create(
                user=request.user,
                patient=patient,
                doctor=doctor,
                hospital=doctor.hospital,
                appointment_date=selected_date_obj,
                time_slot=time_obj,
                token_number=token
            )

            # notification/save in DB
            n = Notification.objects.create(
                user=request.user,
                patient=patient,
                message=f"{doctor.hospital.name} • Appointment with  {doctor.name} confirmed on {selected_date_obj} at {time_obj}"
            )
            
            # get phone
            phone = request.POST.get("phone", "").strip()

            if phone.startswith("+91"):
                phone = phone[3:]

            phone = "+91" + phone
            
            message = f"Your appointment with  {doctor.name} is confirmed on {selected_date_obj} at {time_obj}. Token: {token}"
            
            #whatsapp message after booking
            send_whatsapp(
                patient.phone,
                f"Your appointment with {doctor.name} at {doctor.hospital.name} is confirmed on {selected_date_obj} at {time_obj}.Token: {token}"
            )
            
            #confirmation SMS
            try:
                send_sms(
                    patient.phone,
                    f"Your appointment with {doctor.name} at {doctor.hospital.name} is confirmed on "
                    f"{selected_date_obj} at {time_obj}. Token: {token}"
                )
            except Exception as e:
                print("SMS failed:", e)

            return redirect("success", appointment.id)

        except Exception as e:
            print("REAL ERROR:", e)
            messages.error(request, "Booking failed. Please try again.")
            return redirect(f"/book/{doctor.id}/")
    
    # 🔹 FINAL RESPONSE (ALWAYS REQUIRED)
    return render (request, "book.html", {
        "doctor": doctor,
        "schedules": schedules,
        "available_days": available_days,
        "selected_date": selected_date,
        "slots": slots,
        "today": date.today().isoformat(),
    })
#-------------------------------------------
# success page
#-------------------------------------------

def success_page(request, appointment_id):

    appointment = get_object_or_404(Appointment, id=appointment_id)

    return render(request, "success.html", {
        "appointment": appointment
    })

#--------------------------------------------
#generate time slot
#--------------------------------------------

def generate_time_slots(start_time, end_time, duration):

    slots = []

    start = datetime.combine(datetime.today(), start_time)
    end = datetime.combine(datetime.today(), end_time)

    while start < end:
        slots.append(start.time().strftime("%H:%M"))
        start += timedelta(minutes=duration)

    return slots

#---------------------------------------------------
# Admin dashboard
#---------------------------------------------------
from django.contrib.auth.decorators import login_required
from .models import DoctorLeave

@login_required(login_url='admin_login')
def admin_dashboard(request):
    
    if not request.user.is_staff:
            logout(request)
            messages.error(
            request,
            "Please login as an administrator."
        )
            return redirect("admin_login")

    selected_date = request.GET.get("date")

    if selected_date:
        selected_date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
    else:
        selected_date_obj = date.today()

    day_name = selected_date_obj.strftime("%A")

    # 🔹 Appointments for selected date
    appointments = Appointment.objects.filter(
        appointment_date=selected_date_obj
    )

    # 🔹 get doctors on leave for selected date
    leave_doctors = DoctorLeave.objects.filter(
        leave_date=selected_date_obj
    ).values_list('doctor_id', flat=True)

    # 🔹 Doctors available on that day (excluding leave)
    schedules = DoctorSchedule.objects.filter(
        day_of_week__iexact=day_name
    ).exclude(
        doctor_id__in=leave_doctors
    ).select_related(
        'doctor__hospital', 'doctor__department'
    ).order_by(
        'doctor__hospital__name', 'doctor__department__name', 'doctor__name'
    )

    doctor_data = []

    for schedule in schedules:
        doctor = schedule.doctor

        start_time = schedule.start_time
        end_time = schedule.end_time

        current = datetime.combine(datetime.today(), start_time)
        end = datetime.combine(datetime.today(), end_time)

        total_slots = []
        while current < end:
            total_slots.append(current.strftime("%H:%M"))
            current += timedelta(minutes=30)

        booked = Appointment.objects.filter(
            doctor=doctor,
            appointment_date=selected_date_obj,
            status__in=["Booked", "Completed","Rescheduled"]
        ).values_list('time_slot', flat=True)

        booked = [t.strftime("%H:%M") for t in booked]

        available = [s for s in total_slots if s not in booked]

        total_appointments = Appointment.objects.filter(
            doctor=doctor,
            appointment_date=selected_date_obj
        ).count()

        completed_count = Appointment.objects.filter(
            doctor=doctor,
            appointment_date=selected_date_obj,
            status="Completed"
        ).count()

        doctor_data.append({
            "doctor": doctor,
            "available_slots": available,
            "booked_slots": booked,

            "total_appointments": total_appointments,
            "completed_count": completed_count,
        })
        
    total_appointments = Appointment.objects.filter(
        appointment_date=selected_date_obj
    ).count()

    missed_count = Appointment.objects.filter(
    appointment_date=selected_date_obj,
    status="Missed"
    ).count()

    completed_count = Appointment.objects.filter(
        appointment_date=selected_date_obj,
        status="Completed"
    ).count()

    cancelled_count = Appointment.objects.filter(
        appointment_date=selected_date_obj,
        status="Cancelled"
    ).count()

    rescheduled_count = Appointment.objects.filter(
        appointment_date=selected_date_obj,
        status="Rescheduled"
    ).count()
    
    all_doctors = Doctor.objects.all()

    return render(request, "admin/dashboard.html", {
    "appointments": appointments,
    "doctor_data": doctor_data,
    "selected_date": selected_date_obj,

    "total_appointments": total_appointments,
    "missed_count": missed_count,
    "completed_count": completed_count,
    "cancelled_count": cancelled_count,
    "rescheduled_count": rescheduled_count,

    # 🔴 ADD THIS
    "all_doctors": all_doctors,
})
    
    
 #--------------------------------------------------
 #cancel booking
 #--------------------------------------------------
  
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from .models import Notification

def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)

    # ✅ Update status instead of deleting
    appointment.status = "Cancelled"
    appointment.save()
    
    #whatsapp message
    send_whatsapp(
        appointment.patient.phone,
        f"Your appointment with  {appointment.doctor.name} at {appointment.hospital.name} on {appointment.appointment_date} was cancelled"
    )
    
    #notification/save in DB
    Notification.objects.create(
        user=request.user,
        patient=appointment.patient,
        message=f"Your appointment with  {appointment.doctor.name} at {appointment.hospital.name} on {appointment.appointment_date} was cancelled"
        )
    
    #cancel SMS
    try:
        send_sms(
            appointment.patient.phone,
            f"Your appointment with {appointment.doctor.name} at {appointment.hospital.name} on {appointment.appointment_date} "
            f"has been cancelled"
        )
    except Exception as e:
        print("SMS failed:", e)

    messages.success(request, "Appointment cancelled successfully.")

    # Redirect back to dashboard (keep date if present)
    return redirect(request.META.get('HTTP_REFERER', 'admin_dashboard'))

#-----------------------------------------------------
#    mark apppointment as completed
#-----------------------------------------------------

from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages

def complete_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)

    # ❌ Don't complete cancelled appointments
    if appointment.status == "Cancelled":
        messages.error(request, "Cannot complete a cancelled appointment.")
    else:
        appointment.status = "Completed"
        appointment.save()
        messages.success(request, "Appointment marked as completed.")

    return redirect(request.META.get('HTTP_REFERER', 'admin_dashboard'))

#----------------------------------------------------------
#  login page for admin dashboard
#---------------------------------------------------------

from django.contrib.messages import get_messages
from django.contrib.auth import authenticate, login, logout

def admin_login(request):
    storage = get_messages(request)
    for _ in storage:
        pass   # 🔥 clears old messages

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None: 
            if user.is_staff:
                login(request, user)
                return redirect("admin_dashboard")
            else:
                messages.error(
                 request,
                 "You are not authorized to access the Admin Panel."
                )
        else:
            messages.error(
            request,
            "Invalid username or password."
        )
    else:
            messages.error(request, "Invalid username or password")

    return render(request, "login.html")

#--------------------------------------------------------------
#  log out
#--------------------------------------------------------------

def admin_logout(request):
    logout(request)
    return redirect('admin_login')

#-------------------------------------------------
#  symptom prediction
#-------------------------------------------------

def symptom_checker(request):
    departments = None
    doctors = None
    hospitals = None
    symptoms = None

    if request.method == "POST":
        symptoms = request.POST.get("symptoms")
        latitude = request.POST.get("latitude")
        longitude = request.POST.get("longitude")

        print("SYMPTOM:", symptoms)
        print("LAT:", latitude, "LNG:", longitude)

        # 🔹 AI prediction
        departments = predict_department(symptoms)

        doctors = Doctor.objects.filter(
            department__name__in=departments
        )

        hospitals = Hospital.objects.filter(
            doctor__in=doctors
        ).distinct()

        print("BEFORE SORT:", hospitals)

        hospital_list = list(hospitals)

        # 🔥 DISTANCE CALCULATION
        if latitude and longitude:
            try:
                user_lat = float(latitude)
                user_lng = float(longitude)

                for h in hospital_list:
                    if h.latitude is not None and h.longitude is not None:
                        h.distance = haversine(
                            user_lat, user_lng,
                            h.latitude, h.longitude
                        )
                    else:
                        h.distance = 9999
            except Exception as e:
                print("ERROR IN DISTANCE:", e)

        # 🔥 SCORING (CORRECT PLACE)
        for h in hospital_list:
            doctor_ratings = []

            for d in doctors:
                if d.hospital == h:
                    doctor_ratings.append(d.rating or 0)

            if doctor_ratings:
                avg_rating = sum(doctor_ratings) / len(doctor_ratings)
            else:
                avg_rating = 0

            distance_score = 1 / (h.distance + 1) if hasattr(h, 'distance') else 0

            h.score = (avg_rating * 0.7) + (distance_score * 0.3)

        # 🔥 SORT AFTER SCORE
        hospital_list.sort(key=lambda h: h.score, reverse=True)

        hospitals = hospital_list

    return render(request, "symptom_checker.html", {
        "departments": departments,
        "doctors": doctors,
        "hospitals": hospitals,
    })

#---------------------------------------------
#   handle existing appointments/rescheduling
#---------------------------------------------

from .models import Notification
def handle_doctor_leave(doctor, leave_date,request):
    print("Leave triggered for:", doctor.name, leave_date)

    appointments = Appointment.objects.filter(
        doctor=doctor,
        appointment_date=leave_date,
        status__in=["Booked", "Rescheduled"]
    )

    print("Appointments found:", appointments.count())

    for a in appointments:
        print("➡ Processing:", a.patient.name, a.appointment_date, a.time_slot)

        new_date, new_time = find_next_available_slot(
            doctor,
            a.appointment_date,
            a.time_slot
        )

        if new_date:
            print("Rescheduling to:", new_date, new_time)

            a.rescheduled_from = a.appointment_date
            a.appointment_date = new_date
            a.time_slot = new_time
            a.status = "Rescheduled"
            a.save()
            
            #whatsapp message
            send_whatsapp(
                a.patient.phone,
                f"Your appointment with  {doctor.name} at {doctor.hospital.name} has been rescheduled from {a.rescheduled_from} to {new_date} at {new_time}"
            )
            
            #notification/save in DB
            Notification.objects.create(
                user=request.user,
                patient=a.patient,
                message=f"Your appointment with {doctor.name} at {doctor.hospital.name} has been rescheduled from {a.rescheduled_from} to {new_date} at {new_time}"
            )
            #reschedule SMS
            try:
                send_sms(
                    a.patient.phone,
                    f"Your appointment with  {doctor.name} at {doctor.hospital.name} has been rescheduled "
                    f"from {a.rescheduled_from} to {new_date} at {new_time}"
                )
            except Exception as e:
                print("SMS failed:", e)

        else:
            print("No slot found → Cancelling")

            a.status = "Cancelled"
            a.save()
            
            # 🔔 ADD HERE (inside else)
            Notification.objects.create(
                patient=a.patient,
                message=f"Your appointment on {a.appointment_date} was cancelled"
            )

            # 📱 ADD HERE (inside else)
            try:
                send_sms(
                    a.patient.phone,
                    f"Your appointment with  {doctor.name} at {doctor.hospital.name} on {a.appointment_date} "
                    f"has been cancelled due to doctor unavailability"
                )
            except Exception as e:
                print("SMS failed:", e)
        
    
#------------------------------------------------------
#  slot finding logic/rescheduling
#------------------------------------------------------
        
def find_next_available_slot(doctor, start_date, old_time):
        
    from datetime import timedelta

    for i in range(1, 10):
        next_date = start_date + timedelta(days=i)
        day_name = next_date.strftime("%A")

        schedule = DoctorSchedule.objects.filter(
            doctor=doctor,
            day_of_week__iexact=day_name
        ).first()

        if not schedule:
            continue

        slots = generate_time_slots(
            schedule.start_time,
            schedule.end_time,
            30
        )

        booked = Appointment.objects.filter(
            doctor=doctor,
            appointment_date=next_date,
            status__in=["Booked", "Rescheduled"]
        ).values_list("time_slot", flat=True)

        booked = [t.strftime("%H:%M") for t in booked]

        available = [s for s in slots if s not in booked]

        if old_time.strftime("%H:%M") in available:
            return next_date, old_time

        if available:
            return next_date, datetime.strptime(available[0], "%H:%M").time()

    return None, None

#-------------------------------------------------------
#  leave trigger view
#-------------------------------------------------------

from .models import DoctorLeave

def mark_doctor_leave(request):
    if request.method == "POST":
        doctor_id = request.POST.get("doctor_id")
        leave_date = request.POST.get("date")

        doctor = Doctor.objects.get(id=doctor_id)
        leave_date_obj = datetime.strptime(leave_date, "%Y-%m-%d").date()

        DoctorLeave.objects.create(
            doctor=doctor,
            leave_date=leave_date_obj
        )

        # 🔥 trigger rescheduling
        handle_doctor_leave(doctor, leave_date_obj,request)

    return redirect("admin_dashboard")
    
#--------------------------------------------------
# remove leave
#--------------------------------------------------

from django.shortcuts import get_object_or_404
    
def remove_doctor_leave(request):
    if request.method == "POST":
        doctor_id = request.POST.get("doctor_id")
        leave_date = request.POST.get("date")

        if not doctor_id or not leave_date:
            messages.error(request, "Invalid input")
        return redirect("admin_dashboard")

    doctor = get_object_or_404(Doctor, id=doctor_id)
    leave_date_obj = datetime.strptime(leave_date, "%Y-%m-%d").date()

    DoctorLeave.objects.filter(
        doctor=doctor,
        leave_date=leave_date_obj
    ).delete()

    messages.success(request, "Leave removed successfully.")

    return redirect("admin_dashboard")

#---------------------------------------------
# notification system(SMS)
#---------------------------------------------

from twilio.rest import Client

def send_sms(phone, message):
    client = Client(account_sid, auth_token)

    client.messages.create(
        body=message,
        from_=twilio_number,
        to=phone
    )
    
#---------------------------------------------
#  test  view
#--------------------------------------------
    
from django.http import HttpResponse

def test_sms(request):
    send_sms(
        "xxxxxxxxxx",   # YOUR VERIFIED NUMBER
        "Your OPD system SMS is working!"
    )
    return HttpResponse("SMS sent")

#-------------------------------------------
# sms (mobile number correcting)
#------------------------------------------

def send_sms(phone, message):
    # 🔹 Ensure +91 format
    if not phone.startswith("+"):
        phone = "+91" + phone

    try:
        client = Client(account_sid, auth_token)

        client.messages.create(
            body=message,
            from_=twilio_number,
            to=phone
        )

    except Exception as e:
        print("SMS failed:", e)
#---------------------------------------------
# notification page
#---------------------------------------------
from django.contrib.auth.decorators import login_required
from .models import Notification

@login_required(login_url='/login/')
def notifications(request):

    notes = Notification.objects.filter(
        user=request.user   # 🔥 key change
    ).order_by('-created_at')

    return render(request, "notifications.html", {
        "notes": notes
    })

#---------------------------------------------
# patient dashboard/ my appointments
#---------------------------------------------

from datetime import date, timedelta
from django.contrib.auth.decorators import login_required
from .models import Appointment

@login_required(login_url='/login/')
def patient_dashboard(request):

    today = date.today()

    # 🔥 Convert old Booked appointments to Missed

    old_bookings = Appointment.objects.filter(
        user=request.user,
        status="Booked",
        appointment_date__lt=today
    )

    print("TODAY:", today)
    print("OLD BOOKINGS FOUND:", old_bookings.count())

    for appointment in old_bookings:
        appointment.status = "Missed"
        appointment.save()

    # 🔥 Show only last 30 days

    appointments = Appointment.objects.filter(
        user=request.user
    ).select_related(
        'doctor',
        'hospital',
        'patient'
    ).order_by(
        '-appointment_date',
        '-time_slot'
    )

    # 🔥 Control Cancel button

    for a in appointments:

        a.can_cancel = (
            a.status == "Booked"
            and a.appointment_date >= today
        )

    return render(request, "patient_dashboard.html", {
        "appointments": appointments,
        "today": today
    })
    
#------------------------------------------------
# whatsapp message
#------------------------------------------------

from twilio.rest import Client

def send_whatsapp(phone, message):

    # ensure +91 format
    if not phone.startswith("+"):
        phone = "+91" + phone

    try:
        client = Client(account_sid, auth_token)

        client.messages.create(
            body=message,
            from_="whatsapp:twilio_number",  # sandbox number
            to="whatsapp:" + phone
        )

    except Exception as e:
        print("WhatsApp failed:", e)
        
from django.http import JsonResponse

#------------------------------------------
# suggestions API
#------------------------------------------

def search_suggestions(request):
    query = request.GET.get("q", "")

    suggestions = []

    if query:
        # 🔹 Hospital names
        hospitals = Hospital.objects.filter(
            name__icontains=query
        ).values_list('name', flat=True)

        # 🔹 Departments
        departments = HospitalDepartment.objects.filter(
            department__name__icontains=query
        ).values_list('department__name', flat=True)

        suggestions = list(set(list(hospitals) + list(departments)))[:5]

    return JsonResponse({"results": suggestions})


#------------------------------------------
# show whatsapp status
#------------------------------------------

def send_whatsapp(phone, message):

    phone = phone.strip()

    # 🔹 Remove +91 if already exists
    if phone.startswith("+91"):
        phone = phone[3:]

    phone = "whatsapp:+91" + phone   # ✅ correct format

    try:
        client = Client(account_sid, auth_token)

        client.messages.create(
            body=message,
            from_="whatsapp:twilio_number",
            to=phone
        )

        print("✅ WhatsApp sent to", phone)

    except Exception as e:
        print("❌ WhatsApp failed:", e)
        
#----------------------------------------------
# show SMS status
#----------------------------------------------

def send_sms(phone, message):

    phone = phone.strip()

    if not phone.startswith("+91"):
        phone = "+91" + phone

    try:
        account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        twilio_number = os.environ.get("TWILIO_PHONE_NUMBER")
        
        client = Client(account_sid, auth_token)

        client.messages.create(
            body=message,
            from_=twilio_number,   # ✅ your Twilio number
            to=phone
        )

        print("✅ SMS sent to", phone)

    except Exception as e:
        print("❌ SMS failed:", e)
        
#---------------------------------------------
# user register
#---------------------------------------------

from django.contrib.auth.models import User
from django.contrib.auth import login
from django.contrib import messages
from django.shortcuts import render, redirect

def user_register(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")
        phone = request.POST.get("phone")

        # Check duplicate username
        if User.objects.filter(username=username).exists():

            messages.error(request, "Username already exists")

            return redirect("/register/")

        # Create user
        user = User.objects.create_user(
            username=username,
            password=password
        )

        # Create profile
        UserProfile.objects.create(
            user=user,
            phone=phone
        )

        # Auto login after registration
        login(request, user)

        # Redirect to home page
        return redirect("/")

    return render(request, "userregister.html")

#-----------------------------------------------
# User Login
#-----------------------------------------------

def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect("/")   # homepage
        else:
            messages.error(request, "Invalid credentials")

    return render(request, "userlogin.html")

#----------------------------------------------
# user logout
#----------------------------------------------

from django.contrib.auth import logout
from django.shortcuts import redirect

def user_logout(request):
    logout(request)
    return redirect('login')   # or homepage

#----------------------------------------------
# Logout confirmation
#----------------------------------------------

from django.shortcuts import render, redirect
from django.contrib.auth import logout

def logout_confirm(request):
    return render(request, "logout_confirm.html")


def user_logout(request):
    logout(request)
    return redirect('/')

#---------------------------------------------
# User Profile page
#---------------------------------------------

from django.contrib.auth.decorators import login_required
from .models import UserProfile

@login_required(login_url='/login/')
def profile(request):

    profile, created = UserProfile.objects.get_or_create(
        user=request.user
    )

    return render(request, "profile.html", {
        "user": request.user,
        "profile": profile
    })
    
#--------------------------------------------
#Edit Profile
#--------------------------------------------

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import UserProfile

@login_required
def edit_profile(request):

    user = request.user

    profile, created = UserProfile.objects.get_or_create(
        user=user
    )

    if request.method == "POST":

        username = request.POST.get("username")
        phone = request.POST.get("phone")

        user.username = username

        profile.phone = phone

        user.save()
        profile.save()

        return redirect('profile')

    return render(request, "edit_profile.html", {
        "user": user,
        "profile": profile
    })
 
#--------------------------------------------
# miss appointment view
#--------------------------------------------
   
from django.shortcuts import get_object_or_404, redirect

def miss_appointment(request, appointment_id):

    appointment = get_object_or_404(
        Appointment,
        id=appointment_id
    )

    appointment.status = "Missed"
    appointment.save()

    return redirect('admin_dashboard')

#-------------------------------------------
# cancel appointment
#-------------------------------------------

def cancel_appointment_admin(request, appointment_id):

    appointment = get_object_or_404(
        Appointment,
        id=appointment_id
    )

    appointment.status = "Cancelled"
    appointment.save()

    return redirect('admin_dashboard')

#-------------------------------------------
# rating view
#-------------------------------------------

from django.db.models import Avg
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from .models import Appointment, Rating

@login_required
def rate_appointment(request, appointment_id):

    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        user=request.user
    )

    if appointment.status != "Completed":
        messages.error(
            request,
            "Only completed appointments can be rated."
        )
        return redirect("patient_dashboard")

    if Rating.objects.filter(
        appointment=appointment
    ).exists():

        messages.info(
            request,
            "You already rated this appointment."
        )
        return redirect("patient_dashboard")

    if request.method == "POST":

        rating = request.POST.get("rating")
        review = request.POST.get("review")

        Rating.objects.create(
            appointment=appointment,
            user=request.user,
            doctor=appointment.doctor,
            rating=rating,
            review=review
        )

        doctor_avg = Rating.objects.filter(
            doctor=appointment.doctor
        ).aggregate(
            Avg('rating')
        )['rating__avg']

        appointment.doctor.rating = round(
            doctor_avg,
            1
        )

        appointment.doctor.save()

        messages.success(
            request,
            "Thank you for your feedback."
        )

        return redirect("patient_dashboard")

    return render(
        request,
        "rate_appointment.html",
        {
            "appointment": appointment
        }
    )
    
#---------------------------------------
# chatbot
#---------------------------------------

from django.shortcuts import render

def chatbot(request):
    return render(
        request,
        "chatbot.html"
    )

#--------------------------------------
# chatbot-api
#--------------------------------------

from django.http import JsonResponse
from django.utils import timezone
from .models import Doctor, Appointment,Hospital
from .models import DoctorSchedule

def chatbot_api(request):

    message = request.GET.get(
        "message",
        ""
    ).lower()
    
    user_lat = request.GET.get("lat")
    user_lon = request.GET.get("lon")

    # Health Tips------------

    health_tips = {

        "General Medicine":
        "• Drink plenty of fluids\n• Get adequate rest\n• Monitor your symptoms",

        "Cardiology":
        "• Avoid strenuous activity\n• Seek immediate care if symptoms worsen",

        "Pulmonology":
        "• Avoid smoke and dust\n• Stay hydrated",

        "Neurology":
        "• Rest well\n• Avoid excessive screen time",

        "Gastroenterology":
        "• Avoid spicy foods\n• Eat light meals",

        "Orthopedics":
        "• Avoid heavy lifting\n• Rest the affected area",

        "Dermatology":
        "• Keep the area clean\n• Avoid scratching",

        "ENT":
        "• Drink warm fluids\n• Avoid cold beverages"
    }
    
    # Appointment Queries---------------

    if (
        "my appointments" in message
        or "show appointments" in message
        or "upcoming appointment" in message
    ):

        appointments = Appointment.objects.filter(
            user=request.user,
            status="Booked"
        ).order_by("appointment_date")

        if not appointments.exists():

            return JsonResponse({
                "reply":
                "You don't have any upcoming appointments."
            })

        reply = "Your Upcoming Appointments:\n\n"

        for a in appointments[:3]:

            reply += (
                f"• {a.doctor.name}\n"
                f"({doctor.hospital.name})\n"
                f"  {a.appointment_date}\n"
                f"  Token #{a.token_number}\n\n"
            )

        return JsonResponse({
            "reply": reply
        })
        
    # Token Queries-------------

    if (
        "token" in message
        or "my token" in message
    ):

        appointment = Appointment.objects.filter(
            user=request.user,
            status="Booked"
        ).order_by("appointment_date").first()

        if appointment:

            return JsonResponse({
                "reply":
                f"Your next token number is #{appointment.token_number} with Dr. {appointment.doctor.name} on {appointment.appointment_date}."
            })

        return JsonResponse({
            "reply":
            "No upcoming appointments found."
        })

    # FAQ-------------------

    if any(word in message for word in [
            "cancel",
            "cancel appointment",
            "how to cancel"
        ]):

            return JsonResponse({
                "reply":
                "To cancel an appointment:\n\n"
                "1. Open My Appointments\n"
                "2. Find the appointment\n"
                "3. Click Cancel Appointment\n"
                "4. Confirm cancellation"
            })

    if any(word in message for word in [
            "book",
            "appointment booking",
            "how to book",
            "book appointment",
            "book an appointment"
        ] ):

            return JsonResponse({
                "reply":
                "How to book an appointment:\n\n"
                "1. Search a hospital\n"
                "2. Select a department\n"
                "3. Choose a doctor\n"
                "4. Pick an available date\n"
                "5. Select a time slot\n"
                "6. Confirm booking"
            })

    if "reschedule" in message:

        return JsonResponse({
            "reply":
            "Please contact the hospital or administrator to reschedule your appointment."
        })

    #show doctors-------------
    
    if (
        "available doctors" in message
        or "show doctors" in message
        or "top doctors" in message
        ):

        doctors = Doctor.objects.filter(
            is_active=True,
            is_on_leave=False
        ).order_by("-rating")[:5]

        reply = "Top Available Doctors:\n\n"

        for doctor in doctors:

            reply += (
                f"• {doctor.name}\n"
                f"  {doctor.hospital.name}\n"
                f"  ⭐ {doctor.rating}\n\n"
            )

        return JsonResponse({
            "reply": reply
        })
    
    #nearest hospital search-------------
    
    if any(text in message for text in [

        "nearest hospital",
        "nearby hospital",
        "hospital near me",
        "hospitals near me",
        "closest hospital",
        "nearest hospitals"

    ]):

        if not user_lat or not user_lon:

            return JsonResponse({
                "reply":
                "Location not available."
            })

        user_lat = float(user_lat)
        user_lon = float(user_lon)

        hospitals = Hospital.objects.all()

        hospital_list = []

        for hospital in hospitals:

            distance = haversine(
                user_lat,
                user_lon,
                hospital.latitude,
                hospital.longitude
            )

            hospital_list.append(
                (hospital, distance)
            )

        hospital_list.sort(
            key=lambda x: x[1]
        )

        reply = "Nearest Hospitals:\n\n<br><br>"

        for hospital, distance in hospital_list[:5]:
        
            print("Hospital:", hospital.name)

            reply += (
                f" {hospital.name}<br>"
                f"{hospital.city} • {distance:.1f} km • ⭐ {hospital.rating}<br>"
                f'<a href="https://www.google.com/maps?q={hospital.latitude},{hospital.longitude}" target="_blank">Location</a><br><br>'
            )
        return JsonResponse({
            "reply": reply
        })
    
    #doctor availability--------------

    if "available" in message or "availability" in message:

        clean_message = (
            message.lower()
            .replace("dr.", "")
            .replace("dr ", "")
            .replace("?", "")
            .strip()
        )

        doctors = Doctor.objects.filter(is_active=True)

        for doctor in doctors:

            doctor_name = (
                doctor.name.lower()
                .replace("dr.", "")
                .replace("dr ", "")
                .strip()
            )

            if doctor_name in clean_message:

            # 👇 ADD THESE LINES HERE
                today = timezone.now().strftime("%A")

                schedule = DoctorSchedule.objects.filter(
                    doctor=doctor,
                    day_of_week=today
                ).first()

            # Check leave
                if doctor.is_on_leave:

                    return JsonResponse({
                        "reply":
                        f"❌ {doctor.name} is currently on leave.\n\n"
                        f"Hospital: {doctor.hospital.name}\n"
                        f"Department: {doctor.department.name}"
                    })

            # Check today's schedule
                if not schedule:

                    working_days = DoctorSchedule.objects.filter(
                        doctor=doctor
                    ).values_list("day_of_week", flat=True)

                    return JsonResponse({
                        "reply":
                        f"❌ <b>{doctor.name}</b> is not available today.<br><br>"
                        f"🗓️ <b>Available Days:</b><br>"
                        + "<br>".join(f"• {day}" for day in working_days)
                    })
                    
            # Doctor is available today
                return JsonResponse({
                    "reply":
                    f"✅ <b>{doctor.name}</b> is available today.<br><br>"
                    f"<b>Hospital:</b> {doctor.hospital.name}<br>"
                    f"<b>Department:</b> {doctor.department.name}<br>"
                    f"<b>OPD Time:</b> {schedule.start_time.strftime('%I:%M %p')} - {schedule.end_time.strftime('%I:%M %p')}<br>"
                    f"⭐ <b>Rating:</b> {doctor.rating}"
                })

        return JsonResponse({
            "reply": "Sorry, I couldn't find that doctor."
        })
        
    # Symptom Recommendation--------

    predicted_departments, _ = predict_department(
        message
    )

    if predicted_departments:

        department = predicted_departments[0]

        doctors = Doctor.objects.filter(
            department__name=department,
            is_active=True,
            is_on_leave=False
        ).order_by("-rating")[:3]

        reply = (
            f"Recommended Department:\n"
            f"{department}\n\n"
        )

        if doctors.exists():

            reply += "Available Doctors:\n"

            for doctor in doctors:

                reply += (
                    f"• {doctor.name}\n"
                    f"({doctor.hospital.name})\n"
                )

        if department in health_tips:

            reply += (
                "\nGeneral Health Tips:\n"
                + health_tips[department]
            )

            return JsonResponse({
                "reply": reply
            })

    # Emergency Detection-----------

    emergency_words = [
        "severe chest pain",
        "difficulty breathing",
        "unconscious",
        "heart attack",
        "stroke"
    ]

    for word in emergency_words:

        if word in message:

            return JsonResponse({
                "reply":
                "⚠ This may require urgent medical attention. Please visit the nearest emergency department immediately."
            })

    # Fallback-----------

    return JsonResponse({
        "reply":
        "Sorry, I couldn't understand your request. Try describing your symptoms or asking about appointments."
    })
    
#--------------------------------------
# hospital managemnt-admin dashboard
#--------------------------------------

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Avg, Sum
from .models import Hospital
from django.core.paginator import Paginator
from django.db.models import Avg, Sum


def hospital_management(request):

    hospital_queryset = Hospital.objects.all().order_by("name")

    # Statistics
    stats = hospital_queryset.aggregate(
        average_rating=Avg("rating"),
        total_reviews=Sum("total_reviews")
    )

    # Pagination
    paginator = Paginator(hospital_queryset, 10)
    page_number = request.GET.get("page")
    hospitals = paginator.get_page(page_number)

    context = {
        "hospitals": hospitals,
        "hospital_count": hospital_queryset.count(),
        "average_rating": round(stats["average_rating"] or 0, 1),
        "total_reviews": stats["total_reviews"] or 0,
    }

    return render(
        request,
        "hospitals/hospital_management.html",
        context,
    )
    
#---------------------------------------
# helper fn-location accessing
#---------------------------------------

def get_lat_long(address):
    try:
        geolocator = Nominatim(user_agent="smart_opd_system")
        location = geolocator.geocode(address)
        if location:
            return location.latitude, location.longitude
    except Exception as e:
        print("Geocoding Error:", e)
    return None, None

#-------------------------------
# add hospitals-hsptl mngmnt
#-------------------------------

def hospital_add(request):

    if request.method == "POST":

        form = HospitalForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():

            hospital = form.save(commit=False)

            # Create full address
            full_address = (
                f"{hospital.name}, "
                f"{hospital.address}, "
                f"{hospital.city}, Kerala, India"
            )

            latitude, longitude = get_lat_long(full_address)

            if latitude and longitude:
                hospital.latitude = latitude
                hospital.longitude = longitude

            hospital.save()

            messages.success(
                request,
                "Hospital added successfully."
            )

            return redirect("hospital_management")

    else:

        form = HospitalForm()

    return render(
        request,
        "hospitals/hospital_form.html",
        {
            "form": form,
            "title": "Add Hospital",
        },
    )

#---------------------------------------
# edit hsopitals
#---------------------------------------

def hospital_edit(request, id):

    hospital = get_object_or_404(
        Hospital,
        id=id,
    )

    if request.method == "POST":

        form = HospitalForm(
            request.POST,
            request.FILES,
            instance=hospital,
        )

        if form.is_valid():

            hospital = form.save(commit=False)

            # Generate coordinates again
            full_address = (
                f"{hospital.address}, "
                f"{hospital.city}, "
                f"Kerala, India"
            )

            latitude, longitude = get_lat_long(full_address)

            if latitude and longitude:
                hospital.latitude = latitude
                hospital.longitude = longitude

            hospital.save()

            messages.success(
                request,
                "Hospital updated successfully."
            )

            return redirect(
                "hospital_management"
            )

    else:

        form = HospitalForm(
            instance=hospital,
        )

    return render(
        request,
        "hospitals/hospital_form.html",
        {
            "form": form,
            "title": "Edit Hospital",
        }
    )
    
#----------------------------------------
# delete hospitals
#----------------------------------------

def hospital_delete(request,id):

    hospital=get_object_or_404(Hospital,id=id)
    if request.method=="POST":
        hospital.delete()
        messages.success(request,"Hospital deleted successfully.")

    return redirect("hospital_management" )

#----------------------------------------
# department management
#----------------------------------------

from django.core.paginator import Paginator
from django.db.models import Count


def department_management(request):

    department_list = Department.objects.annotate(
        hospital_count=Count("hospitaldepartment"),
        doctor_count=Count("doctor"),
    ).order_by("name")

    paginator = Paginator(department_list, 10)

    page_number = request.GET.get("page")
    departments = paginator.get_page(page_number)
    context = {
        "departments": departments,
        "department_count": Department.objects.count(),
        "hospital_department_count": HospitalDepartment.objects.count(),
        "doctor_count": Doctor.objects.count(),
    }
    return render(
        request,
        "departments/department_management.html",
        context,
    )
    
#---------------------------------------
# add department
#---------------------------------------
    
def department_add(request):

    if request.method == "POST":
        form = DepartmentForm(request.POST)
        if form.is_valid():
            department = form.save()
            hospitals = form.cleaned_data["hospitals"]
            for hospital in hospitals:
                HospitalDepartment.objects.create(
                    hospital=hospital,
                    department=department,
                )
            messages.success(
                request,
                "Department added successfully.",
            )
            return redirect("department_management")
    else:
        form = DepartmentForm()
    return render(
        request,
        "departments/department_form.html",
        {
            "form": form,
            "title": "Add Department",
        },
    )

#--------------------------------------
# edit deprtmnt
#--------------------------------------

def department_edit(request, id):

    department = get_object_or_404(
        Department,
        id=id,
    )
    if request.method == "POST":
        form = DepartmentForm(
            request.POST,
            instance=department,
        )
        if form.is_valid():
            department = form.save()
            HospitalDepartment.objects.filter(
                department=department
            ).delete()
            hospitals = form.cleaned_data["hospitals"]
            for hospital in hospitals:
                HospitalDepartment.objects.create(
                    hospital=hospital,
                    department=department,
                )
            messages.success(
                request,
                "Department updated successfully.",
            )
            return redirect("department_management")
    else:
        selected = Hospital.objects.filter(
            hospitaldepartment__department=department
        )
        form = DepartmentForm(
            instance=department,
            initial={
                "hospitals": selected,
            },
        )
    return render(
        request,
        "departments/department_form.html",
        {
            "form": form,
            "title": "Edit Department",
        },
    )
    
#--------------------------------------
# delete dprtmnt
#--------------------------------------

def department_delete(request, id):

    department = get_object_or_404(
        Department,
        id=id,
    )
    if Doctor.objects.filter(
        department=department
    ).exists():
        messages.error(
            request,
            "Cannot delete. Doctors are assigned to this department.",
        )
        return redirect(
            "department_management"
        )
    HospitalDepartment.objects.filter(
        department=department
    ).delete()
    department.delete()
    messages.success(
        request,
        "Department deleted successfully.",
    )
    return redirect(
        "department_management"
    )

#---------------------------------------
# doctor management
#---------------------------------------
    
from django.db.models import Avg

def doctor_management(request):

    doctor_list = Doctor.objects.select_related(
        "hospital",
        "department"
    ).order_by("name")
    paginator = Paginator(doctor_list,10)
    page_number = request.GET.get("page")
    doctors = paginator.get_page(page_number)
    context={
        "doctors":doctors,
        "doctor_count":Doctor.objects.count(),
        "active_count":Doctor.objects.filter(
            is_active=True
        ).count(),

        "leave_count":Doctor.objects.filter(
            is_on_leave=True
        ).count(),

        "average_rating":round(
            Doctor.objects.aggregate(
                avg=Avg("rating")
            )["avg"] or 0,
            1
        ),
    }

    return render(
        request,
        "doctors/doctor_management.html",
        context,

    )

#------------------------------------
# Add doctor
#------------------------------------

def doctor_add(request):

    if request.method=="POST":
        form=DoctorForm(
            request.POST,
            request.FILES,
        )
        
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Doctor added successfully."
            )
            
            return redirect(
                "doctor_management"
            )

    else:
        form=DoctorForm()

    return render(
        request,
        "doctors/doctor_form.html",
        {
            "form":form,
            "title":"Add Doctor",
        }
    )

#------------------------------------
# Doctor edit
#------------------------------------

def doctor_edit(request,id):

    doctor=get_object_or_404(
        Doctor,
        id=id,
    )

    if request.method=="POST":
        form=DoctorForm(
            request.POST,
            request.FILES,
            instance=doctor,
        )
        
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Doctor updated successfully."
            )

            return redirect(
                "doctor_management"
            )

    else:
        form=DoctorForm(
            instance=doctor,
        )

    return render(
        request,
        "doctors/doctor_form.html",
        {
           "form":form,
            "title":"Edit Doctor",
        }
    )
    
#-------------------------------------
# delete doctor
#-------------------------------------

def doctor_delete(request,id):

    doctor=get_object_or_404(
        Doctor,
        id=id,
    )
    doctor.delete()
    messages.success(
        request,
        "Doctor deleted successfully."
    )

    return redirect(
        "doctor_management"
    )
    
#---------------------------------------
# Schedule Management
#---------------------------------------

from django.db.models import Case, When, IntegerField

def schedule_management(request):

    schedule_list = DoctorSchedule.objects.select_related(
        "doctor",
        "doctor__hospital",
        "doctor__department",
    ).annotate(
    day_order=Case(
        When(day_of_week="Monday", then=1),
        When(day_of_week="Tuesday", then=2),
        When(day_of_week="Wednesday", then=3),
        When(day_of_week="Thursday", then=4),
        When(day_of_week="Friday", then=5),
        When(day_of_week="Saturday", then=6),
        When(day_of_week="Sunday", then=7),
        output_field=IntegerField(),
    )
    ).order_by(
        "doctor__name",
        "day_order",
    )

    paginator = Paginator(schedule_list, 10)

    page_number = request.GET.get("page")

    schedules = paginator.get_page(page_number)

    context = {

        "schedules": schedules,

        "schedule_count": DoctorSchedule.objects.count(),

        "doctor_count": Doctor.objects.count(),

        "average_slot_duration": round(
            DoctorSchedule.objects.aggregate(
                avg=Avg("slot_duration")
            )["avg"] or 0,
            1,
        ),

        "working_doctors": Doctor.objects.filter(
            is_active=True,
            is_on_leave=False,
        ).count(),

    }

    return render(
        request,
        "schedules/schedule_management.html",
        context,
    )
    
#---------------------------------------
# Edit Schedule
#---------------------------------------

def schedule_edit(request, id):

    schedule = get_object_or_404(
        DoctorSchedule,
        id=id,
    )

    if request.method == "POST":

        form = DoctorScheduleForm(
            request.POST,
            instance=schedule,
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Schedule updated successfully."
            )

            return redirect(
                "schedule_management"
            )

    else:

        form = DoctorScheduleForm(
            instance=schedule,
        )

    return render(
        request,
        "schedules/schedule_form.html",
        {
            "form": form,
            "title": "Edit Schedule",
        },
    )
    
#---------------------------------------
# Add Schedule
#---------------------------------------

def schedule_add(request):

    if request.method == "POST":

        form = DoctorScheduleForm(request.POST)

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Schedule added successfully."
            )

            return redirect(
                "schedule_management"
            )

    else:

        form = DoctorScheduleForm()

    return render(
        request,
        "schedules/schedule_form.html",
        {
            "form": form,
            "title": "Add Schedule",
        },
    )
    
#---------------------------------------
# Delete Schedule
#---------------------------------------

def schedule_delete(request, id):

    schedule = get_object_or_404(
        DoctorSchedule,
        id=id,
    )

    schedule.delete()

    messages.success(
        request,
        "Schedule deleted successfully."
    )

    return redirect(
        "schedule_management"
    )

#--------------------------------------
# appointment management
#--------------------------------------

from django.core.paginator import Paginator

def appointment_management(request):

    appointments = Appointment.objects.select_related(
        "patient",
        "doctor",
        "doctor__hospital",
        "doctor__department",
    ).order_by(
        "-appointment_date",
        "time_slot",
    )

    # Filters
    status = request.GET.get("status")
    hospital = request.GET.get("hospital")
    department = request.GET.get("department")
    doctor = request.GET.get("doctor")
    date = request.GET.get("date")

    if status:
        appointments = appointments.filter(status=status)

    if hospital:
        appointments = appointments.filter(
            doctor__hospital_id=hospital
        )

    if department:
        appointments = appointments.filter(
            doctor__department_id=department
        )

    if doctor:
        appointments = appointments.filter(
            doctor_id=doctor
        )

    if date:
        appointments = appointments.filter(
            appointment_date=date
        )

    paginator = Paginator(appointments, 10)

    page = request.GET.get("page")

    appointments = paginator.get_page(page)

    context = {

        "appointments": appointments,

        "hospitals": Hospital.objects.all(),

        "departments": Department.objects.all(),

        "doctors": Doctor.objects.all(),

        "selected_status": status,

        "selected_hospital": hospital,

        "selected_department": department,

        "selected_doctor": doctor,

        "selected_date": date,

    }

    return render(
        request,
        "appointments/appointment_management.html",
        context,
    )
    
#---------------------------------------
# Rating Management
#---------------------------------------

from django.core.paginator import Paginator


def rating_management(request):

    rating_list = Rating.objects.select_related(
        "user",
        "doctor",
        "doctor__hospital",
        "appointment",
    ).order_by("-created_at")

    paginator = Paginator(
        rating_list,
        10
    )

    page_number = request.GET.get("page")

    ratings = paginator.get_page(
        page_number
    )

    context = {

        "ratings": ratings,

    }

    return render(

        request,

        "ratings/rating_management.html",

        context,

    )
    
#---------------------------------------
# Delete Rating
#---------------------------------------

def rating_delete(request, id):

    rating = get_object_or_404(

        Rating,

        id=id,

    )

    doctor = rating.doctor

    rating.delete()

    average = Rating.objects.filter(

        doctor=doctor

    ).aggregate(

        Avg("rating")

    )["rating__avg"] or 0

    doctor.rating = round(

        average,

        1,

    )

    doctor.save()

    messages.success(

        request,

        "Rating deleted successfully."

    )

    return redirect(

        "rating_management"

    )
    
#---------------------------------------
# Notification Management
#---------------------------------------

from django.core.paginator import Paginator

def notification_management(request):

    notification_list = Notification.objects.select_related(
        "patient",
        "appointment",
    ).order_by(
        "-created_at"
    )

    paginator = Paginator(
        notification_list,
        10
    )

    page_number = request.GET.get("page")

    notifications = paginator.get_page(
        page_number
    )

    context = {

        "notifications": notifications,

    }

    return render(

        request,

        "notifications/notification_management.html",

        context,

    )
    
#---------------------------------------
# Delete Notification
#---------------------------------------

def notification_delete(request, id):

    notification = get_object_or_404(

        Notification,

        id=id,

    )

    notification.delete()

    messages.success(

        request,

        "Notification deleted successfully."

    )

    return redirect(

        "notification_management"

    )

#-----------------------------------------
# Decorator to protect every doctor page
#-----------------------------------------

from functools import wraps


def doctor_required(view_func):

    @wraps(view_func)

    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:

            return redirect("doctor_login")

        try:

            Doctor.objects.get(

                user=request.user,

                is_active=True

            )

        except Doctor.DoesNotExist:

            logout(request)

            return redirect("doctor_login")

        return view_func(request, *args, **kwargs)

    return wrapper

#------------------------------------
# doctor login
#-------------------------------------

def doctor_login(request):

    if request.user.is_authenticated:
        try:
            Doctor.objects.get(user=request.user)
            return redirect("doctor_dashboard")
        except Doctor.DoesNotExist:
            pass

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            try:
                doctor = Doctor.objects.get(
                    user=user,
                    is_active=True
                )

                login(request, user)

                return redirect("doctor_dashboard")

            except Doctor.DoesNotExist:

                messages.error(
                    request,
                    "Doctor account not found."
                )

        else:

            messages.error(
                request,
                "Invalid username or password."
            )

    return render(
        request,
        "doctor/doctor_login.html"
    )
#------------------------------------
# Doctor logout
#------------------------------------

@doctor_required
def doctor_logout(request):

    if request.method == "POST":

        logout(request)

        return redirect("doctor_login")

    doctor = Doctor.objects.get(user=request.user)

    return render(
        request,
        "doctor/doctor_logout_confirm.html",
        {
            "doctor": doctor
        }
    )

#---------------------------------------
# doctor dashboard
#---------------------------------------

from datetime import date

@doctor_required
def doctor_dashboard(request):

    doctor = Doctor.objects.get(user=request.user)

    selected_date = request.GET.get("date")

    if selected_date:

        selected_date = datetime.strptime(
            selected_date,
            "%Y-%m-%d"
        ).date()

    else:

        selected_date = date.today()

    appointments = Appointment.objects.filter(
        doctor=doctor,
        appointment_date=selected_date
    ).select_related(
        "patient"
    ).order_by(
        "time_slot"
    )

    total_appointments = appointments.count()

    completed_count = appointments.filter(
        status="Completed"
    ).count()

    missed_count = appointments.filter(
        status="Missed"
    ).count()

    remaining_count = appointments.filter(
        status__in=["Booked", "Rescheduled"]
    ).count()

    context = {

        "doctor": doctor,

        "appointments": appointments,

        "total_appointments": total_appointments,

        "completed_count": completed_count,

        "missed_count": missed_count,
        
        "selected_date": selected_date,

        "remaining_count": remaining_count,

    }

    return render(
        request,
        "doctor/doctor_dashboard.html",
        context
    )
    
#--------------------------------------
#complete appointment-marked by doctor
#--------------------------------------
@doctor_required
def doctor_complete_appointment(request, appointment_id):

    doctor = Doctor.objects.get(user=request.user)

    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        doctor=doctor
    )

    if request.method == "POST":

        appointment.status = "Completed"

        appointment.save()

        messages.success(
            request,
            "Appointment marked as Completed."
        )

    return redirect("doctor_dashboard")

#-----------------------------------------
# missed appointment-marked by doctor
#-----------------------------------------

@doctor_required
def doctor_miss_appointment(request, appointment_id):

    doctor = Doctor.objects.get(user=request.user)

    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        doctor=doctor
    )

    if request.method == "POST":

        appointment.status = "Missed"

        appointment.save()

        messages.success(
            request,
            "Appointment marked as Missed."
        )

    return redirect("doctor_dashboard")

#---------------------------------------------
#doctor profile
#---------------------------------------------

@doctor_required
def doctor_profile(request):

    doctor = get_object_or_404(
        Doctor,
        user=request.user
    )

    context = {

        "doctor": doctor,

    }

    return render(
        request,
        "doctor/doctor_profile.html",
        context
    )

#--------------------------------------
# edit doctor profile
#-------------------------------------

@doctor_required
def doctor_edit_profile(request):

    doctor = Doctor.objects.get(user=request.user)

    if request.method == "POST":

        form = DoctorProfileForm(
            request.POST,
            request.FILES,
            instance=doctor
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Profile updated successfully."
            )

            return redirect("doctor_profile")

    else:

        form = DoctorProfileForm(instance=doctor)

    return render(
        request,
        "doctor/doctor_edit_profile.html",
        {
            "doctor": doctor,
            "form": form,
        }
    )
    
#-----------------------------------
# change password of dr
#-----------------------------------

@doctor_required
def doctor_change_password(request):

    doctor = Doctor.objects.get(user=request.user)

    if request.method == "POST":

        form = PasswordChangeForm(
            request.user,
            request.POST
        )

        form.fields["old_password"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Enter current password"
        })

        form.fields["new_password1"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Enter new password"
        })

        form.fields["new_password2"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Confirm new password"
        })

        if form.is_valid():

            user = form.save()

            update_session_auth_hash(
                request,
                user
            )

            messages.success(
                request,
                "Password changed successfully."
            )

            return redirect("doctor_change_password")

    else:

        form = PasswordChangeForm(request.user)

        form.fields["old_password"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Enter current password"
        })

        form.fields["new_password1"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Enter new password"
        })

        form.fields["new_password2"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Confirm new password"
        })

    return render(
        request,
        "doctor/doctor_change_password.html",
        {
            "doctor": doctor,
            "form": form,
        }
    )