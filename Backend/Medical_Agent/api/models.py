from django.db import models
from django.contrib.auth.models import User


class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    patient_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    name = models.CharField(max_length=100)
    gender = models.CharField(max_length=10, choices=[('男', '男'), ('女', '女')])
    birth_date = models.DateField(null=True, blank=True)
    age = models.IntegerField()
    phone = models.CharField(max_length=20, null=True, blank=True)
    address = models.CharField(max_length=200, null=True, blank=True)
    id_card = models.CharField(max_length=20, null=True, blank=True, unique=True)
    blood_type = models.CharField(max_length=10, null=True, blank=True)
    health_info = models.TextField(null=True, blank=True)
    allergy_history = models.JSONField(null=True, blank=True)
    emergency_contact = models.CharField(max_length=100, null=True, blank=True)
    emergency_phone = models.CharField(max_length=20, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Department(models.Model):
    department_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    parent_department = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    doctor_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    name = models.CharField(max_length=100)
    title = models.CharField(max_length=50, null=True, blank=True)
    hospital = models.CharField(max_length=100, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    license_number = models.CharField(max_length=50, null=True, blank=True)
    specialty = models.CharField(max_length=100, null=True, blank=True)
    experience = models.IntegerField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    duty_time = models.CharField(max_length=100, null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Schedule(models.Model):
    schedule_id = models.CharField(max_length=50, unique=True)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    morning_afternoon = models.CharField(max_length=10, choices=[('上午', '上午'), ('下午', '下午'), ('晚上', '晚上')])
    total_slots = models.IntegerField(default=30)
    available_slots = models.IntegerField(default=30)
    status = models.CharField(max_length=20, choices=[('available', '可预约'), ('full', '已满'), ('canceled', '已取消')], default='available')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.doctor.name} - {self.date} {self.morning_afternoon}"


class Order(models.Model):
    order_id = models.CharField(max_length=50, unique=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    department_name = models.CharField(max_length=100, null=True, blank=True)
    schedule = models.ForeignKey(Schedule, on_delete=models.SET_NULL, null=True, blank=True)
    order_type = models.CharField(max_length=20, choices=[('online', '线上挂号'), ('offline', '线下挂号')], default='online')
    source = models.CharField(max_length=20, choices=[('smart', '智能挂号推荐'), ('direct', '直接挂号')], default='direct')
    status = models.CharField(max_length=20, choices=[('pending', '待接诊'), ('ongoing', '问诊中'), ('finished', '已结束'), ('cancelled', '已取消')], default='pending')
    visit_time = models.DateTimeField(null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    time = models.CharField(max_length=20, null=True, blank=True)
    waiting_number = models.IntegerField(null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    payment_time = models.DateTimeField(null=True, blank=True)
    qr_code = models.CharField(max_length=200, null=True, blank=True)
    scanned = models.BooleanField(default=False)
    chief_complaint = models.TextField(null=True, blank=True)
    present_illness = models.TextField(null=True, blank=True)
    tongue = models.CharField(max_length=200, null=True, blank=True)
    pulse = models.CharField(max_length=200, null=True, blank=True)
    symptoms = models.JSONField(null=True, blank=True)
    signs = models.CharField(max_length=200, null=True, blank=True)
    other = models.TextField(null=True, blank=True)
    syndrome = models.CharField(max_length=200, null=True, blank=True)
    prescription = models.CharField(max_length=200, null=True, blank=True)
    ingredients = models.JSONField(null=True, blank=True)
    advice = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.order_id


class Chat(models.Model):
    session_id = models.CharField(max_length=100, unique=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True)
    messages = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[('active', '进行中'), ('ended', '已结束')], default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Session {self.session_id}"


class ChatMessage(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='chat_messages')
    sender_type = models.CharField(max_length=20, choices=[('patient', '患者'), ('doctor', '医生'), ('system', '系统')])
    sender_id = models.IntegerField(null=True, blank=True)
    content = models.TextField()
    message_type = models.CharField(max_length=20, choices=[('text', '文本'), ('image', '图片'), ('voice', '语音')], default='text')
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender_type}: {self.content[:50]}"


class ClinicRecord(models.Model):
    record_id = models.CharField(max_length=50, unique=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True)
    visit_date = models.DateTimeField(auto_now_add=True)
    chief_complaint = models.TextField()
    history_of_present_illness = models.TextField(null=True, blank=True)
    past_history = models.TextField(null=True, blank=True)
    physical_examination = models.TextField(null=True, blank=True)
    tongue = models.CharField(max_length=200, null=True, blank=True)
    pulse = models.CharField(max_length=200, null=True, blank=True)
    other_signs = models.TextField(null=True, blank=True)
    zheng_type = models.CharField(max_length=100, null=True, blank=True)
    zheng_description = models.TextField(null=True, blank=True)
    diagnosis = models.TextField(null=True, blank=True)
    treatment_principle = models.TextField(null=True, blank=True)
    treatment_plan = models.TextField(null=True, blank=True)
    prescription = models.CharField(max_length=200, null=True, blank=True)
    herbs = models.JSONField(null=True, blank=True)
    ingredients = models.JSONField(null=True, blank=True)
    dosage = models.TextField(null=True, blank=True)
    decoction_method = models.TextField(null=True, blank=True)
    advice = models.TextField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    follow_up = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Record {self.record_id}"


class Collection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    collection_type = models.CharField(max_length=20, choices=[('herb', '中药'), ('formula', '方剂'), ('record', '医案'), ('doctor', '医生')])
    target_id = models.CharField(max_length=100)
    target_name = models.CharField(max_length=200)
    extra_info = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'collection_type', 'target_id']

    def __str__(self):
        return f"{self.user.username} - {self.collection_type}: {self.target_name}"


class DiagnosisSession(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True)
    symptoms = models.TextField()
    tongue = models.CharField(max_length=200, null=True, blank=True)
    pulse = models.CharField(max_length=200, null=True, blank=True)
    other_signs = models.TextField(null=True, blank=True)
    zheng_type = models.CharField(max_length=100, null=True, blank=True)
    zheng_description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Session {self.id} - {self.patient.name}"


class Prescription(models.Model):
    diagnosis_session = models.ForeignKey(DiagnosisSession, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True)
    main_formula = models.CharField(max_length=200)
    formula_description = models.TextField(null=True, blank=True)
    herbs = models.TextField()
    dosage = models.TextField()
    decoction_method = models.TextField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Prescription {self.id} - {self.main_formula}"


class Notification(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    type = models.CharField(max_length=50)
    title = models.CharField(max_length=200)
    order_id = models.CharField(max_length=50, null=True, blank=True)
    content = models.TextField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type}: {self.title}"