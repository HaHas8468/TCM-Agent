import uuid
import logging
from datetime import datetime, timedelta

from rest_framework import viewsets, permissions, status, mixins
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.db import transaction

from .models import Patient, Doctor, Department, Schedule, Order, Chat, ChatMessage, ClinicRecord, Collection, Notification
from .serializers import PatientSerializer, DoctorSerializer, DepartmentSerializer, ScheduleSerializer, OrderSerializer, ChatSerializer, ChatMessageSerializer, ClinicRecordSerializer, CollectionSerializer, NotificationSerializer


logger = logging.getLogger(__name__)


class LoginViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['post'])
    def login(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        user = authenticate(username=username, password=password)
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            
            try:
                patient = Patient.objects.get(user=user)
                role = 'patient'
                return Response({
                    'token': token.key,
                    'patient_id': patient.patient_id,
                    'name': patient.name
                })
            except Patient.DoesNotExist:
                try:
                    doctor = Doctor.objects.get(user=user)
                    role = 'doctor'
                    return Response({
                        'token': token.key,
                        'doctor_id': doctor.doctor_id,
                        'name': doctor.name,
                        'department': doctor.department.name if doctor.department else '',
                        'default_landing': 'queue'
                    })
                except Doctor.DoesNotExist:
                    return Response({
                        'token': token.key,
                        'user_id': user.id,
                        'username': user.username,
                        'role': 'admin'
                    })
        return Response({'code': 401, 'msg': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

    @action(detail=False, methods=['post'])
    def register(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        confirm_password = request.data.get('confirm_password')
        
        if password != confirm_password:
            return Response({'code': 400, 'msg': 'Passwords do not match'}, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(username=username).exists():
            return Response({'code': 400, 'msg': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.create_user(username=username, password=password)
        
        patient = Patient.objects.create(
            user=user,
            patient_id=f'P{datetime.now().strftime("%Y%m%d%H%M%S")}{user.id}',
            name=username,
            gender='男',
            age=0
        )
        
        return Response({'code': 0, 'data': {'patient_id': patient.patient_id}}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def logout(self, request):
        request.user.auth_token.delete()
        return Response({'code': 0, 'data': None})


class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        try:
            patient = Patient.objects.get(user=user)
            return Patient.objects.filter(id=patient.id)
        except Patient.DoesNotExist:
            return Patient.objects.none()

    @action(detail=False, methods=['get'])
    def profile(self, request):
        try:
            patient = Patient.objects.get(user=request.user)
            serializer = PatientSerializer(patient)
            data = serializer.data
            if data.get('allergy_history') and isinstance(data['allergy_history'], str):
                import json
                data['allergy_history'] = json.loads(data['allergy_history'])
            return Response({'code': 0, 'data': data})
        except Patient.DoesNotExist:
            return Response({'code': 404, 'msg': 'Patient profile not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['put'])
    def update_profile(self, request):
        try:
            patient = Patient.objects.get(user=request.user)
            serializer = PatientSerializer(patient, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'code': 0, 'data': None})
            return Response({'code': 400, 'msg': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Patient.DoesNotExist:
            return Response({'code': 404, 'msg': 'Patient profile not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def diagnosis_history(self, request):
        try:
            patient = Patient.objects.get(user=request.user)
            status_filter = request.query_params.get('status', 'all')
            
            orders = Order.objects.filter(patient=patient)
            if status_filter != 'all':
                orders = orders.filter(status=status_filter)
            
            result = []
            for order in orders:
                doctor_info = {
                    'doctor_id': order.doctor.doctor_id,
                    'name': order.doctor.name
                } if order.doctor else None
                
                advice_list = order.advice.split(',') if order.advice else []
                
                result.append({
                    'order_id': order.order_id,
                    'doctor': doctor_info,
                    'department': order.department_name or (order.department.name if order.department else ''),
                    'date': order.date.isoformat() if order.date else order.created_at.isoformat(),
                    'status': order.status,
                    'symptoms_summary': ', '.join(order.symptoms) if order.symptoms else '',
                    'diagnosis_summary': f"{order.syndrome}, {order.prescription}" if order.syndrome and order.prescription else '',
                    'advice_list': advice_list
                })
            
            return Response({'code': 0, 'data': result})
        except Patient.DoesNotExist:
            return Response({'code': 404, 'msg': 'Patient not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def latest_diagnosis(self, request):
        try:
            patient = Patient.objects.get(user=request.user)
            order = Order.objects.filter(patient=patient, status='finished').order_by('-updated_at').first()
            
            if not order:
                return Response({'code': 0, 'data': None})
            
            advice_list = order.advice.split(',') if order.advice else []
            
            data = {
                'order_id': order.order_id,
                'syndrome': order.syndrome,
                'prescription': order.prescription,
                'department': order.department_name or (order.department.name if order.department else ''),
                'diagnosis_basis': f"根据您症状，辨证为{order.syndrome}" if order.syndrome else '',
                'advice_list': advice_list,
                'sync_time': order.updated_at.isoformat()
            }
            
            return Response({'code': 0, 'data': data})
        except Patient.DoesNotExist:
            return Response({'code': 404, 'msg': 'Patient not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        try:
            patient = Patient.objects.get(patient_id=pk)
            records = ClinicRecord.objects.filter(patient=patient).order_by('-visit_date')
            
            history_syndromes = []
            for record in records:
                history_syndromes.append({
                    'date': record.visit_date.strftime('%Y-%m-%d'),
                    'syndrome': record.zheng_type,
                    'prescription': record.prescription
                })
            
            data = {
                'patient_id': patient.patient_id,
                'history_syndromes': history_syndromes,
                'allergy_history': patient.allergy_history or []
            }
            
            return Response({'code': 0, 'data': data})
        except Patient.DoesNotExist:
            return Response({'code': 404, 'msg': 'Patient not found'}, status=status.HTTP_404_NOT_FOUND)


class DoctorViewSet(viewsets.ModelViewSet):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        try:
            doctor = Doctor.objects.get(user=user)
            return Doctor.objects.filter(id=doctor.id)
        except Doctor.DoesNotExist:
            if user.is_staff:
                return Doctor.objects.all()
            return Doctor.objects.none()

    @action(detail=False, methods=['get'])
    def profile(self, request):
        try:
            doctor = Doctor.objects.get(user=request.user)
            serializer = DoctorSerializer(doctor)
            data = serializer.data
            data['role'] = 'doctor'
            return Response({'code': 0, 'data': data})
        except Doctor.DoesNotExist:
            return Response({'code': 404, 'msg': 'Doctor profile not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['put'])
    def update_profile(self, request):
        try:
            doctor = Doctor.objects.get(user=request.user)
            serializer = DoctorSerializer(doctor, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'code': 0, 'data': None})
            return Response({'code': 400, 'msg': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Doctor.DoesNotExist:
            return Response({'code': 404, 'msg': 'Doctor profile not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def queue(self, request):
        try:
            doctor = Doctor.objects.get(user=request.user)
            date_str = request.query_params.get('date', datetime.now().date().isoformat())
            department = request.query_params.get('department', '')
            period = request.query_params.get('period', 'all')
            
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            orders = Order.objects.filter(doctor=doctor, date=date)
            
            if department:
                orders = orders.filter(department__name=department)
            
            result = []
            for order in orders:
                result.append({
                    'order_id': order.order_id,
                    'patient_id': order.patient.patient_id,
                    'patient_name': order.patient.name,
                    'department': order.department_name or (order.department.name if order.department else ''),
                    'time': order.time,
                    'status': order.status
                })
            
            today_total = orders.count()
            pending = orders.filter(status='pending').count()
            ongoing = orders.filter(status='ongoing').count()
            finished = orders.filter(status='finished').count()
            
            return Response({
                'code': 0,
                'data': result,
                'kpi': {
                    'today_total': today_total,
                    'pending': pending,
                    'ongoing': ongoing,
                    'finished': finished
                }
            })
        except Doctor.DoesNotExist:
            return Response({'code': 404, 'msg': 'Doctor not found'}, status=status.HTTP_404_NOT_FOUND)


class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def list_with_doctors(self, request):
        departments = Department.objects.all()
        result = []
        
        for dept in departments:
            doctors = Doctor.objects.filter(department=dept)
            doctor_list = []
            for doc in doctors:
                doctor_list.append({
                    'doctor_id': doc.doctor_id,
                    'name': doc.name,
                    'specialty': doc.specialty
                })
            
            if doctor_list:
                result.append({
                    'department': dept.name,
                    'doctors': doctor_list
                })
        
        return Response({'code': 0, 'data': result})


class ScheduleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def slots_by_doctor(self, request):
        doctor_id = request.query_params.get('doctor_id')
        date_str = request.query_params.get('date', datetime.now().date().isoformat())
        
        if not doctor_id:
            return Response({'code': 400, 'msg': 'doctor_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            doctor = Doctor.objects.get(doctor_id=doctor_id)
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            schedules = Schedule.objects.filter(doctor=doctor, date=date, status='available', available_slots__gt=0)
            
            available_slots = []
            for schedule in schedules:
                start = schedule.start_time
                end = schedule.end_time
                current = start
                
                while current < end:
                    available_slots.append(current.strftime('%H:%M'))
                    current = (datetime.combine(date, current) + timedelta(hours=1)).time()
            
            return Response({
                'code': 0,
                'data': {
                    'doctor_id': doctor_id,
                    'date': date_str,
                    'available_slots': available_slots
                }
            })
        except Doctor.DoesNotExist:
            return Response({'code': 404, 'msg': 'Doctor not found'}, status=status.HTTP_404_NOT_FOUND)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        try:
            patient = Patient.objects.get(user=user)
            return Order.objects.filter(patient=patient)
        except Patient.DoesNotExist:
            try:
                doctor = Doctor.objects.get(user=user)
                return Order.objects.filter(doctor=doctor)
            except Doctor.DoesNotExist:
                if user.is_staff:
                    return Order.objects.all()
                return Order.objects.none()

    def create(self, request):
        try:
            patient = Patient.objects.get(user=request.user)
        except Patient.DoesNotExist:
            return Response({'code': 404, 'msg': 'Patient not found'}, status=status.HTTP_404_NOT_FOUND)

        doctor_id = request.data.get('doctor_id')
        department = request.data.get('department')
        date_str = request.data.get('date')
        time = request.data.get('time')
        source = request.data.get('source', 'direct')
        
        if not doctor_id or not date_str or not time:
            return Response({'code': 400, 'msg': 'doctor_id, date, time are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            doctor = Doctor.objects.get(doctor_id=doctor_id)
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            order_id = f'O{datetime.now().strftime("%Y%m%d%H%M%S")}{uuid.uuid4().hex[:8]}'
            
            order = Order.objects.create(
                order_id=order_id,
                patient=patient,
                doctor=doctor,
                department=doctor.department,
                department_name=department,
                date=date,
                time=time,
                source=source,
                status='pending'
            )
            
            return Response({
                'code': 0,
                'data': {
                    'order_id': order.order_id,
                    'status': order.status,
                    'doctor_id': doctor_id,
                    'date': date_str,
                    'time': time
                }
            }, status=status.HTTP_201_CREATED)
        except Doctor.DoesNotExist:
            return Response({'code': 404, 'msg': 'Doctor not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['put'])
    def start(self, request, pk=None):
        try:
            order = Order.objects.get(order_id=pk)
        except Order.DoesNotExist:
            return Response({'code': 404, 'msg': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

        if order.status != 'pending':
            return Response({'code': 400, 'msg': 'Order is not pending'}, status=status.HTTP_400_BAD_REQUEST)

        order.status = 'ongoing'
        order.save()

        return Response({'code': 0, 'data': {'order_id': order.order_id, 'status': order.status}})

    @action(detail=True, methods=['put'])
    def finish(self, request, pk=None):
        try:
            order = Order.objects.get(order_id=pk)
        except Order.DoesNotExist:
            return Response({'code': 404, 'msg': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

        if order.status not in ['pending', 'ongoing']:
            return Response({'code': 400, 'msg': 'Order cannot be finished'}, status=status.HTTP_400_BAD_REQUEST)

        order.status = 'finished'
        order.syndrome = request.data.get('syndrome')
        order.prescription = request.data.get('prescription')
        order.ingredients = request.data.get('ingredients')
        order.advice = request.data.get('advice')
        order.save()

        # 创建病历记录，疗法存入 chief_complaint，注意事项存入 history_of_present_illness
        therapy = request.data.get('therapy')
        precautions = request.data.get('precautions')
        record_id = f'R{datetime.now().strftime("%Y%m%d%H%M%S")}{uuid.uuid4().hex[:8]}'
        ClinicRecord.objects.create(
            record_id=record_id,
            patient=order.patient,
            doctor=order.doctor,
            order=order,
            chief_complaint=therapy or order.chief_complaint or "",
            history_of_present_illness=precautions or order.present_illness or "",
            tongue=order.tongue or "",
            pulse=order.pulse or "",
            zheng_type=order.syndrome or "",
            prescription=order.prescription or "",
            ingredients=order.ingredients,
            advice=order.advice or "",
        )

        return Response({'code': 0, 'data': {'order_id': order.order_id, 'status': order.status}})

    @action(detail=True, methods=['put'])
    def save(self, request, pk=None):
        try:
            order = Order.objects.get(order_id=pk)
        except Order.DoesNotExist:
            return Response({'code': 404, 'msg': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

        if order.status not in ['pending', 'ongoing']:
            return Response({'code': 400, 'msg': 'Order cannot be saved'}, status=status.HTTP_400_BAD_REQUEST)

        if order.status == 'pending':
            order.status = 'ongoing'
        
        if 'syndrome' in request.data:
            order.syndrome = request.data['syndrome']
        if 'prescription' in request.data:
            order.prescription = request.data['prescription']
        if 'ingredients' in request.data:
            order.ingredients = request.data['ingredients']
        if 'advice' in request.data:
            order.advice = request.data['advice']
        
        order.save()

        return Response({'code': 0, 'data': {'order_id': order.order_id, 'status': order.status}})

    @action(detail=True, methods=['post'])
    def diagnosis(self, request, pk=None):
        try:
            order = Order.objects.get(order_id=pk)
        except Order.DoesNotExist:
            return Response({'code': 404, 'msg': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

        order.chief_complaint = request.data.get('chief_complaint')
        order.present_illness = request.data.get('present_illness')
        order.tongue = request.data.get('tongue')
        order.pulse = request.data.get('pulse')
        order.symptoms = request.data.get('symptoms')
        order.signs = request.data.get('signs')
        order.other = request.data.get('other')
        order.save()

        return Response({'code': 0, 'data': {'order_id': order.order_id}})

    @action(detail=True, methods=['get'])
    def detail(self, request, pk=None):
        try:
            order = Order.objects.get(order_id=pk)
            records = ClinicRecord.objects.filter(order=order)
            
            if records.exists():
                record = records.first()
                serializer = ClinicRecordSerializer(record)
                data = serializer.data
                data['order_id'] = order.order_id
                return Response({'code': 0, 'data': data})
            
            doctor_info = {
                'doctor_id': order.doctor.doctor_id,
                'name': order.doctor.name
            } if order.doctor else None
            
            patient_info = {
                'patient_id': order.patient.patient_id,
                'name': order.patient.name,
                'gender': order.patient.gender,
                'age': order.patient.age
            }
            
            data = {
                'order_id': order.order_id,
                'patient': patient_info,
                'doctor': doctor_info,
                'chief_complaint': order.chief_complaint,
                'present_illness': order.present_illness,
                'tongue': order.tongue,
                'pulse': order.pulse,
                'syndrome': order.syndrome,
                'prescription': order.prescription,
                'ingredients': order.ingredients,
                'advice': order.advice,
                'date': order.visit_date.isoformat() if order.visit_date else order.created_at.isoformat()
            }
            
            return Response({'code': 0, 'data': data})
        except Order.DoesNotExist:
            return Response({'code': 404, 'msg': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)


class ClinicRecordViewSet(viewsets.ModelViewSet):
    queryset = ClinicRecord.objects.all()
    serializer_class = ClinicRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        try:
            patient = Patient.objects.get(user=user)
            return ClinicRecord.objects.filter(patient=patient)
        except Patient.DoesNotExist:
            try:
                doctor = Doctor.objects.get(user=user)
                return ClinicRecord.objects.filter(doctor=doctor)
            except Doctor.DoesNotExist:
                if user.is_staff:
                    return ClinicRecord.objects.all()
                return ClinicRecord.objects.none()

    def create(self, request):
        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            return Response({'code': 404, 'msg': 'Doctor not found'}, status=status.HTTP_404_NOT_FOUND)

        record_id = f'R{datetime.now().strftime("%Y%m%d%H%M%S")}{uuid.uuid4().hex[:8]}'

        record = ClinicRecord.objects.create(
            record_id=record_id,
            doctor=doctor,
            patient_id=request.data.get('patient_id'),
            order_id=request.data.get('order_id'),
            chief_complaint=request.data.get('chief_complaint', ''),
            history_of_present_illness=request.data.get('history_of_present_illness'),
            past_history=request.data.get('past_history'),
            physical_examination=request.data.get('physical_examination'),
            tongue=request.data.get('tongue'),
            pulse=request.data.get('pulse'),
            other_signs=request.data.get('other_signs'),
            zheng_type=request.data.get('zheng_type'),
            zheng_description=request.data.get('zheng_description'),
            diagnosis=request.data.get('diagnosis'),
            treatment_principle=request.data.get('treatment_principle'),
            treatment_plan=request.data.get('treatment_plan'),
            prescription=request.data.get('prescription'),
            herbs=request.data.get('herbs'),
            ingredients=request.data.get('ingredients'),
            dosage=request.data.get('dosage'),
            decoction_method=request.data.get('decoction_method'),
            advice=request.data.get('advice'),
            notes=request.data.get('notes'),
            follow_up=request.data.get('follow_up')
        )

        if request.data.get('order_id'):
            try:
                order = Order.objects.get(id=request.data.get('order_id'))
                order.status = 'finished'
                order.save()
            except Order.DoesNotExist:
                pass

        serializer = ClinicRecordSerializer(record)
        return Response({'code': 0, 'data': serializer.data}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def search(self, request):
        name = request.query_params.get('name', '')
        patient_id = request.query_params.get('patient_id', '')
        syndrome = request.query_params.get('syndrome', '')
        date_from = request.query_params.get('date_from', '')
        date_to = request.query_params.get('date_to', '')
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))

        records = ClinicRecord.objects.all()
        
        if name:
            records = records.filter(patient__name__icontains=name)
        if patient_id:
            records = records.filter(patient__patient_id=patient_id)
        if syndrome:
            records = records.filter(zheng_type__icontains=syndrome)
        if date_from:
            records = records.filter(visit_date__gte=date_from)
        if date_to:
            records = records.filter(visit_date__lte=date_to)

        total = records.count()
        records = records[(page-1)*page_size:page*page_size]

        result = []
        for record in records:
            result.append({
                'record_id': record.record_id,
                'patient': {
                    'patient_id': record.patient.patient_id,
                    'name': record.patient.name
                },
                'syndrome': record.zheng_type,
                'prescription': record.prescription,
                'therapy': record.chief_complaint or "",
                'precautions': record.history_of_present_illness or "",
                'date': record.visit_date.isoformat()
            })

        return Response({
            'code': 0,
            'data': {
                'list': result,
                'total': total,
                'page': page,
                'page_size': page_size
            }
        })

    @action(detail=True, methods=['get'])
    def record_detail(self, request, pk=None):
        try:
            record = ClinicRecord.objects.get(record_id=pk)
            serializer = ClinicRecordSerializer(record)
            data = serializer.data
            
            data['patient'] = {
                'patient_id': record.patient.patient_id,
                'name': record.patient.name,
                'gender': record.patient.gender,
                'age': record.patient.age
            }
            
            if record.doctor:
                data['doctor'] = {
                    'doctor_id': record.doctor.doctor_id,
                    'name': record.doctor.name
                }
            
            return Response({'code': 0, 'data': data})
        except ClinicRecord.DoesNotExist:
            return Response({'code': 404, 'msg': 'Record not found'}, status=status.HTTP_404_NOT_FOUND)


class CollectionViewSet(viewsets.ModelViewSet):
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Collection.objects.filter(user=self.request.user)

    def create(self, request):
        try:
            collection = Collection.objects.get(
                user=request.user,
                collection_type=request.data.get('collection_type'),
                target_id=request.data.get('target_id')
            )
            return Response({'code': 400, 'msg': 'Already collected'}, status=status.HTTP_400_BAD_REQUEST)
        except Collection.DoesNotExist:
            pass

        serializer = CollectionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({'code': 0, 'data': serializer.data}, status=status.HTTP_201_CREATED)
        return Response({'code': 400, 'msg': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        try:
            patient = Patient.objects.get(user=user)
            return Notification.objects.filter(patient=patient).order_by('-created_at')
        except Patient.DoesNotExist:
            return Notification.objects.none()

    @action(detail=False, methods=['get'])
    def list_notifications(self, request):
        try:
            patient = Patient.objects.get(user=request.user)
            notifications = Notification.objects.filter(patient=patient).order_by('-created_at')
            
            result = []
            for n in notifications:
                result.append({
                    'type': n.type,
                    'title': n.title,
                    'order_id': n.order_id,
                    'time': n.created_at.isoformat()
                })
            
            return Response({'code': 0, 'data': result})
        except Patient.DoesNotExist:
            return Response({'code': 404, 'msg': 'Patient not found'}, status=status.HTTP_404_NOT_FOUND)


class AdminViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAdminUser]

    @action(detail=False, methods=['get'])
    def users(self, request):
        users = User.objects.all()
        result = []
        
        for user in users:
            role = 'admin'
            extra_info = {}
            
            try:
                patient = Patient.objects.get(user=user)
                role = 'patient'
                extra_info = {
                    'patient_id': patient.patient_id,
                    'name': patient.name
                }
            except Patient.DoesNotExist:
                try:
                    doctor = Doctor.objects.get(user=user)
                    role = 'doctor'
                    extra_info = {
                        'doctor_id': doctor.doctor_id,
                        'name': doctor.name,
                        'department': doctor.department.name if doctor.department else ''
                    }
                except Doctor.DoesNotExist:
                    pass
            
            result.append({
                'id': user.id,
                'username': user.username,
                'role': role,
                **extra_info
            })
        
        return Response({'code': 0, 'data': result})