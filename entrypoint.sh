#!/bin/sh

if [ "$SQL_ENGINE" = "django.db.backends.postgresql" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

# Использовать PORT из переменных окружения Railway или 8000 по умолчанию
PORT="${PORT:-8000}"

# Установка всех зависимостей
pip install -r requirements.txt

# Определяем, какой это контейнер по имени команды
COMMAND="$@"

# Миграции запускаем только в web-контейнере или если это явно указано
if [[ "$COMMAND" == *"runserver"* ]] || [[ "$CONTAINER_ROLE" == "web" ]] || [[ "$PERFORM_MIGRATIONS" == "1" ]]; then
    echo "Выполнение миграций..."
    python manage.py makemigrations
    python manage.py migrate
    
    # Создание профилей и предустановленных категорий - обратите внимание, что отступы удалены!
    python manage.py shell -c "from django.contrib.auth.models import User
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

# Проверка, есть ли категории у пользователей
for user in User.objects.all():
    if Category.objects.filter(user=user).count() == 0:
        # Дефолтные категории расходов
        default_expense_categories = [
            'Groceries', 'Restaurants & Cafes', 'Transport', 'Housing', 'Utilities', 
            'Internet & Communications', 'Entertainment', 'Clothing & Footwear', 'Health & Medicine', 'Education', 
            'Travel', 'Gifts', 'Household Items', 'Electronics', 'Sports', 
            'Beauty & Self-care', 'Hobbies', 'Pets', 'Taxi', 'Books'
        ]
        
        # Дефолтные категории доходов
        default_income_categories = [
            'Salary', 'Freelance', 'Business', 'Investments', 'Gifts',
            'Interest', 'Rental Income', 'Dividends', 'Bonuses', 'Other Income'
        ]
        
        # Создаем категории расходов
        for category_name in default_expense_categories:
            Category.objects.create(name=category_name, user=user)
            print(f'Created expense category {category_name} for {user.username}')
            
        # Создаем категории доходов
        for category_name in default_income_categories:
            Category.objects.create(name=category_name, user=user)
            print(f'Created income category {category_name} for {user.username}')"
    
    # Сбор статических файлов
    python manage.py collectstatic --no-input
else
    echo "Пропускаем выполнение миграций в этом контейнере..."
fi

# Проверяем, был ли передан стандартный аргумент
if [ -z "$COMMAND" ] || [ "$COMMAND" = "gunicorn budget_app.wsgi:application --bind 0.0.0.0:8000" ]; then
    # Запускаем с использованием PORT из Railway
    exec gunicorn budget_app.wsgi:application --bind 0.0.0.0:$PORT
else
    # Если был передан другой аргумент, используем его
    exec "$@"
fi