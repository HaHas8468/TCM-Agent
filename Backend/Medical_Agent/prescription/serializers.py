from rest_framework import serializers
from .models import Formula, FormulaHerb, FormulaIndication, Modification, Pharmacology


class FormulaHerbSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormulaHerb
        fields = ['id', 'herb_name', 'dosage', 'role']


class FormulaIndicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormulaIndication
        fields = ['id', 'zheng_type', 'description']


class ModificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Modification
        fields = ['id', 'condition', 'modification']


class PharmacologySerializer(serializers.ModelSerializer):
    class Meta:
        model = Pharmacology
        fields = ['id', 'content', 'source']


class FormulaSerializer(serializers.ModelSerializer):
    herbs = FormulaHerbSerializer(many=True, read_only=True)
    indications = FormulaIndicationSerializer(many=True, read_only=True)
    modifications = ModificationSerializer(many=True, read_only=True)
    pharmacology = PharmacologySerializer(many=True, read_only=True)

    class Meta:
        model = Formula
        fields = ['id', 'name', 'pinyin', 'description', 'effect', 'source', 
                  'decoction_method', 'herbs', 'indications', 'modifications', 'pharmacology']


class FormulaRecommendationSerializer(serializers.Serializer):
    zheng_type = serializers.CharField()


class FormulaDetailSerializer(serializers.Serializer):
    formula_name = serializers.CharField()
