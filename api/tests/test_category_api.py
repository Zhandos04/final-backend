from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from expenses.models import Category

class CategoryAPITests(APITestCase):
    def setUp(self):
        # Создаем тестового пользователя
        self.user = User.objects.create_user(
            username='testuser', 
            email='test@example.com', 
            password='testpassword123'
        )
        
        # Авторизуемся
        self.client.force_authenticate(user=self.user)
        
        # Создаем тестовую категорию
        self.category = Category.objects.create(
            name='Test Category',
            user=self.user
        )
        
        # URL-ы для тестирования
        self.list_url = reverse('category-list')
        self.detail_url = reverse('category-detail', args=[self.category.id])
    
    def test_list_categories(self):
        """Тест: получение списка категорий"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Проверяем, что есть ответ, без проверки конкретной структуры
        # Просто убеждаемся, что запрос успешен
        self.assertTrue(response.data is not None)
    
    def test_create_category(self):
        """Тест: создание новой категории"""
        # Запомним начальное количество категорий
        initial_count = Category.objects.count()
        
        data = {
            'name': 'New Category'
        }
        
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Проверяем, что количество категорий увеличилось на 1
        self.assertEqual(Category.objects.count(), initial_count + 1)
        
        # Проверяем данные новой категории
        new_category = Category.objects.get(name='New Category')
        self.assertEqual(new_category.user, self.user)
    
    def test_get_category_detail(self):
        """Тест: получение детальной информации о категории"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Category')
    
    def test_update_category(self):
        """Тест: обновление существующей категории"""
        data = {
            'name': 'Updated Category'
        }
        
        response = self.client.put(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Перезагружаем объект из БД
        self.category.refresh_from_db()
        
        # Проверяем, что данные обновились
        self.assertEqual(self.category.name, 'Updated Category')
    
    def test_delete_category(self):
        """Тест: удаление категории"""
        # Запомним начальное количество категорий
        initial_count = Category.objects.count()
        
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Проверяем, что количество категорий уменьшилось на 1
        self.assertEqual(Category.objects.count(), initial_count - 1)
    
    def test_unauthorized_access(self):
        """Тест: доступ без авторизации должен быть запрещен"""
        # Выходим из системы
        self.client.force_authenticate(user=None)
        
        # Пытаемся получить список категорий
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
