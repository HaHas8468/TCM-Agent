from django.db import models


class Symptom(models.Model):
    name = models.CharField(max_length=50, unique=True)
    category = models.CharField(max_length=50, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


class TongueSign(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


class PulseSign(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


class ZhengType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    main_symptoms = models.TextField(null=True, blank=True)
    typical_tongue = models.TextField(null=True, blank=True)
    typical_pulse = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


class DiagnosisQuestion(models.Model):
    question = models.CharField(max_length=500)
    question_type = models.CharField(max_length=50, choices=[
        ('symptom', '症状'),
        ('tongue', '舌象'),
        ('pulse', '脉象'),
        ('other', '其他')
    ])
    zheng_type = models.ForeignKey(ZhengType, on_delete=models.SET_NULL, null=True, blank=True)
    order = models.IntegerField(default=0)

    def __str__(self):
        return self.question
