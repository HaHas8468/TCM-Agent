from rest_framework import serializers
from .models import Symptom, TongueSign, PulseSign, ZhengType, DiagnosisQuestion


class SymptomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Symptom
        fields = ['id', 'name', 'category', 'description']


class TongueSignSerializer(serializers.ModelSerializer):
    class Meta:
        model = TongueSign
        fields = ['id', 'name', 'description']


class PulseSignSerializer(serializers.ModelSerializer):
    class Meta:
        model = PulseSign
        fields = ['id', 'name', 'description']


class ZhengTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ZhengType
        fields = ['id', 'name', 'description', 'main_symptoms', 'typical_tongue', 'typical_pulse']


class DiagnosisQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiagnosisQuestion
        fields = ['id', 'question', 'question_type', 'zheng_type', 'order']


class DiagnosisInputSerializer(serializers.Serializer):
    symptoms = serializers.ListField(child=serializers.CharField())
    tongue = serializers.ListField(child=serializers.CharField(), required=False)
    pulse = serializers.ListField(child=serializers.CharField(), required=False)
    other_signs = serializers.CharField(required=False)


class DiagnosisResultSerializer(serializers.Serializer):
    zheng_type = serializers.CharField()
    confidence = serializers.FloatField()
    description = serializers.CharField()
    reasoning = serializers.CharField()
    recommended_formulas = serializers.ListField(child=serializers.DictField(), required=False)
