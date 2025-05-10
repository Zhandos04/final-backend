# api/urls.py (обновленный с маршрутом для загрузки файлов)
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from api.views.transaction_views import TransactionViewSet
from api.views.category_views import CategoryViewSet
from api.views.user_views import UserProfileView, RegisterView, LogoutView
from api.views.report_views import ReportViewSet
from api.views.budget_views import BudgetViewSet
from api.views.goal_views import GoalViewSet
from api.views.import_export_views import ImportCSVView, ExportCSVView, TaskStatusView
from api.views.file_views import FileUploadView

router = DefaultRouter()
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'reports', ReportViewSet, basename='report')
router.register(r'budgets', BudgetViewSet, basename='budget')
router.register(r'goals', GoalViewSet, basename='goal')

urlpatterns = [
    path('', include(router.urls)),
    
    # Аутентификация и пользователи
    path('users/profile/', UserProfileView.as_view(), name='user-profile'),
    path('users/register/', RegisterView.as_view(), name='register'),
    path('users/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('users/refresh-token/', TokenRefreshView.as_view(), name='token_refresh'),
    path('users/logout/', LogoutView.as_view(), name='logout'),
    
    # Импорт/Экспорт
    path('import/csv/', ImportCSVView.as_view(), name='import-csv'),
    path('export/csv/', ExportCSVView.as_view(), name='export-csv'),
    path('task-status/<str:task_id>/', TaskStatusView.as_view(), name='task-status'),
    
    # Загрузка файлов (для проверки AWS S3)
    path('upload/', FileUploadView.as_view(), name='file-upload'),
    
    # API документация через DRF
    path('auth/', include('rest_framework.urls')),
]