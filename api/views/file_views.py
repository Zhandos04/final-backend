# api/views/file_views.py
from rest_framework import views, parsers, permissions, status
from rest_framework.response import Response
from django.conf import settings
import os
import uuid
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.core.files.storage import default_storage


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

    # Необходимые настройки S3
    REQUIRED_S3_SETTINGS = [
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY',
        'AWS_STORAGE_BUCKET_NAME',
        'AWS_S3_REGION_NAME'
    ]

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
            upload_path = f"uploads/{filename}"

            # Проверяем, включен ли S3
            use_s3 = getattr(settings, 'USE_S3', False)

            storage_info = {
                'storage_type': 'S3' if use_s3 else 'local',
                'use_s3': use_s3
            }

            # Проверяем настройки S3 если нужно
            if use_s3:
                missing_settings = [s for s in self.REQUIRED_S3_SETTINGS if not getattr(settings, s, None)]

                if missing_settings:
                    storage_info.update({
                        'missing_settings': missing_settings,
                        'warning': 'Отсутствуют необходимые настройки для S3, используем локальное хранилище',
                        'storage_type': 'local'
                    })
                    use_s3 = False

            # Выполняем загрузку с помощью соответствующего хранилища
            if use_s3:
                try:
                    from storages.backends.s3boto3 import S3Boto3Storage
                    storage = S3Boto3Storage()
                    path = storage.save(upload_path, file_obj)
                    file_url = storage.url(path)

                    storage_info.update({
                        'message': 'Файл успешно загружен в AWS S3',
                        'bucket': settings.AWS_STORAGE_BUCKET_NAME,
                        'region': settings.AWS_S3_REGION_NAME
                    })
                except Exception as e:
                    storage_info.update({
                        's3_error': str(e),
                        'warning': 'Ошибка при использовании S3, используем локальное хранилище',
                        'storage_type': 'local'
                    })
                    use_s3 = False

            # Используем локальное хранилище если не S3
            if not use_s3:
                path = default_storage.save(upload_path, file_obj)
                file_url = request.build_absolute_uri(settings.MEDIA_URL + path)
                storage_info['message'] = 'Файл успешно загружен в локальное хранилище'

            # Формируем и возвращаем ответ
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