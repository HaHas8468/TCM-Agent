from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Symptom, TongueSign, PulseSign, ZhengType, DiagnosisQuestion
from .serializers import SymptomSerializer, TongueSignSerializer, PulseSignSerializer, \
    ZhengTypeSerializer, DiagnosisQuestionSerializer, DiagnosisInputSerializer, DiagnosisResultSerializer
from knowledge_graph.queries import DiagnosisQueries, FormulaQueries
from knowledge_graph.nlp import entity_recognizer, zheng_classifier


class SymptomViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Symptom.objects.all()
    serializer_class = SymptomSerializer

    @action(detail=False, methods=['get'])
    def search(self, request):
        keyword = request.query_params.get('keyword', '')
        queryset = self.queryset.filter(name__icontains=keyword)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class TongueSignViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TongueSign.objects.all()
    serializer_class = TongueSignSerializer


class PulseSignViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PulseSign.objects.all()
    serializer_class = PulseSignSerializer


class ZhengTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ZhengType.objects.all()
    serializer_class = ZhengTypeSerializer

    @action(detail=False, methods=['get'])
    def by_symptoms(self, request):
        symptoms = request.query_params.getlist('symptoms', [])
        if not symptoms:
            return Response({"error": "请提供症状列表"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            results = DiagnosisQueries.get_zheng_by_symptoms(symptoms)
            return Response(results)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DiagnosisQuestionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DiagnosisQuestion.objects.all().order_by('order')
    serializer_class = DiagnosisQuestionSerializer

    @action(detail=False, methods=['get'])
    def by_zheng(self, request):
        zheng_type = request.query_params.get('zheng_type', '')
        if not zheng_type:
            return Response({"error": "请提供证型"}, status=status.HTTP_400_BAD_REQUEST)
        queryset = self.queryset.filter(zheng_type__name=zheng_type)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class DiagnosisViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['post'])
    def classify(self, request):
        serializer = DiagnosisInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        symptoms = data.get('symptoms', [])
        tongue = data.get('tongue', [])
        pulse = data.get('pulse', [])
        other_signs = data.get('other_signs', '')

        try:
            kg_results = DiagnosisQueries.get_zheng_by_symptoms(symptoms)
            llm_result = zheng_classifier.classify_zheng(symptoms, tongue, pulse, other_signs)
            
            result = {
                "zheng_type": llm_result.get('zheng_type', '未确定'),
                "confidence": llm_result.get('confidence', 0),
                "description": llm_result.get('description', ''),
                "reasoning": llm_result.get('reasoning', ''),
                "knowledge_graph_matches": kg_results
            }

            if result['zheng_type'] != '未确定':
                formulas = FormulaQueries.get_formulas_by_zheng(result['zheng_type'])
                result['recommended_formulas'] = formulas

            return Response(result)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def extract_entities(self, request):
        text = request.data.get('text', '')
        if not text:
            return Response({"error": "请提供文本内容"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            entities = entity_recognizer.extract_entities_with_llm(text)
            return Response(entities)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
