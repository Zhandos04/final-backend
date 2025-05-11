# api/views/file_views.py
from rest_framework import views, parsers, permissions, status
from rest_framework.response import Response
from django.conf import settings
import os
import uuid
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class FileUploadView(views.APIView):

    """
    API для загрузки файлов в AWS S3 или локальное хранилище.
    Через этот эндпоинт можно проверить, работает ли AWS S3.
    
    Если USE_S3=True и все настройки AWS корректны,
    файл будет загружен в S3 и URL будет содержать домен S3.
    
    Если USE_S3=False или настройки некорректны,
    файл будет загружен в локальное хранилище.
    """
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Загрузка файла в AWS S3 или локальное хранилище",
        manual_parameters=[
            openapi.Parameter(
                name='file',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=True,
                description='Файл для загрузки'
            ),
        ],
        responses={
            200: openapi.Response(
                description="Успешная загрузка файла",
                examples={
                    'application/json': {
                        'status': 'success',
                        'file_url': 'https://example.com/path/to/file.jpg',
                        'filename': 'uuid-filename.jpg',
                        'original_filename': 'uploaded.jpg',
                        'file_size': 12345,
                        'content_type': 'image/jpeg',
                        'storage_info': {'storage_type': 'S3', 'use_s3': True}
                    }
                }
            ),
            400: "Файл не предоставлен",
            500: "Ошибка при загрузке файла"
        }
    )
    def post(self, request):
        try:
            file_obj = request.FILES.get('file')
            
            if not file_obj:
                return Response({
                    'status': 'error',
                    'message': 'Файл не предоставлен'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Генерируем уникальное имя файла
            filename = f"{uuid.uuid4()}{os.path.splitext(file_obj.name)[1]}"
            
            # Проверяем, включен ли S3
            use_s3 = getattr(settings, 'USE_S3', False)
            
            storage_info = {
                'storage_type': 'S3' if use_s3 else 'local',
                'use_s3': use_s3
            }
            
            if use_s3:
                # Проверяем наличие всех необходимых настроек
                required_settings = [
                    'AWS_ACCESS_KEY_ID', 
                    'AWS_SECRET_ACCESS_KEY', 
                    'AWS_STORAGE_BUCKET_NAME', 
                    'AWS_S3_REGION_NAME'
                ]
                
                missing_settings = [s for s in required_settings if not getattr(settings, s, None)]
                
                if missing_settings:
                    storage_info['missing_settings'] = missing_settings
                    storage_info['warning'] = 'Отсутствуют необходимые настройки для S3, используем локальное хранилище'
                    use_s3 = False
            
            if use_s3:
                try:

                    # Используем S3
                    from storages.backends.s3boto3 import S3Boto3Storage
                    storage = S3Boto3Storage()
                    path = storage.save(f"uploads/{filename}", file_obj)
                    file_url = storage.url(path)
                    
                    storage_info['message'] = 'Файл успешно загружен в AWS S3'
                    storage_info['bucket'] = settings.AWS_STORAGE_BUCKET_NAME
                    storage_info['region'] = settings.AWS_S3_REGION_NAME
                    
                except Exception as e:

                    # Если произошла ошибка при использовании S3, 
                    # переходим на локальное хранилище
                    storage_info['s3_error'] = str(e)
                    storage_info['warning'] = 'Ошибка при использовании S3, используем локальное хранилище'
                    use_s3 = False
            
            # Если S3 отключен или возникла ошибка, используем локальное хранилище

            if not use_s3:
                from django.core.files.storage import default_storage
                
                path = default_storage.save(f"uploads/{filename}", file_obj)
                file_url = request.build_absolute_uri(settings.MEDIA_URL + path)
                
                storage_info['message'] = 'Файл успешно загружен в локальное хранилище'
            
            # Общий ответ
            
            return Response({
                'status': 'success',
                'file_url': file_url,
                'filename': filename,
                'original_filename': file_obj.name,
                'file_size': file_obj.size,
                'content_type': file_obj.content_type,
                'storage_info': storage_info
            })
                
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Ошибка при загрузке файла: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)