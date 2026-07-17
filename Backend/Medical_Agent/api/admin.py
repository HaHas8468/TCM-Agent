from django.contrib import admin
from .models import Patient, Doctor, DiagnosisSession, Prescription, MedicalRecord

admin.site.register(Patient)
admin.site.register(Doctor)
admin.site.register(DiagnosisSession)
admin.site.register(Prescription)
admin.site.register(MedicalRecord)
