#!/bin/sh

if [ "$SQL_ENGINE" = "django.db.backends.postgresql" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

# Установка всех зависимостей
pip install -r requirements.txt

# Создание миграций для всех приложений
python manage.py makemigrations expenses
python manage.py makemigrations users

# Применение миграций
python manage.py migrate

# Создание профилей и предустановленных категорий
python manage.py shell -c "
from django.contrib.auth.models import User
from users.models import Profile
from expenses.models import Category

# Создание профилей для пользователей
for user in User.objects.all():
    try:
        profile = user.profile
        print(f'Profile already exists for {user.username}')
    except Profile.DoesNotExist:
        Profile.objects.create(user=user)
        print(f'Created profile for {user.username}')

# Default expense categories
default_expense_categories = [
    'Groceries', 'Restaurants & Cafes', 'Transport', 'Housing', 'Utilities', 
    'Internet & Communications', 'Entertainment', 'Clothing & Footwear', 'Health & Medicine', 'Education', 
    'Travel', 'Gifts', 'Household Items', 'Electronics', 'Sports', 
    'Beauty & Self-care', 'Hobbies', 'Pets', 'Taxi', 'Books'
]

# Default income categories
default_income_categories = [
    'Salary', 'Freelance', 'Business', 'Investments', 'Gifts',
    'Interest', 'Rental Income', 'Dividends', 'Bonuses', 'Other Income'
]

# Создаем категории для всех пользователей
for user in User.objects.all():
    # Проверяем, есть ли у пользователя уже категории
    existing_categories = Category.objects.filter(user=user).count()
    
    if existing_categories == 0:
        # Создаем категории расходов и доходов
        for category_name in default_expense_categories:
            Category.objects.create(name=category_name, user=user)
            print(f'Created expense category {category_name} for {user.username}')
            
        for category_name in default_income_categories:
            Category.objects.create(name=category_name, user=user)
            print(f'Created income category {category_name} for {user.username}')
"

# Сбор статических файлов
python manage.py collectstatic --no-input

exec "$@"