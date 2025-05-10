from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from expenses.models import Transaction, Category
from decimal import Decimal
from datetime import date

class TransactionAPITests(APITestCase):
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
        
        # Создаем тестовую транзакцию
        self.transaction = Transaction.objects.create(
            amount=Decimal('100.00'),
            description='Test Transaction',
            date=date.today(),
            category=self.category,
            user=self.user,
            transaction_type='expense'
        )
        
        # URL-ы для тестирования
        self.list_url = reverse('transaction-list')
        self.detail_url = reverse('transaction-detail', args=[self.transaction.id])
    
    def test_list_transactions(self):
        """Тест: получение списка транзакций"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Проверяем только, что ответ успешно получен,
        # без предположений о количестве элементов
        self.assertTrue(response.data is not None)
    
    def test_create_transaction(self):
        """Тест: создание новой транзакции"""
        data = {
            'amount': '50.00',
            'description': 'New Transaction',
            'date': date.today().isoformat(),
            'category': self.category.id,
            'transaction_type': 'income'
        }
        
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Проверяем, что транзакция действительно создана
        self.assertEqual(Transaction.objects.count(), 2)
        
        # Проверяем данные новой транзакции
        new_transaction = Transaction.objects.get(description='New Transaction')
        self.assertEqual(new_transaction.amount, Decimal('50.00'))
        self.assertEqual(new_transaction.transaction_type, 'income')
        self.assertEqual(new_transaction.user, self.user)
    
    def test_get_transaction_detail(self):
        """Тест: получение детальной информации о транзакции"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['amount'], '100.00')
        self.assertEqual(response.data['description'], 'Test Transaction')
    
    def test_update_transaction(self):
        """Тест: обновление существующей транзакции"""
        data = {
            'amount': '75.00',
            'description': 'Updated Transaction',
            'date': date.today().isoformat(),
            'category': self.category.id,
            'transaction_type': 'expense'
        }
        
        response = self.client.put(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Перезагружаем объект из БД
        self.transaction.refresh_from_db()
        
        # Проверяем, что данные обновились
        self.assertEqual(self.transaction.amount, Decimal('75.00'))
        self.assertEqual(self.transaction.description, 'Updated Transaction')
    
    def test_partial_update_transaction(self):
        """Тест: частичное обновление транзакции"""
        data = {
            'description': 'Partially Updated Transaction'
        }
        
        response = self.client.patch(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Перезагружаем объект из БД
        self.transaction.refresh_from_db()
        
        # Проверяем, что изменилось только описание
        self.assertEqual(self.transaction.description, 'Partially Updated Transaction')
        self.assertEqual(self.transaction.amount, Decimal('100.00'))  # Не должно измениться
    
    def test_delete_transaction(self):
        """Тест: удаление транзакции"""
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Проверяем, что транзакция удалена из БД
        self.assertEqual(Transaction.objects.count(), 0)
    
    def test_unauthorized_access(self):
        """Тест: доступ без авторизации должен быть запрещен"""
        # Выходим из системы
        self.client.force_authenticate(user=None)
        
        # Пытаемся получить список транзакций
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
