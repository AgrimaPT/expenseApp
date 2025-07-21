from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .forms import SignupForm, LoginForm,ShopForm,StaffSignupForm,CategoryForm,ExpenseForm
from django.contrib.auth.decorators import login_required
from .models import CustomUser, Shop,Category,SalaryExpense

def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = SignupForm()
    return render(request, 'signup.html', {'form': form})

def staff_signup_view(request):
    if request.method == 'POST':
        form = StaffSignupForm(request.POST)
        if form.is_valid():
            shop_code = form.cleaned_data.get('shop_code')
            try:
                shop = Shop.objects.get(shop_code=shop_code)
            except Shop.DoesNotExist:
                form.add_error('shop_code', 'Invalid shop code')
                return render(request, 'staff_signup.html', {'form': form})
            
            staff = form.save(commit=False)
            staff.role = 'staff'
            staff.shop = shop
            staff.save()
            return redirect('login')
    else:
        form = StaffSignupForm()
    return render(request, 'staff_signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def create_shop(request):
    if request.user.role != 'admin':
        return redirect('dashboard')  # staff not allowed to create shop

    if request.method == 'POST':
        form = ShopForm(request.POST)
        if form.is_valid():
            shop = form.save()
            request.user.shop = shop  # assign shop to admin
            request.user.save()
            return redirect('dashboard')
    else:
        form = ShopForm()
    return render(request, 'create_shop.html', {'form': form})

@login_required
def dashboard_view(request):
    if request.user.role == 'admin':
        if not request.user.shop:
            return redirect('create_shop')  # force shop creation
        return render(request, 'dashboard_admin.html')
    else:
        return render(request, 'dashboard_staff.html')
    

@login_required
def manage_staff_view(request):
    if request.user.role != 'admin':
        return redirect('dashboard')  # Only admins can view staff

    staff_members = CustomUser.objects.filter(role='staff', shop=request.user.shop)
    return render(request, 'manage_staff.html', {'staff_members': staff_members})


@login_required
def category_list_view(request):
    categories = Category.objects.filter(shop=request.user.shop)
    return render(request, 'category_list.html', {'categories': categories})

@login_required
def add_category_view(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.shop = request.user.shop
            category.save()
            return redirect('category_list')
    else:
        form = CategoryForm()
    return render(request, 'add_category.html', {'form': form})

@login_required
def edit_category_view(request, category_id):
    category = get_object_or_404(Category, id=category_id, shop=request.user.shop)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'add_category.html', {'form': form, 'edit': True})

from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Category,Expense

@login_required
def delete_category_view(request, category_id):
    category = get_object_or_404(Category, id=category_id, shop=request.user.shop)
    if request.method == 'POST':
        category.delete()
    return redirect('category_list')

from django.utils import timezone
import json
from .models import Category, Expense, ExpenseItem
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

@login_required
def add_expense(request):
    if request.method == 'POST':
        print("POST received:", request.POST)

        items_json = request.POST.get('items_json')
        if not items_json:
            return render(request, 'add_expense.html', {
                'error': 'No expense items added',
                'categories': Category.objects.filter(shop=request.user.shop),
                'today_date': timezone.now().date().strftime('%Y-%m-%d'),
            })

        items_data = json.loads(items_json)

        # Create the expense
        expense = Expense.objects.create(
            shop=request.user.shop,
            added_by=request.user,
            date=request.POST.get('date') or timezone.now().date()
        )
        print("Expense created:", expense)

        # Save each item
        for item in items_data:
            print("Processing item:", item)
            category_id = item.get('catId')
            quantity = item.get('qty')
            price = item.get('price')

            if not (category_id and quantity and price):
                continue  # Skip incomplete

            category = Category.objects.get(id=category_id)
            ExpenseItem.objects.create(
                expense=expense,
                category=category,
                quantity=quantity,
                price=price
            )

        return redirect('expense_list')

    categories = Category.objects.filter(shop=request.user.shop)
    today_date = timezone.now().date().strftime('%Y-%m-%d')
    return render(request, 'add_expense.html', {
        'categories': categories,
        'today_date': today_date,
    })




from django.utils import timezone
from .models import CustomUser, SalaryExpense

from django.db.models import Q
from django.utils import timezone
from .models import SalaryExpense
from django.urls import reverse
@login_required
def mark_daily_salary(request):
    shop = request.user.shop
    staff_members = CustomUser.objects.filter(role='staff', shop=shop)

    # Get selected date from GET or POST or default to today
    date_str = request.GET.get('date') or request.POST.get('date')
    try:
        selected_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        selected_date = timezone.now().date()

    existing_salaries_qs = SalaryExpense.objects.filter(
        employee__in=staff_members,
        date=selected_date
    )
    existing_salaries = {s.employee_id: s for s in existing_salaries_qs}

    if request.method == 'POST':
        # ✅ Create one Expense object to group all the salary items
        expense = Expense.objects.create(
            shop=shop,
            date=selected_date
        )

        for staff in staff_members:
            salary_key = f'salary_{staff.id}'
            salary_value = request.POST.get(salary_key)
            if salary_value:
                salary_value = float(salary_value)

                if staff.id in existing_salaries:
                    existing = existing_salaries[staff.id]
                    existing.amount = salary_value
                    existing.expense = expense  # ✅ update expense link if needed
                    existing.save()
                else:
                    SalaryExpense.objects.create(
                        expense=expense,  # ✅ link to Expense
                        employee=staff,
                        amount=salary_value,
                        date=selected_date,
                        
                    )

        return redirect('expense_list')

    return render(request, 'mark_salary.html', {
        'staff_members': staff_members,
        'selected_date': selected_date,
        'existing_salaries': existing_salaries,
    })


from django.utils import timezone
from .models import Expense, SalaryExpense

# @login_required
# def expense_list(request):
#     selected_date_str = request.GET.get('date')
#     today = timezone.now().date()
#     selected_date = today if not selected_date_str else timezone.datetime.strptime(selected_date_str, '%Y-%m-%d').date()

#     shop = request.user.shop

#     # Expenses (with related items and categories)
#     expenses = Expense.objects.filter(shop=shop, date=selected_date).prefetch_related('items', 'items__category')

#     # Salaries (filter based on the same date)
#     salary_entries = SalaryExpense.objects.filter(expense__shop=shop,employee__shop=shop, date=selected_date).select_related('employee')

#     # Totals
#     items_total = sum(item.amount for expense in expenses for item in expense.items.all())
#     salary_total = sum(s.amount for s in salary_entries)
#     total_expense = items_total + salary_total

#     return render(request, 'expense_list.html', {
#         'expenses': expenses,
#         'salary_entries': salary_entries,
#         'selected_date': selected_date,
#         'items_total': items_total,
#         'salary_total': salary_total,
#         'total_expense': total_expense
#     })


from .models import Expense, ExpenseItem, SalaryExpense, OnlinePayment  # Make sure OnlinePayment is imported

@login_required
def expense_list(request):
    selected_date_str = request.GET.get('date')
    today = timezone.now().date()
    selected_date = today if not selected_date_str else timezone.datetime.strptime(selected_date_str, '%Y-%m-%d').date()

    shop = request.user.shop

    # Expenses (with related items and categories)
    expenses = Expense.objects.filter(shop=shop, date=selected_date).prefetch_related('items', 'items__category')
    item_expenses_count = sum(expense.items.count() for expense in expenses)

    # Salaries (filter based on the same date)
    salary_entries = SalaryExpense.objects.filter(expense__shop=shop, employee__shop=shop, date=selected_date).select_related('employee')

    # Online Payments
    online_payments = OnlinePayment.objects.filter(expense__shop=shop, expense__date=selected_date)

    # Totals
    items_total = sum(item.amount for expense in expenses for item in expense.items.all())
    salary_total = sum(s.amount for s in salary_entries)
    online_total = sum(op.amount for op in online_payments)
    total_expense = items_total + salary_total + online_total

    return render(request, 'expense_list.html', {
        'expenses': expenses,
        'salary_entries': salary_entries,
        'online_payments': online_payments,
        'selected_date': selected_date,
        'items_total': items_total,
        'salary_total': salary_total,
        'online_total': online_total,
        'total_expense': total_expense,
        'item_expenses_count': item_expenses_count,
    })


from .models import OnlinePayment,DailySaleSummary
from django.core.files.storage import FileSystemStorage

@login_required
def add_online_payment(request):
    if request.method == 'POST':
        items_json = request.POST.get('items_json')
        if not items_json:
            return render(request, 'add_online_payment.html', {
                'error': 'No payment items added',
                'categories': Category.objects.filter(shop=request.user.shop),
                'today_date': timezone.now().date().strftime('%Y-%m-%d'),
            })

        items_data = json.loads(items_json)

        expense = Expense.objects.create(
            shop=request.user.shop,
            added_by=request.user,
            date=request.POST.get('date') or timezone.now().date()
        )

        for index, item in enumerate(items_data):
            category = Category.objects.get(id=item['catId'])
            OnlinePayment.objects.create(
                expense=expense,
                category=category,
                quantity=item['qty'],
                price=item['price'],
                bill_number=item.get('billNumber'),
                bill_image=request.FILES.get(f'billImage_{index}')
            )

        return redirect('expense_list')

    categories = Category.objects.filter(shop=request.user.shop)
    today_date = timezone.now().date().strftime('%Y-%m-%d')
    return render(request, 'add_online_payment.html', {
        'categories': categories,
        'today_date': today_date,
    })



from django.db.models import Sum, F
from decimal import Decimal


# @login_required
# def daily_sale_summary(request):
#     shop = request.user.shop
#     date_str = request.GET.get('date') or request.POST.get('date')
#     selected_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else timezone.now().date()

#     if request.method == 'POST':
#         remaining_cash = Decimal(request.POST.get('remaining_cash', 0))
#         cash_in_account = Decimal(request.POST.get('cash_in_account', 0))

#         # Get all expenses
#         expense_total = ExpenseItem.objects.filter(
#             expense__shop=shop, expense__date=selected_date
#         ).aggregate(total=Sum(F('quantity') * F('price')))['total'] or 0

#         salary_total = SalaryExpense.objects.filter(
#             expense__shop=shop, date=selected_date
#         ).aggregate(total=Sum('amount'))['total'] or 0

#         online_total = OnlinePayment.objects.filter(
#             expense__shop=shop, expense__date=selected_date
#         ).aggregate(total=Sum(F('quantity') * F('price')))['total'] or 0

#         total_expense = expense_total + salary_total
#         total_sale = remaining_cash + cash_in_account + total_expense
#         daily_benefit = total_sale - total_expense - online_total

#         # Get previous cumulative benefit
#         first_of_month = selected_date.replace(day=1)
#         previous_summaries = DailySaleSummary.objects.filter(
#             shop=shop, date__gte=first_of_month, date__lt=selected_date
#         ).order_by('date')

#         last_cumulative = previous_summaries.last().cumulative_monthly_benefit if previous_summaries.exists() else 0
#         cumulative_monthly_benefit = last_cumulative + daily_benefit

#         # Save to model
#         DailySaleSummary.objects.update_or_create(
#             shop=shop, date=selected_date,
#             defaults={
#                 'remaining_cash': remaining_cash,
#                 'cash_in_account': cash_in_account,
#                 'total_sale': total_sale,
#                 'daily_benefit': daily_benefit,
#                 'cumulative_monthly_benefit': cumulative_monthly_benefit
#             }
#         )

#         return redirect('daily_sale_summary')

#     return render(request, 'sale_summary_form.html', {
#         'selected_date': selected_date
#     })

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from decimal import Decimal
from django.db.models import Sum
from .models import ExpenseItem, SalaryExpense, OnlinePayment

# @login_required
# def daily_sale_summary(request):
#     shop = request.user.shop
#     context = {'calculated': False}

#     if request.method == 'POST':
#         # Get form values
#         date_str = request.POST.get('date')
#         cash_in_box = request.POST.get('cash_in_box')
#         cash_in_account = request.POST.get('cash_in_account')

#         # Parse values
#         try:
#             selected_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
#         except:
#             selected_date = timezone.now().date()

#         try:
#             cash_in_box = Decimal(cash_in_box)
#         except:
#             cash_in_box = Decimal('0.00')

#         try:
#             cash_in_account = Decimal(cash_in_account)
#         except:
#             cash_in_account = Decimal('0.00')

#         # ExpenseItem total
#         expense_items_total = ExpenseItem.objects.filter(
#             expense__shop=shop,
#             expense__date=selected_date
#         ).aggregate(total=Sum('quantity') * Sum('price'))['total'] or Decimal('0.00')

#         if expense_items_total == 0:
#             expense_items_total = ExpenseItem.objects.filter(
#                 expense__shop=shop,
#                 expense__date=selected_date
#             ).annotate(amount=F('quantity') * F('price')).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

#         # SalaryExpense total
#         salary_total = SalaryExpense.objects.filter(
#             expense__shop=shop,
#             date=selected_date
#         ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

#         # OnlinePayment total
#         online_payment_total = OnlinePayment.objects.filter(
#             expense__shop=shop,
#             expense__date=selected_date
#         ).annotate(amount=F('quantity') * F('price')).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

#         # Total expense (cash) = ExpenseItem + Salary
#         total_expense = expense_items_total + salary_total

#         # Total sale = cash in box + cash in account + total_expense
#         total_sale = cash_in_box + cash_in_account + total_expense

#         # Daily benefit = total_sale - total_expense - online_payment
#         daily_benefit = total_sale - total_expense - online_payment_total

#         # Monthly benefit = sum of daily benefit till date (including today)
#         from django.db.models.functions import TruncDate
#         from .models import Expense  # if needed

#         start_of_month = selected_date.replace(day=1)
#         salary_month_total = SalaryExpense.objects.filter(
#             expense__shop=shop,
#             date__range=(start_of_month, selected_date)
#         ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

#         expense_item_month_total = ExpenseItem.objects.filter(
#             expense__shop=shop,
#             expense__date__range=(start_of_month, selected_date)
#         ).annotate(amount=F('quantity') * F('price')).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

#         online_month_total = OnlinePayment.objects.filter(
#             expense__shop=shop,
#             expense__date__range=(start_of_month, selected_date)
#         ).annotate(amount=F('quantity') * F('price')).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

#         cash_in_box_total = cash_in_box  # You may want to store per-day cash later
#         cash_in_account_total = cash_in_account

#         monthly_total_expense = expense_item_month_total + salary_month_total
#         monthly_benefit = (cash_in_box_total + cash_in_account_total + monthly_total_expense) - monthly_total_expense - online_month_total

#         # Pass values to template
#         context.update({
#             'calculated': True,
#             'selected_date': selected_date,
#             'expense_items_total': expense_items_total,
#             'salary_total': salary_total,
#             'total_expense': total_expense,
#             'online_payment_total': online_payment_total,
#             'total_sale': total_sale,
#             'daily_benefit': daily_benefit,
#             'monthly_benefit': monthly_benefit,
#         })

#     return render(request, 'sale_summary_form.html', context)
from datetime import timedelta


@login_required
def daily_sale_summary(request):
    shop = request.user.shop
    context = {'calculated': False}

    if request.method == 'POST':
        # Get input values
        date_str = request.POST.get('date')
        cash_in_box = request.POST.get('cash_in_box')
        cash_in_account = request.POST.get('cash_in_account')

        # Convert and validate inputs
        try:
            selected_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            selected_date = timezone.now().date()

        try:
            cash_in_box = Decimal(cash_in_box)
        except:
            cash_in_box = Decimal('0.00')

        try:
            cash_in_account = Decimal(cash_in_account)
        except:
            cash_in_account = Decimal('0.00')

        # Expense items (quantity * price)
        expense_items_total = ExpenseItem.objects.filter(
            expense__shop=shop,
            expense__date=selected_date
        ).annotate(amount=F('quantity') * F('price')).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        # Salaries
        salary_total = SalaryExpense.objects.filter(
            employee__shop=shop,
            date=selected_date
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        # Online Payments
        online_payment_total = OnlinePayment.objects.filter(
            expense__shop=shop,
            expense__date=selected_date
        ).annotate(amount=F('quantity') * F('price')).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        # Total expense in cash (ExpenseItem + Salary)
        total_expense = expense_items_total + salary_total

        # Total sale
        total_sale = cash_in_box + cash_in_account + total_expense

        # Daily benefit
        daily_benefit = total_sale - total_expense - online_payment_total

        # Cumulative monthly benefit till date
        start_of_month = selected_date.replace(day=1)

        # Monthly expenses
        month_expense_items = ExpenseItem.objects.filter(
            expense__shop=shop,
            expense__date__range=(start_of_month, selected_date)
        ).annotate(amount=F('quantity') * F('price')).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        month_salary = SalaryExpense.objects.filter(
            employee__shop=shop,
            date__range=(start_of_month, selected_date)
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        month_online_payments = OnlinePayment.objects.filter(
            expense__shop=shop,
            expense__date__range=(start_of_month, selected_date)
        ).annotate(amount=F('quantity') * F('price')).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        # month_cash = cash_in_box
        # month_account = cash_in_account

        # monthly_expense_total = month_expense_items + month_salary
        # cumulative_monthly_benefit = (month_cash + month_account + monthly_expense_total) - monthly_expense_total - month_online_payments
        

        previous_daily_benefits = DailySaleSummary.objects.filter(
            shop=shop,
            date__range=(start_of_month, selected_date - timedelta(days=1))  # exclude current day
        ).aggregate(total=Sum('daily_benefit'))['total'] or Decimal('0.00')
        
        # Current day's benefit will be added to the cumulative total
        cumulative_monthly_benefit = previous_daily_benefits + daily_benefit


        # ✅ Save or update the summary
        DailySaleSummary.objects.update_or_create(
            shop=shop,
            date=selected_date,
            defaults={
                'remaining_cash': cash_in_box,
                'cash_in_account': cash_in_account,
                'total_sale': total_sale,
                'daily_benefit': daily_benefit,
                'cumulative_monthly_benefit': cumulative_monthly_benefit,
            }
        )

        # Display data in template
        context.update({
            'calculated': True,
            'selected_date': selected_date,
            'cash_in_box': cash_in_box,
            'cash_in_account': cash_in_account,
            'expense_items_total': expense_items_total,
            'salary_total': salary_total,
            'total_expense': total_expense,
            'online_payment_total': online_payment_total,
            'total_sale': total_sale,
            'daily_benefit': daily_benefit,
            'monthly_benefit': cumulative_monthly_benefit,
        })


    return render(request, 'sale_summary_form.html', context)




# @login_required
# def view_daily_summary(request):
#     shop = request.user.shop
#     selected_date = None
#     summary = None
#     message = None

#     if request.method == 'POST':
#         date_str = request.POST.get('date')
#         try:
#             selected_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
#         except:
#             selected_date = timezone.now().date()

#         try:
#             summary = DailySaleSummary.objects.get(shop=shop, date=selected_date)
            
#             # ONLY recalculate for current/future dates
#             if selected_date >= timezone.now().date():
#                 start_of_month = selected_date.replace(day=1)
#                 previous_daily_benefits = DailySaleSummary.objects.filter(
#                     shop=shop,
#                     date__range=(start_of_month, selected_date - timedelta(days=1))
#                 ).aggregate(total=Sum('daily_benefit'))['total'] or Decimal('0.00')
                
#                 # Update only if this is current/future date
#                 summary.cumulative_monthly_benefit = previous_daily_benefits + summary.daily_benefit
#                 summary.save()
            
#         except DailySaleSummary.DoesNotExist:
#             message = "No summary data found for the selected date."

#     return render(request, 'view_sale_summary.html', {
#         'selected_date': selected_date,
#         'summary': summary,
#         'message': message
#     })

from datetime import timedelta

@login_required
def view_daily_summary(request):
    shop = request.user.shop
    selected_date = None
    summary = None
    message = None

    if request.method == 'POST':
        date_str = request.POST.get('date')
        try:
            selected_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            selected_date = timezone.now().date()

    if not selected_date:
        selected_date = timezone.now().date()

    try:
        summary = DailySaleSummary.objects.get(shop=shop, date=selected_date)
    except DailySaleSummary.DoesNotExist:
        message = "No summary data found for the selected date."

    # Get last 7 days of data for the chart
    date_range = [selected_date - timedelta(days=i) for i in range(6, -1, -1)]
    last_7_days = []
    for day in date_range:
        try:
            day_summary = DailySaleSummary.objects.get(shop=shop, date=day)
            last_7_days.append({
                'date': day,
                'daily_benefit': float(day_summary.daily_benefit)
            })
        except DailySaleSummary.DoesNotExist:
            last_7_days.append({
                'date': day,
                'daily_benefit': 0
            })

    return render(request, 'view_sale_summary.html', {
        'selected_date': selected_date,
        'summary': summary,
        'message': message,
        'last_7_days': last_7_days
    })

# from decimal import Decimal
# from django.db.models import F, Sum
# from django.utils import timezone
# from django.contrib.auth.decorators import login_required
# from django.shortcuts import render
# from .models import ExpenseItem, SalaryExpense, OnlinePayment, DailySaleSummary


# @login_required
# def daily_sale_summary(request):
#     shop = request.user.shop
#     context = {'calculated': False}

#     if request.method == 'POST':
#         # Get input values
#         date_str = request.POST.get('date')
#         remaining_cash_in_shop = request.POST.get('remaining_cash_in_shop')
#         cash_credited_today = request.POST.get('cash_credited_today')

#         # Parse date
#         try:
#             selected_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
#         except:
#             selected_date = timezone.now().date()

#         # Safe decimal conversion
#         try:
#             remaining_cash_in_shop = Decimal(remaining_cash_in_shop)
#         except:
#             remaining_cash_in_shop = Decimal('0.00')

#         try:
#             cash_credited_today = Decimal(cash_credited_today)
#         except:
#             cash_credited_today = Decimal('0.00')

#         # Cash-based expenses
#         expense_items_total = ExpenseItem.objects.filter(
#             expense__shop=shop,
#             expense__date=selected_date
#         ).annotate(amount=F('quantity') * F('price')).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

#         salary_total = SalaryExpense.objects.filter(
#             employee__shop=shop,
#             date=selected_date
#         ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

#         total_cash_expense = expense_items_total + salary_total

#         # Online expenses
#         online_payment_total = OnlinePayment.objects.filter(
#             expense__shop=shop,
#             expense__date=selected_date
#         ).annotate(amount=F('quantity') * F('price')).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

#         # Total sale (Cash box + Cash credited + Cash spent)
#         total_sale = remaining_cash_in_shop + cash_credited_today + total_cash_expense

#         # Daily benefit
#         daily_benefit = total_sale - total_cash_expense - online_payment_total

#         # Monthly benefit till date (from saved DailySaleSummary)
#         start_of_month = selected_date.replace(day=1)
#         cumulative_monthly_benefit = DailySaleSummary.objects.filter(
#             shop=shop,
#             date__range=(start_of_month, selected_date)
#         ).exclude(date=selected_date).aggregate(total=Sum('daily_benefit'))['total'] or Decimal('0.00')

#         cumulative_monthly_benefit += daily_benefit

#         # Save or update summary
#         DailySaleSummary.objects.update_or_create(
#             shop=shop,
#             date=selected_date,
#             defaults={
#                 'remaining_cash': remaining_cash_in_shop,
#                 'cash_in_account': cash_credited_today,
#                 'total_sale': total_sale,
#                 'daily_benefit': daily_benefit,
#                 'cumulative_monthly_benefit': cumulative_monthly_benefit,
#             }
#         )

#         context.update({
#             'calculated': True,
#             'selected_date': selected_date,
#             'remaining_cash_in_shop': remaining_cash_in_shop,
#             'cash_credited_today': cash_credited_today,
#             'expense_items_total': expense_items_total,
#             'salary_total': salary_total,
#             'total_cash_expense': total_cash_expense,
#             'online_payment_total': online_payment_total,
#             'total_sale': total_sale,
#             'daily_benefit': daily_benefit,
#             'monthly_benefit': cumulative_monthly_benefit,
#         })

#     return render(request, 'sale_summary_form.html', context)


# @login_required
# def view_daily_summary(request):
#     shop = request.user.shop
#     selected_date = None
#     summary = None
#     message = None

#     if request.method == 'POST':
#         date_str = request.POST.get('date')
#         try:
#             selected_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
#         except:
#             selected_date = timezone.now().date()

#         try:
#             summary = DailySaleSummary.objects.get(shop=shop, date=selected_date)
#         except DailySaleSummary.DoesNotExist:
#             message = "No summary data found for the selected date."

#     return render(request, 'view_sale_summary.html', {
#         'selected_date': selected_date,
#         'summary': summary,
#         'message': message,
#     })
