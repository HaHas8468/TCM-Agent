from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import MedicalRecord, Disease
from .serializers import MedicalRecordSerializer, DiseaseSerializer, RecordSearchSerializer
from knowledge_graph.queries import MedicalRecordQueries


class MedicalRecordViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MedicalRecord.objects.all()
    serializer_class = MedicalRecordSerializer

    @action(detail=False, methods=['get'])
    def search(self, request):
        disease_name = request.query_params.get('disease_name', '')
        zheng_type = request.query_params.get('zheng_type', '')
        formula_name = request.query_params.get('formula_name', '')
        
        try:
            kg_results = MedicalRecordQueries.search_records(disease_name, zheng_type, formula_name)
            
            queryset = self.queryset
            if disease_name:
                queryset = queryset.filter(disease_name__icontains=disease_name)
            if zheng_type:
                queryset = queryset.filter(zheng_type__icontains=zheng_type)
            if formula_name:
                queryset = queryset.filter(formula_name__icontains=formula_name)
            
            db_results = self.get_serializer(queryset, many=True).data
            
            return Response({
                "knowledge_graph_results": kg_results,
                "database_results": db_results
            })
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def detail(self, request):
        title = request.data.get('title', '')
        if not title:
            return Response({"error": "请提供医案标题"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            kg_detail = MedicalRecordQueries.get_record_details(title)
            db_detail = self.queryset.filter(title=title).first()
            
            result = {}
            if kg_detail:
                result['knowledge_graph_detail'] = kg_detail
            if db_detail:
                result['database_detail'] = self.get_serializer(db_detail).data
            
            return Response(result if result else {"error": "未找到该医案"}, status=status.HTTP_404_NOT_FOUND if not result else status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DiseaseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Disease.objects.all()
    serializer_class = DiseaseSerializer

    @action(detail=False, methods=['get'])
    def search(self, request):
        keyword = request.query_params.get('keyword', '')
        queryset = self.queryset.filter(name__icontains=keyword)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
