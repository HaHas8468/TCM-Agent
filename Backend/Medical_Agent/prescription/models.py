from django.db import models


class Formula(models.Model):
    name = models.CharField(max_length=200, unique=True)
    pinyin = models.CharField(max_length=200, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    effect = models.TextField(null=True, blank=True)
    source = models.CharField(max_length=200, null=True, blank=True)
    decoction_method = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


class FormulaHerb(models.Model):
    formula = models.ForeignKey(Formula, on_delete=models.CASCADE)
    herb_name = models.CharField(max_length=100)
    dosage = models.CharField(max_length=50, null=True, blank=True)
    role = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"{self.formula.name} - {self.herb_name}"


class FormulaIndication(models.Model):
    formula = models.ForeignKey(Formula, on_delete=models.CASCADE)
    zheng_type = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.formula.name} - {self.zheng_type}"


class Modification(models.Model):
    formula = models.ForeignKey(Formula, on_delete=models.CASCADE)
    condition = models.TextField()
    modification = models.TextField()

    def __str__(self):
        return f"{self.formula.name} - {self.condition[:30]}"


class Pharmacology(models.Model):
    formula = models.ForeignKey(Formula, on_delete=models.CASCADE)
    content = models.TextField()
    source = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return f"{self.formula.name} - 药理研究"
