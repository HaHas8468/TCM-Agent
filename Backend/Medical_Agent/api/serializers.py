from rest_framework import serializers
from .models import Patient, Doctor, Department, Schedule, Order, Chat, ChatMessage, ClinicRecord, Collection, DiagnosisSession, Prescription, Notification


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['id', 'patient_id', 'name', 'gender', 'birth_date', 'age', 'phone', 'address', 'id_card', 
                  'blood_type', 'health_info', 'allergy_history', 'emergency_contact', 'emergency_phone',
                  'created_at', 'updated_at']


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'department_id', 'name', 'description', 'parent_department', 'created_at']


class DoctorSerializer(serializers.ModelSerializer):
    department = DepartmentSerializer(read_only=True)
    department_id = serializers.PrimaryKeyRelatedField(queryset=Department.objects.all(), source='department', write_only=True)

    class Meta:
        model = Doctor
        fields = ['id', 'doctor_id', 'name', 'title', 'hospital', 'department', 'department_id',
                  'license_number', 'specialty', 'experience', 'phone', 'duty_time', 'bio',
                  'description', 'created_at', 'updated_at']


class ScheduleSerializer(serializers.ModelSerializer):
    doctor = DoctorSerializer(read_only=True)
    department = DepartmentSerializer(read_only=True)
    doctor_id = serializers.PrimaryKeyRelatedField(queryset=Doctor.objects.all(), source='doctor', write_only=True)
    department_id = serializers.PrimaryKeyRelatedField(queryset=Department.objects.all(), source='department', write_only=True)

    class Meta:
        model = Schedule
        fields = ['id', 'schedule_id', 'doctor', 'department', 'doctor_id', 'department_id',
                  'date', 'start_time', 'end_time', 'morning_afternoon', 'total_slots', 
                  'available_slots', 'status', 'created_at']


class OrderSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    doctor = DoctorSerializer(read_only=True)
    department = DepartmentSerializer(read_only=True)
    patient_id = serializers.PrimaryKeyRelatedField(queryset=Patient.objects.all(), source='patient', write_only=True)
    doctor_id = serializers.PrimaryKeyRelatedField(queryset=Doctor.objects.all(), source='doctor', write_only=True, required=False)
    department_id = serializers.PrimaryKeyRelatedField(queryset=Department.objects.all(), source='department', write_only=True, required=False)
    schedule_id = serializers.PrimaryKeyRelatedField(queryset=Schedule.objects.all(), source='schedule', write_only=True, required=False)

    class Meta:
        model = Order
        fields = ['id', 'order_id', 'patient', 'doctor', 'department', 'schedule',
                  'patient_id', 'doctor_id', 'department_id', 'schedule_id',
                  'department_name', 'order_type', 'source', 'status', 'visit_time',
                  'date', 'time', 'waiting_number', 'amount', 'payment_time',
                  'qr_code', 'scanned', 'chief_complaint', 'present_illness',
                  'tongue', 'pulse', 'symptoms', 'signs', 'other', 'syndrome',
                  'prescription', 'ingredients', 'advice',
                  'created_at', 'updated_at']


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'sender_type', 'sender_id', 'content', 'message_type', 'timestamp', 'is_read']


class ChatSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    doctor = DoctorSerializer(read_only=True)
    messages = ChatMessageSerializer(source='chat_messages', many=True, read_only=True)
    patient_id = serializers.PrimaryKeyRelatedField(queryset=Patient.objects.all(), source='patient', write_only=True)
    doctor_id = serializers.PrimaryKeyRelatedField(queryset=Doctor.objects.all(), source='doctor', write_only=True, required=False)
    order_id = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all(), source='order', write_only=True, required=False)

    class Meta:
        model = Chat
        fields = ['id', 'session_id', 'patient', 'doctor', 'order', 'messages',
                  'patient_id', 'doctor_id', 'order_id', 'status', 'created_at', 'updated_at']


class ClinicRecordSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    doctor = DoctorSerializer(read_only=True)
    patient_id = serializers.PrimaryKeyRelatedField(queryset=Patient.objects.all(), source='patient', write_only=True)
    doctor_id = serializers.PrimaryKeyRelatedField(queryset=Doctor.objects.all(), source='doctor', write_only=True, required=False)
    order_id = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all(), source='order', write_only=True, required=False)

    class Meta:
        model = ClinicRecord
        fields = ['id', 'record_id', 'patient', 'doctor', 'order',
                  'patient_id', 'doctor_id', 'order_id',
                  'visit_date', 'chief_complaint', 'history_of_present_illness', 'past_history',
                  'physical_examination', 'tongue', 'pulse', 'other_signs',
                  'zheng_type', 'zheng_description', 'diagnosis', 'treatment_principle',
                  'treatment_plan', 'prescription', 'herbs', 'ingredients',
                  'dosage', 'decoction_method', 'advice', 'notes', 'follow_up',
                  'created_at', 'updated_at']


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = ['id', 'user', 'collection_type', 'target_id', 'target_name', 'extra_info', 'created_at']


class DiagnosisSessionSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    doctor = DoctorSerializer(read_only=True)
    patient_id = serializers.PrimaryKeyRelatedField(queryset=Patient.objects.all(), source='patient', write_only=True)
    doctor_id = serializers.PrimaryKeyRelatedField(queryset=Doctor.objects.all(), source='doctor', write_only=True, required=False)

    class Meta:
        model = DiagnosisSession
        fields = ['id', 'patient', 'doctor', 'patient_id', 'doctor_id',
                  'symptoms', 'tongue', 'pulse', 'other_signs',
                  'zheng_type', 'zheng_description', 'created_at', 'updated_at']


class PrescriptionSerializer(serializers.ModelSerializer):
    doctor = DoctorSerializer(read_only=True)
    doctor_id = serializers.PrimaryKeyRelatedField(queryset=Doctor.objects.all(), source='doctor', write_only=True, required=False)

    class Meta:
        model = Prescription
        fields = ['id', 'diagnosis_session', 'doctor', 'doctor_id',
                  'main_formula', 'formula_description', 'herbs', 'dosage',
                  'decoction_method', 'notes', 'created_at']


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'patient', 'type', 'title', 'order_id', 'content', 'is_read', 'created_at']