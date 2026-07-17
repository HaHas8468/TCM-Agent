from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Herb, Meridian
from .serializers import HerbSerializer, MeridianSerializer, HerbSearchSerializer, \
    HerbPropertyFilterSerializer, HerbMeridianFilterSerializer
from knowledge_graph.queries import HerbQueries


class HerbViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Herb.objects.all()
    serializer_class = HerbSerializer

    @action(detail=False, methods=['get'])
    def search(self, request):
        keyword = request.query_params.get('keyword', '')
        if not keyword:
            return Response({"error": "请提供搜索关键词"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            kg_results = HerbQueries.search_herbs(keyword)
            db_results = self.queryset.filter(name__icontains=keyword)
            
            return Response({
                "knowledge_graph_results": kg_results,
                "database_results": self.get_serializer(db_results, many=True).data
            })
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def by_property(self, request):
        property_name = request.query_params.get('property_name', '')
        if not property_name:
            return Response({"error": "请提供药性名称"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            kg_results = HerbQueries.get_herbs_by_property(property_name)
            db_results = self.queryset.filter(property=property_name)
            
            return Response({
                "knowledge_graph_results": kg_results,
                "database_results": self.get_serializer(db_results, many=True).data
            })
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def by_meridian(self, request):
        meridian_name = request.query_params.get('meridian_name', '')
        if not meridian_name:
            return Response({"error": "请提供经络名称"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            kg_results = HerbQueries.get_herbs_by_meridian(meridian_name)
            db_results = self.queryset.filter(herbmeridian__meridian__name=meridian_name)
            
            return Response({
                "knowledge_graph_results": kg_results,
                "database_results": self.get_serializer(db_results.distinct(), many=True).data
            })
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def detail(self, request):
        herb_name = request.data.get('herb_name', '')
        if not herb_name:
            return Response({"error": "请提供中药名称"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            kg_detail = HerbQueries.get_herb_details(herb_name)
            db_detail = self.queryset.filter(name=herb_name).first()
            
            result = {}
            if kg_detail:
                result['knowledge_graph_detail'] = kg_detail
            if db_detail:
                result['database_detail'] = self.get_serializer(db_detail).data
            
            return Response(result if result else {"error": "未找到该中药信息"}, status=status.HTTP_404_NOT_FOUND if not result else status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MeridianViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Meridian.objects.all()
    serializer_class = MeridianSerializer
