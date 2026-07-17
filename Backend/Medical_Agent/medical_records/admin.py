from django.contrib import admin
from .models import MedicalRecord, RecordHerb, RecordFormula, Disease

admin.site.register(MedicalRecord)
admin.site.register(RecordHerb)
admin.site.register(RecordFormula)
admin.site.register(Disease)
