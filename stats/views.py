from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, timedelta
import statistics
from influxdb_client import InfluxDBClient
from django.conf import settings
from .models import StatRecord
from .serializers import StatRecordSerializer

class ProcessDataView(APIView):
    """
    요청받은 날짜(YYYY-MM-DD)를 기준으로 InfluxDB에서 rawdata를 조회하고,
    평균과 표준편차를 계산하여 PostgreSQL에 저장한 후 결과를 반환합니다.
    """
    def get(self, request, format=None):
        date_str = request.query_params.get('date')
        if not date_str:
            return Response({"error": "Missing 'date' parameter"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
        
        # 해당 날짜의 00:00:00 ~ 23:59:59 범위 설정
        start_time = datetime.combine(target_date, datetime.min.time())
        end_time = start_time + timedelta(days=1)
        
        influx_conf = settings.INFLUXDB
        
        try:
            with InfluxDBClient(url=influx_conf['URL'], token=influx_conf['TOKEN'], org=influx_conf['ORG']) as client:
                query_api = client.query_api()
                # Flux 쿼리 (measurement, field 이름은 실제 사용 환경에 맞게 수정)
                flux_query = f'''
                from(bucket:"{influx_conf['BUCKET']}")
                  |> range(start: {start_time.isoformat()}Z, stop: {end_time.isoformat()}Z)
                  |> filter(fn: (r) => r["_measurement"] == "rawdata")
                  |> filter(fn: (r) => r["_field"] == "value")
                '''
                result = query_api.query(org=influx_conf['ORG'], query=flux_query)
                values = []
                for table in result:
                    for record in table.records:
                        if record.get_value() is not None:
                            values.append(record.get_value())
                
                if not values:
                    return Response({"error": "No data found for the specified date."}, status=status.HTTP_404_NOT_FOUND)
                
                avg = statistics.mean(values)
                std = statistics.stdev(values) if len(values) > 1 else 0.0
                
                # ORM을 사용해 PostgreSQL에 저장
                stat_record = StatRecord.objects.create(date=target_date, average=avg, std_dev=std)
                serializer = StatRecordSerializer(stat_record)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)