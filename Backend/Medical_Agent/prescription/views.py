from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Formula
from .serializers import FormulaSerializer, FormulaRecommendationSerializer, FormulaDetailSerializer
from knowledge_graph.queries import FormulaQueries, HerbQueries


class FormulaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Formula.objects.all()
    serializer_class = FormulaSerializer

    @action(detail=False, methods=['get'])
    def search(self, request):
        keyword = request.query_params.get('keyword', '')
        queryset = self.queryset.filter(name__icontains=keyword)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def recommend(self, request):
        serializer = FormulaRecommendationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        zheng_type = serializer.validated_data['zheng_type']
        
        try:
            kg_formulas = FormulaQueries.get_formulas_by_zheng(zheng_type)
            db_formulas = self.queryset.filter(formulaindication__zheng_type=zheng_type)
            
            result = []
            for kg_formula in kg_formulas:
                formula_detail = FormulaQueries.get_formula_details(kg_formula['formula_name'])
                if formula_detail:
                    herbs_detail = []
                    for herb_name in formula_detail.get('herbs', []):
                        herb = HerbQueries.get_herb_details(herb_name)
                        if herb:
                            herbs_detail.append(herb)
                    formula_detail['herbs_detail'] = herbs_detail
                result.append(formula_detail or kg_formula)
            
            db_result = self.get_serializer(db_formulas.distinct(), many=True).data
            
            return Response({
                "knowledge_graph_results": result,
                "database_results": db_result
            })
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def detail(self, request):
        serializer = FormulaDetailSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        formula_name = serializer.validated_data['formula_name']
        
        try:
            formula_detail = FormulaQueries.get_formula_details(formula_name)
            if formula_detail:
                herbs_detail = []
                for herb_name in formula_detail.get('herbs', []):
                    herb = HerbQueries.get_herb_details(herb_name)
                    if herb:
                        herbs_detail.append(herb)
                formula_detail['herbs_detail'] = herbs_detail
            return Response(formula_detail)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
