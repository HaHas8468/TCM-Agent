from django.contrib import admin
from .models import Symptom, TongueSign, PulseSign, ZhengType, DiagnosisQuestion

admin.site.register(Symptom)
admin.site.register(TongueSign)
admin.site.register(PulseSign)
admin.site.register(ZhengType)
admin.site.register(DiagnosisQuestion)
