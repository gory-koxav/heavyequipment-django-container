from django.db import models

class StatRecord(models.Model):
    date = models.DateField()
    average = models.FloatField()
    std_dev = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Stats for {self.date}: Avg={self.average}, Std={self.std_dev}"