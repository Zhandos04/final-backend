from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from users.models import Profile

class UserProfileAPITests(APITestCase):
    def setUp(self):
        # Создаем тестового пользователя
        self.user = User.objects.create_user(
            username='testuser', 
            email='test@example.com', 
            password='testpassword123'
        )
        
        # Обновляем профиль пользователя
        self.user.profile.currency = '₽'
        self.user.profile.save()
        
        # Авторизуемся
        self.client.force_authenticate(user=self.user)
        
        # URL для тестирования
        self.profile_url = reverse('user-profile')
        self.register_url = reverse('register')
    
    def test_get_profile(self):
        """Тест: получение профиля пользователя"""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['profile']['currency'], '₽')
    
    def test_update_profile(self):
        """Тест: обновление профиля пользователя"""
        data = {
            'username': 'updateduser',
            'email': 'updated@example.com',
            'profile': {
                'currency': '$'
            }
        }
        
        response = self.client.put(self.profile_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Перезагружаем объект из БД
        self.user.refresh_from_db()
        self.user.profile.refresh_from_db()
        
        # Проверяем, что данные обновились
        self.assertEqual(self.user.username, 'updateduser')
        self.assertEqual(self.user.email, 'updated@example.com')
        self.assertEqual(self.user.profile.currency, '$')
    
    def test_register_user(self):
        """Тест: регистрация нового пользователя"""
        # Выходим из системы
        self.client.force_authenticate(user=None)
        
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpassword123',
            'password2': 'newpassword123',
            'first_name': 'John',
            'last_name': 'Doe'
        }
        
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Проверяем, что пользователь создан в БД
        self.assertTrue(User.objects.filter(username='newuser').exists())
        
        # Проверяем, что профиль также создан
        new_user = User.objects.get(username='newuser')
        self.assertTrue(hasattr(new_user, 'profile'))
        
        # Проверяем данные нового пользователя
        self.assertEqual(new_user.email, 'new@example.com')
        self.assertEqual(new_user.first_name, 'John')
        self.assertEqual(new_user.last_name, 'Doe')
    
    def test_register_user_password_mismatch(self):
        """Тест: регистрация с несовпадающими паролями должна возвращать ошибку"""
        # Выходим из системы
        self.client.force_authenticate(user=None)
        
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpassword123',
            'password2': 'differentpassword',
            'first_name': 'John',
            'last_name': 'Doe'
        }
        
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Проверяем, что пользователь не создан в БД
        self.assertFalse(User.objects.filter(username='newuser').exists())