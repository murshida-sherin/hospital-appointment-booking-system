from django import forms
from .models import Department, Hospital

class HospitalForm(forms.ModelForm):

    class Meta:

        model = Hospital

        fields = [
            "name",
            "city",
            "address",
            "location_name",
            "image",
        ]

        widgets = {

            "name": forms.TextInput(attrs={
                "class":"form-control",
                "placeholder":"Hospital Name",
            }),

            "city": forms.TextInput(attrs={
                "class":"form-control",
            }),

            "address": forms.Textarea(attrs={
                "class":"form-control",
                "rows":5,
                "placeholder":"Enter the complete hospital address...",
            }),

            "location_name": forms.TextInput(attrs={
                "class":"form-control",
            }),

        }
        
        
class DepartmentForm(forms.ModelForm):

    hospitals = forms.ModelMultipleChoiceField(
        queryset=Hospital.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    class Meta:

        model = Department

        fields = [
            "name",
            "description",
            "hospitals",
        ]

        widgets = {

            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter Department Name",
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Enter Description",
                }
            ),

        }
        

from .models import Doctor


class DoctorForm(forms.ModelForm):

    class Meta:

        model = Doctor

        fields = [
            "image",
            "name",
            "qualification",
            "hospital",
            "department",
            "experience_years",
            "fee",
            "phone",
            "email",
            "is_active",
            "is_on_leave",
        ]

        widgets = {

            "name": forms.TextInput(attrs={
                "class":"form-control",
                "placeholder":"Doctor Name",
            }),

            "qualification": forms.TextInput(attrs={
                "class":"form-control",
                "placeholder":"Qualification (MBBS, MD...)",
            }),

            "hospital": forms.Select(attrs={
                "class":"form-select",
            }),

            "department": forms.Select(attrs={
                "class":"form-select",
            }),

            "experience_years": forms.NumberInput(attrs={
                "class":"form-control",
            }),

            "fee": forms.NumberInput(attrs={
                "class":"form-control",
            }),

            "phone": forms.TextInput(attrs={
                "class":"form-control",
            }),

            "email": forms.EmailInput(attrs={
                "class":"form-control",
            }),

            "is_active": forms.CheckboxInput(attrs={
                "class":"form-check-input",
            }),

            "is_on_leave": forms.CheckboxInput(attrs={
                "class":"form-check-input",
            }),

        }
        

from django import forms
from .models import DoctorSchedule


class DoctorScheduleForm(forms.ModelForm):

    SLOT_CHOICES = [
        (10, "10 Minutes"),
        (15, "15 Minutes"),
        (20, "20 Minutes"),
        (30, "30 Minutes"),
        (45, "45 Minutes"),
        (60, "60 Minutes"),
    ]

    slot_duration = forms.ChoiceField(
        choices=SLOT_CHOICES,
        label="Slot Duration"
    )

    class Meta:
        model = DoctorSchedule

        fields = [
            "doctor",
            "day_of_week",
            "start_time",
            "end_time",
            "slot_duration",
        ]

        widgets = {

            "doctor": forms.Select(attrs={
                "class": "form-select"
            }),

            "day_of_week": forms.Select(attrs={
                "class": "form-select"
            }),

            "start_time": forms.TimeInput(
                attrs={
                    "class": "form-control",
                    "type": "time",
                }
            ),

            "end_time": forms.TimeInput(
                attrs={
                    "class": "form-control",
                    "type": "time",
                }
            ),
        }

    def clean_slot_duration(self):
        return int(self.cleaned_data["slot_duration"])



class DoctorLoginForm(forms.Form):

    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Username"
            }
        )
    )

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Password"
            }
        )
    )
    
    
    
    
from django import forms
from .models import Doctor


class DoctorProfileForm(forms.ModelForm):

    class Meta:
        model = Doctor

        fields = [
            "phone",
            "email",
            "image",
        ]

        widgets = {

            "phone": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter phone number"
            }),

            "email": forms.EmailInput(attrs={
                "class": "form-control",
                "placeholder": "Enter email address"
            }),

            "image": forms.ClearableFileInput(attrs={
                "class": "form-control"
            }),

        }