from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.db.models.functions import TruncMonth
import datetime
import calendar
from .models import Transaction, Category
from .forms import TransactionForm, CategoryForm

@login_required
def dashboard(request):
    current_month = datetime.datetime.now().month
    current_year = datetime.datetime.now().year
    
    # Get current month transactions
    transactions = Transaction.objects.filter(
        user=request.user,
        date__month=current_month,
        date__year=current_year
    ).order_by('-date')
    
    # Total amounts
    income = Transaction.objects.filter(
        user=request.user, 
        transaction_type='income',
        date__month=current_month,
        date__year=current_year
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    expenses = Transaction.objects.filter(
        user=request.user, 
        transaction_type='expense',
        date__month=current_month,
        date__year=current_year
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    balance = income - expenses
    
    # Chart data
    expense_categories = Category.objects.filter(user=request.user)
    category_data = []
    
    # Get expense amounts by category
    for category in expense_categories:
        category_sum = Transaction.objects.filter(
            user=request.user,
            category=category,
            transaction_type='expense',
            date__month=current_month,
            date__year=current_year
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        if category_sum > 0:
            category_data.append({
                'name': category.name,
                'amount': float(category_sum)  # Convert to float for JSON
            })
    
    # Debug print
    print(f"Category data: {category_data}")
    
    context = {
        'transactions': transactions,
        'income': income,
        'expenses': expenses,
        'balance': balance,
        'category_data': category_data,
        'month_name': calendar.month_name[current_month]
    }
    
    return render(request, 'expenses/dashboard.html', context)

@login_required
def add_transaction(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            messages.success(request, 'Transaction added successfully!')
            return redirect('dashboard')
    else:
        form = TransactionForm()
        form.fields['category'].queryset = Category.objects.filter(user=request.user)
    
    return render(request, 'expenses/transaction_form.html', {'form': form})

@login_required
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.save()
            messages.success(request, 'Category added successfully!')
            return redirect('dashboard')
    else:
        form = CategoryForm()
    
    return render(request, 'expenses/category_form.html', {'form': form})

@login_required
def reports(request):
    # Data for the last 6 months
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=180)
    
    # Gather data by month
    monthly_data = Transaction.objects.filter(
        user=request.user,
        date__range=[start_date, end_date]
    ).annotate(
        month=TruncMonth('date')
    ).values('month', 'transaction_type').annotate(
        total=Sum('amount')
    ).order_by('month')
    
    # Format for charts
    months = []
    incomes = []
    expenses = []
    savings = []
    
    for data in monthly_data:
        month_str = data['month'].strftime('%b %Y')
        
        if month_str not in months:
            months.append(month_str)
            incomes.append(0)
            expenses.append(0)
            savings.append(0)
        
        month_index = months.index(month_str)
        
        if data['transaction_type'] == 'income':
            incomes[month_index] = float(data['total'])
        else:
            expenses[month_index] = float(data['total'])
    
    # Calculate savings
    for i in range(len(months)):
        savings[i] = incomes[i] - expenses[i]
    
    # Pass months as JSON list
    context = {
        'months': months,
        'incomes': incomes,
        'expenses': expenses,
        'savings': savings
    }
    
    return render(request, 'expenses/reports.html', context)

@login_required
def delete_transaction(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    
    if request.method == 'POST':
        transaction.delete()
        messages.success(request, f'Transaction deleted successfully!')
        return redirect('dashboard')
    
    return render(request, 'expenses/delete_transaction.html', {'transaction': transaction})

@login_required
def edit_transaction(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            form.save()
            messages.success(request, f'Transaction updated successfully!')
            return redirect('dashboard')
    else:
        form = TransactionForm(instance=transaction)
        form.fields['category'].queryset = Category.objects.filter(user=request.user)
    
    return render(request, 'expenses/transaction_form.html', {'form': form})