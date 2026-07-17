from django.contrib import admin
from .models import Formula, FormulaHerb, FormulaIndication, Modification, Pharmacology

admin.site.register(Formula)
admin.site.register(FormulaHerb)
admin.site.register(FormulaIndication)
admin.site.register(Modification)
admin.site.register(Pharmacology)
