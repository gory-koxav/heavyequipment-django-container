from rest_framework import serializers
from .models import StatRecord

class StatRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatRecord
        fields = ['id', 'date', 'average', 'std_dev', 'created_at']