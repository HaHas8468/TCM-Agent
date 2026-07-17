from rest_framework import serializers
from .models import MedicalRecord, RecordHerb, RecordFormula, Disease


class RecordHerbSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecordHerb
        fields = ['id', 'herb_name']


class RecordFormulaSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecordFormula
        fields = ['id', 'formula_name']


class MedicalRecordSerializer(serializers.ModelSerializer):
    herbs = RecordHerbSerializer(many=True, read_only=True)
    formulas = RecordFormulaSerializer(many=True, read_only=True)

    class Meta:
        model = MedicalRecord
        fields = ['id', 'title', 'disease_name', 'zheng_type', 'formula_name', 
                  'content', 'author', 'source', 'created_at', 'herbs', 'formulas']


class DiseaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Disease
        fields = ['id', 'name', 'pinyin', 'description']


class RecordSearchSerializer(serializers.Serializer):
    disease_name = serializers.CharField(required=False)
    zheng_type = serializers.CharField(required=False)
    formula_name = serializers.CharField(required=False)
