from rest_framework import views, permissions, status
from rest_framework.response import Response
from django.conf import settings
import os
import tempfile
from api.tasks import process_csv_import, generate_csv_export
from api.throttling import UserRateThrottle
from celery.result import AsyncResult

class ImportCSVView(views.APIView):

    """
    API для импорта транзакций из CSV файла
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    
    def post(self, request):
        file_obj = request.FILES.get('file')
        
        if not file_obj:
            return Response({'error': 'Файл не предоставлен'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Проверяем расширение файла

        if not file_obj.name.endswith('.csv'):
            return Response({'error': 'Файл должен быть в формате CSV'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Создаем временный файл

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
        
        try:
            # Сохраняем загруженный файл во временный файл

            for chunk in file_obj.chunks():
                temp_file.write(chunk)
            temp_file.close()
            
            # Запускаем задачу Celery для обработки файла

            task = process_csv_import.delay(request.user.id, temp_file.name)
            
            return Response({
                'message': 'Файл успешно загружен и обрабатывается',
                'task_id': task.id
            })
            

        except Exception as e:
            # В случае ошибки удаляем временный файл
            os.unlink(temp_file.name)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ExportCSVView(views.APIView):

    """
    API для экспорта транзакций в CSV файл
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    
    def get(self, request):
        year = request.query_params.get('year')
        month = request.query_params.get('month')
        
        # Запускаем задачу Celery для генерации CSV

        task = generate_csv_export.delay(request.user.id, year, month)
        
        return Response({
            'message': 'Экспорт в CSV запущен',
            'task_id': task.id
        })

class TaskStatusView(views.APIView):
    
    """
    API для проверки статуса задачи Celery
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, task_id):
        task_result = AsyncResult(task_id)
        
        response_data = {
            'task_id': task_id,
            'status': task_result.status,
        }
        
        if task_result.successful():
            response_data['result'] = task_result.get()
        elif task_result.failed():
            response_data['error'] = str(task_result.result)
        
        return Response(response_data)