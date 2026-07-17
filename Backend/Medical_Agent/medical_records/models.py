from django.db import models


class MedicalRecord(models.Model):
    title = models.CharField(max_length=200)
    disease_name = models.CharField(max_length=100)
    zheng_type = models.CharField(max_length=100)
    formula_name = models.CharField(max_length=100)
    content = models.TextField()
    author = models.CharField(max_length=100, null=True, blank=True)
    source = models.CharField(max_length=200, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class RecordHerb(models.Model):
    record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE)
    herb_name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.record.title} - {self.herb_name}"


class RecordFormula(models.Model):
    record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE)
    formula_name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.record.title} - {self.formula_name}"


class Disease(models.Model):
    name = models.CharField(max_length=100, unique=True)
    pinyin = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name
