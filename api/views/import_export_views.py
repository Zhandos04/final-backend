from rest_framework import views, permissions, status
from rest_framework.response import Response
from django.conf import settings
import os
import tempfile
from api.tasks import process_csv_import, generate_csv_export
from api.throttling import UserRateThrottle
from celery.result import AsyncResult
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt


class CSVBaseView(views.APIView):
    """Базовый класс для работы с CSV файлами"""
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def handle_error(self, error, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR):
        """Обработка ошибок"""
        return Response({'error': str(error)}, status=status_code)


@method_decorator(csrf_exempt, name='dispatch')
class ImportCSVView(CSVBaseView):
    """
    API для импорта транзакций из CSV файла
    """

    def post(self, request):
        file_obj = request.FILES.get('file')
        temp_file = None

        try:
            if not file_obj:
                return self.handle_error('Файл не предоставлен', status.HTTP_400_BAD_REQUEST)

            # Проверяем расширение файла
            if not file_obj.name.lower().endswith('.csv'):
                return self.handle_error('Файл должен быть в формате CSV', status.HTTP_400_BAD_REQUEST)

            # Создаем временный файл с автоматической очисткой
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')

            # Сохраняем загруженный файл во временный файл
            for chunk in file_obj.chunks():
                temp_file.write(chunk)
            temp_file.close()

            # Запускаем задачу Celery для обработки файла
            task = process_csv_import.delay(request.user.id, temp_file.name)

            return Response({
                'message': 'Файл успешно загружен и обрабатывается',
                'task_id': task.id,
                'filename': file_obj.name,
                'file_size': file_obj.size
            })

        except Exception as e:
            # В случае ошибки удаляем временный файл
            if temp_file and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
            return self.handle_error(e)


class ExportCSVView(CSVBaseView):
    """
    API для экспорта транзакций в CSV файл
    """

    def get(self, request):
        try:
            # Получаем и валидируем параметры
            year = request.query_params.get('year')
            month = request.query_params.get('month')

            # Запускаем задачу Celery для генерации CSV
            task = generate_csv_export.delay(request.user.id, year, month)

            # Подготавливаем описательный ответ
            period_description = ""
            if year and month:
                period_description = f"за {month}/{year}"
            elif year:
                period_description = f"за {year} год"
            else:
                period_description = "за весь период"

            return Response({
                'message': f'Экспорт транзакций {period_description} в CSV запущен',
                'task_id': task.id,
                'params': {
                    'year': year,
                    'month': month
                }
            })

        except Exception as e:
            return self.handle_error(e)


class TaskStatusView(CSVBaseView):
    """
    API для проверки статуса задачи Celery
    """

    def get(self, request, task_id):
        try:
            if not task_id:
                return self.handle_error('Идентификатор задачи не указан', status.HTTP_400_BAD_REQUEST)

            task_result = AsyncResult(task_id)

            response_data = {
                'task_id': task_id,
                'status': task_result.status,
                'timestamp': timezone.now().isoformat()
            }

            if task_result.successful():
                response_data['result'] = task_result.get()
                response_data['finished_at'] = task_result.date_done.isoformat() if task_result.date_done else None
            elif task_result.failed():
                response_data['error'] = str(task_result.result)
                response_data['finished_at'] = task_result.date_done.isoformat() if task_result.date_done else None
            elif task_result.status == 'PENDING':
                response_data['message'] = 'Задача находится в очереди на выполнение'
            elif task_result.status == 'STARTED':
                response_data['message'] = 'Задача выполняется'

            return Response(response_data)

        except Exception as e:
            return self.handle_error(e)