from django.contrib import admin
from .models import Herb, Meridian, HerbMeridian, Contraindication, Compatibility, ModernResearch

admin.site.register(Herb)
admin.site.register(Meridian)
admin.site.register(HerbMeridian)
admin.site.register(Contraindication)
admin.site.register(Compatibility)
admin.site.register(ModernResearch)
