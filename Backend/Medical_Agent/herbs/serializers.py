from rest_framework import serializers
from .models import Herb, Meridian, HerbMeridian, Contraindication, Compatibility, ModernResearch


class MeridianSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meridian
        fields = ['id', 'name']


class HerbMeridianSerializer(serializers.ModelSerializer):
    meridian = MeridianSerializer(read_only=True)

    class Meta:
        model = HerbMeridian
        fields = ['id', 'meridian']


class ContraindicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contraindication
        fields = ['id', 'content']


class CompatibilitySerializer(serializers.ModelSerializer):
    target_herb_name = serializers.CharField(source='target_herb.name', read_only=True)

    class Meta:
        model = Compatibility
        fields = ['id', 'target_herb_name', 'relationship', 'description']


class ModernResearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModernResearch
        fields = ['id', 'content', 'source']


class HerbSerializer(serializers.ModelSerializer):
    meridians = HerbMeridianSerializer(many=True, read_only=True)
    contraindications = ContraindicationSerializer(many=True, read_only=True)
    compatibility = CompatibilitySerializer(many=True, read_only=True)
    modern_research = ModernResearchSerializer(many=True, read_only=True)

    class Meta:
        model = Herb
        fields = ['id', 'name', 'pinyin', 'property', 'flavor', 'effect', 'dosage', 
                  'description', 'meridians', 'contraindications', 'compatibility', 'modern_research']


class HerbSearchSerializer(serializers.Serializer):
    keyword = serializers.CharField()


class HerbPropertyFilterSerializer(serializers.Serializer):
    property_name = serializers.CharField()


class HerbMeridianFilterSerializer(serializers.Serializer):
    meridian_name = serializers.CharField()
