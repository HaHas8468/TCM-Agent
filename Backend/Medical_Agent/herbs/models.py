from django.db import models


class Herb(models.Model):
    name = models.CharField(max_length=100, unique=True)
    pinyin = models.CharField(max_length=100, null=True, blank=True)
    property = models.CharField(max_length=50, null=True, blank=True)
    flavor = models.CharField(max_length=100, null=True, blank=True)
    effect = models.TextField(null=True, blank=True)
    dosage = models.CharField(max_length=50, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


class Meridian(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class HerbMeridian(models.Model):
    herb = models.ForeignKey(Herb, on_delete=models.CASCADE)
    meridian = models.ForeignKey(Meridian, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('herb', 'meridian')

    def __str__(self):
        return f"{self.herb.name} - {self.meridian.name}"


class Contraindication(models.Model):
    herb = models.ForeignKey(Herb, on_delete=models.CASCADE)
    content = models.TextField()

    def __str__(self):
        return f"{self.herb.name} - 禁忌"


class Compatibility(models.Model):
    herb = models.ForeignKey(Herb, on_delete=models.CASCADE, related_name='compatibility_source')
    target_herb = models.ForeignKey(Herb, on_delete=models.CASCADE, related_name='compatibility_target')
    relationship = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.herb.name} {self.relationship} {self.target_herb.name}"


class ModernResearch(models.Model):
    herb = models.ForeignKey(Herb, on_delete=models.CASCADE)
    content = models.TextField()
    source = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return f"{self.herb.name} - 现代研究"
