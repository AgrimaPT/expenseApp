from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .forms import DistributorForm,SignupForm, LoginForm,ShopForm,StaffSignupForm,SupervisorSignupForm,ExpenseForm,EmployeeForm,ShopAccessRequestForm
from django.contrib.auth.decorators import login_required
from .models import CustomUser, Shop,SalaryExpense,Employee,Distributor,SupervisorShopAccess
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Expense
from django.utils import timezone
import json
from .models import  Expense, ExpenseItem,SalaryExpense,OnlinePayment,DailySaleSummary
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.files.storage import FileSystemStorage
from django.db.models import Sum, F
from decimal import Decimal
from django.shortcuts import render
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.db.models import Q
from django.urls import reverse
from django.contrib import messages


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
            staff.is_active = False  # Ensure this is set
            staff.approval_status = 'pending'
            staff.shop = shop
            staff.save()
            return redirect('login')
    else:
        form = StaffSignupForm()
    return render(request, 'staff_signup.html', {'form': form})

# views.py
def supervisor_signup_view(request):
    if request.method == 'POST':
        form = SupervisorSignupForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)  # Log the user in immediately after signup
                messages.success(
                    request,
                    "Account created successfully! Please request access to shops."
                )
                return redirect('request_shop_access')  # Redirect to shop access page
            except Exception as e:
                messages.error(request, f"Error creating account: {str(e)}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = SupervisorSignupForm()

    return render(request, 'supervisor_signup.html', {
        'form': form,
        'title': 'Supervisor Registration'
    })

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            
            # Additional checks for staff/supervisor
            # if user.role in ['staff', 'supervisor']:
            if user.role == 'staff':
                if user.approval_status != 'approved':
                    messages.error(request, 
                        f"Account pending approval. Status: {user.approval_status}. "
                        f"Please contact admin.")
                    return redirect('login')
                if not user.is_active:
                    messages.error(request, 
                        f"Account not active. is_active: {user.is_active}. "
                        f"Please contact admin.")
                    return redirect('login')
                    
            login(request, user)
            if user.role == 'supervisor':
                if not SupervisorShopAccess.objects.filter(
                    supervisor=user,
                    is_approved=True
                ).exists():
                    return redirect('request_shop_access')
            
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
        return redirect('dashboard')

    if request.method == 'POST':
        form = ShopForm(request.POST)
        if form.is_valid():
            shop = form.save(commit=False)
            shop.admin = request.user  # Assign the current admin as the shop admin
            shop.save()
            return redirect('shop_list')
    else:
        form = ShopForm()
    return render(request, 'create_shop.html', {'form': form})

@login_required
def edit_shop(request, shop_id):
    if request.user.role != 'admin':
        return redirect('dashboard')
    
    shop = get_object_or_404(Shop, id=shop_id, admin=request.user)
    if request.method == 'POST':
        form = ShopForm(request.POST, instance=shop)
        if form.is_valid():
            form.save()
            return redirect('shop_list')
    else:
        form = ShopForm(instance=shop)
    return render(request, 'edit_shop.html', {'form': form, 'shop': shop})
@login_required
def shop_list(request):
    if request.user.role != 'admin':
        return redirect('dashboard')
    
    shops = Shop.objects.filter(admin=request.user)
    return render(request, 'shop_list.html', {'shops': shops})

# @login_required
# def dashboard_view(request):
#     if request.user.role == 'admin':
#         shops = Shop.objects.filter(admin=request.user)
        
#         # Get shop_id from URL, session, or default to first shop
#         shop_id = request.GET.get('shop_id') or request.session.get('active_shop_id')
        
#         if shop_id:
#             try:
#                 shop = Shop.objects.get(id=shop_id, admin=request.user)
#                 request.session['active_shop_id'] = shop.id  # Persist in session
#             except Shop.DoesNotExist:
#                 shop = shops.first() if shops.exists() else None
#         else:
#             shop = shops.first() if shops.exists() else None
#             if shop:
#                 request.session['active_shop_id'] = shop.id
        
#         if not shop:
#             return redirect('create_shop')
            
#         context = {
#             'shop': shop,
#             'shops': shops,
#             'active_shop_id': shop.id,  # Explicitly pass to template
#             'show_admin_features': True  # Only for admin
#         }
#         return render(request, 'dashboard_admin.html', context)
    
#     # For supervisor users
#     elif request.user.role == 'supervisor':
#         if not request.user.shop:
#             return redirect('logout')
#         request.session['active_shop_id'] = request.user.shop.id
#         context = {
#             'shop': request.user.shop,
#             'show_admin_features': False  # Hide admin features
#         }
#         return render(request, 'dashboard_admin.html', context)
    
#     # For staff users
#     else:
#         if not request.user.shop:
#             return redirect('logout')
#         request.session['active_shop_id'] = request.user.shop.id
#         return render(request, 'dashboard_staff.html', {'shop': request.user.shop})

@login_required
def dashboard_view(request):
    if request.user.role == 'admin':
        shops = Shop.objects.filter(admin=request.user)
        
        # Get shop_id from URL, session, or default to first shop
        shop_id = request.GET.get('shop_id') or request.session.get('active_shop_id')
        
        if shop_id:
            try:
                shop = Shop.objects.get(id=shop_id, admin=request.user)
                request.session['active_shop_id'] = shop.id
            except Shop.DoesNotExist:
                shop = shops.first() if shops.exists() else None
        else:
            shop = shops.first() if shops.exists() else None
            if shop:
                request.session['active_shop_id'] = shop.id
        
        if not shop:
            return redirect('create_shop')
            
        context = {
            'shop': shop,
            'shops': shops,
            'active_shop_id': shop.id,
            'show_admin_features': True
        }
        return render(request, 'dashboard_admin.html', context)
    
    # For supervisor users
    elif request.user.role == 'supervisor':
        # Get all approved shops for this supervisor
        accessible_shops = Shop.objects.filter(
            supervisor_accesses__supervisor=request.user,  # Changed from supervisor_shop_access
            supervisor_accesses__is_approved=True
        ).distinct()
        
        if not accessible_shops.exists():
            messages.info(request, "You don't have access to any shops yet. Please request access.")
            return redirect('request_shop_access')
            
        # Get selected shop from session or request
        shop_id = request.GET.get('shop_id') or request.session.get('active_shop_id')
        
        if shop_id:
            try:
                shop = accessible_shops.get(id=shop_id)
                request.session['active_shop_id'] = shop.id
            except Shop.DoesNotExist:
                shop = accessible_shops.first()
                request.session['active_shop_id'] = shop.id
        else:
            shop = accessible_shops.first()
            request.session['active_shop_id'] = shop.id
            
        context = {
            'shop': shop,
            'shops': accessible_shops,
            'active_shop_id': shop.id,
            'show_admin_features': False
        }
        return render(request, 'dashboard_admin.html', context)
    
    # For staff users
    else:
        if not request.user.shop:
            return redirect('logout')
        request.session['active_shop_id'] = request.user.shop.id
        return render(request, 'dashboard_staff.html', {'shop': request.user.shop})


@login_required
def manage_staff_view(request):
    if request.user.role != 'admin':
        return redirect('dashboard')  # Only admins can view staff

    staff_members = CustomUser.objects.filter(role='staff', shop=request.user.shop)
    return render(request, 'manage_staff.html', {'staff_members': staff_members})


@login_required
def category_list_view(request):
    """
    View to list categories for the selected shop
    - Admins can view categories for any of their shops
    - Staff can only view categories for their assigned shop
    - Maintains shop selection in session for admins
    """
    
    # Get the appropriate shop based on user role
    if request.user.role == 'admin':
        # For admins, get shop from session or request
        shop_id = request.GET.get('shop_id') or request.session.get('active_shop_id')
        if not shop_id:
            # messages.warning(request, "Please select a shop first")
            return redirect('dashboard')
        
        shop = get_object_or_404(Shop, id=shop_id, admin=request.user)
        request.session['active_shop_id'] = shop.id  # Persist in session
    else:
        # For staff, use their assigned shop
        if not hasattr(request.user, 'shop'):
            # messages.error(request, "No shop assigned to your account")
            return redirect('logout')
        shop = request.user.shop
    
    # Get categories with optimization
    categories = (
        Category.objects
        .filter(shop=shop)
        # .annotate(
        #     item_count=Count('expenseitem'),
        #     last_used=Max('expenseitem__expense__date')
        # )
        .order_by('name')
    )
    
    # For admin users, get all their shops for the dropdown
    if request.user.role == 'admin':
        shops = Shop.objects.filter(admin=request.user)
    else:
        shops = None
    
    context = {
        'categories': categories,
        'shop': shop,
        'shops': shops,  # Only for admin dropdown
        'current_shop_id': shop.id,
    }
    
    return render(request, 'category_list.html', context)


@login_required
def add_category_view(request):
    # Get the active shop based on user role
    if request.user.role == 'admin':
        shop_id = request.session.get('active_shop_id')
        if not shop_id:
            messages.error(request, "Please select a shop first")
            return redirect('dashboard')
        shop = get_object_or_404(Shop, id=shop_id, admin=request.user)
    else:
        shop = request.user.shop

    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.shop = shop  # Use the determined shop
            category.save()
            messages.success(request, "Category added successfully")
            return redirect('category_list')
    else:
        form = CategoryForm()
    
    return render(request, 'add_category.html', {
        'form': form,
        'shop': shop
    })

@login_required
def edit_category_view(request, category_id):
    # Get the active shop based on user role
    if request.user.role == 'admin':
        shop_id = request.session.get('active_shop_id')
        if not shop_id:
            messages.error(request, "Please select a shop first")
            return redirect('dashboard')
        shop = get_object_or_404(Shop, id=shop_id, admin=request.user)
    else:
        shop = request.user.shop

    # Ensure category belongs to the correct shop
    category = get_object_or_404(Category, id=category_id, shop=shop)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "Category updated successfully")
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)
    
    return render(request, 'add_category.html', {
        'form': form,
        'edit': True,
        'shop': shop
    })

@login_required
def delete_category_view(request, category_id):
    # Get the active shop based on user role
    if request.user.role == 'admin':
        shop_id = request.session.get('active_shop_id')
        if not shop_id:
            messages.error(request, "Please select a shop first")
            return redirect('dashboard')
        shop = get_object_or_404(Shop, id=shop_id, admin=request.user)
    else:
        shop = request.user.shop

    # Ensure category belongs to the correct shop
    category = get_object_or_404(Category, id=category_id, shop=shop)
    
    if request.method == 'POST':
        category.delete()
        messages.success(request, "Category deleted successfully")
    
    return redirect('category_list')


# def get_active_shop(request):
#     """Helper function to get the active shop based on user role"""
#     if request.user.role == 'admin':
#         shop_id = request.session.get('active_shop_id')
#         if not shop_id:
#             messages.error(request, "Please select a shop first")
#             return None
#         return get_object_or_404(Shop, id=shop_id, admin=request.user)
#     return request.user.shop

def get_active_shop(request):
    """Helper function to get the active shop based on user role"""
    if request.user.role == 'admin':
        shop_id = request.session.get('active_shop_id')
        if not shop_id:
            messages.error(request, "Please select a shop first")
            return None
        return get_object_or_404(Shop, id=shop_id, admin=request.user)
    elif request.user.role == 'supervisor':
        shop_id = request.session.get('active_shop_id')
        if not shop_id:
            messages.error(request, "Please select a shop first")
            return None
        return get_object_or_404(
            Shop, 
            id=shop_id,
            supervisor_accesses__supervisor=request.user,  # Changed here
            supervisor_accesses__is_approved=True
        )
    return request.user.shop

@login_required
def add_expense(request):
    shop = get_active_shop(request)
    if not shop:
        return redirect('dashboard')

    if request.method == 'POST':
        # Create form without shop parameter
        form = ExpenseForm(request.POST)
        if form.is_valid():
            # Create expense but don't save yet
            expense = form.save(commit=False)
            # Set the shop and added_by manually
            expense.shop = shop
            expense.added_by = request.user
            expense.save()
            
            # Process the items JSON
            items_json = request.POST.get('items_json')
            if items_json:
                try:
                    items_data = json.loads(items_json)
                    for item in items_data:
                        distributor_id = item.get('distributorId')
                        amount = item.get('amount')
                        date = item.get('date')

                        if distributor_id and amount:
                            distributor = get_object_or_404(Distributor, id=distributor_id, shop=shop,type='local')
                            ExpenseItem.objects.create(
                                expense=expense,
                                distributor=distributor,
                                amount=amount,
                                date=date or expense.date
                            )
                except json.JSONDecodeError as e:
                    messages.error(request, "Invalid items data format")
                    return redirect('add_expense')

            messages.success(request, "Expense added successfully")
            return redirect('expense_list')
    else:
        form = ExpenseForm()  # No shop parameter here

    distributors = Distributor.objects.filter(shop=shop, type='local')
    return render(request, 'add_expense.html', {
        'form': form,
        'distributors': distributors,
        'today_date': timezone.now().date().strftime('%Y-%m-%d'),
        'shop': shop
    })

from decimal import InvalidOperation

@login_required
def mark_daily_salary(request):
    shop = get_active_shop(request)
    if not shop:
        return redirect('dashboard')

    employees = Employee.objects.filter(shop=shop, is_active=True)
    
    date_str = request.GET.get('date') or request.POST.get('date')
    try:
        selected_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        selected_date = timezone.now().date()

    existing_salaries = SalaryExpense.objects.filter(
        employee__shop=shop,
        date=selected_date
    ).select_related('employee')

    existing_salaries_dict = {s.employee_id: s for s in existing_salaries}

    if request.method == 'POST':
        expense = Expense.objects.create(
            shop=shop,
            added_by=request.user,
            date=selected_date
        )

        for employee in employees:
            salary_key = f'salary_{employee.id}'
            if salary_key in request.POST and request.POST[salary_key]:
                try:
                    salary_value = Decimal(request.POST[salary_key])
                    notes = request.POST.get(f'notes_{employee.id}', '')
                    
                    if employee.id in existing_salaries_dict:
                        # Update existing
                        salary = existing_salaries_dict[employee.id]
                        salary.amount = salary_value
                        
                        salary.expense = expense
                        salary.save()
                    else:
                        # Create new
                        SalaryExpense.objects.create(
                            expense=expense,
                            employee=employee,
                            amount=salary_value,
                            date=selected_date,
                        )
                except (ValueError, InvalidOperation):
                    continue

        messages.success(request, "Salaries updated successfully")
        return redirect('expense_list')

    return render(request, 'mark_salary.html', {
        'employees': employees,
        'selected_date': selected_date,
        'existing_salaries': existing_salaries_dict,
        'shop': shop
    })

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from django.urls import reverse
from decimal import Decimal
from .models import ExpenseItem, SalaryExpense, OnlinePayment, Shop
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.utils import timezone
from django.urls import reverse
from decimal import Decimal
from .models import ExpenseItem, SalaryExpense, OnlinePayment, Shop, CustomUser
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum
from django.urls import reverse
from decimal import Decimal
from .models import (
    ExpenseItem, 
    SalaryExpense, 
    OnlinePayment,
    Shop
)
from django.db.models import Sum, DecimalField  # Add this import at the top
from decimal import Decimal


@login_required
def expense_list(request):
    # Get the active shop for the user
    if request.user.role == 'admin':
        shop_id = request.GET.get('shop_id') or request.session.get('active_shop_id')
        if not shop_id:
            messages.error(request, "Please select a shop first")
            return redirect('dashboard')
        
        try:
            shop = Shop.objects.get(id=shop_id, admin=request.user)
            request.session['active_shop_id'] = shop.id
        except Shop.DoesNotExist:
            messages.error(request, "Invalid shop selected")
            return redirect('dashboard')
        
    elif request.user.role == 'supervisor':
        # Get shop from session or request
        shop_id = request.GET.get('shop_id') or request.session.get('active_shop_id')
        if not shop_id:
            messages.error(request, "Please select a shop first")
            return redirect('dashboard')
            
        try:
            # Verify supervisor has access to this shop
            shop = Shop.objects.get(
                id=shop_id,
                supervisor_accesses__supervisor=request.user,
                supervisor_accesses__is_approved=True
            )
            request.session['active_shop_id'] = shop.id
        except Shop.DoesNotExist:
            messages.error(request, "You don't have access to this shop")
            return redirect('dashboard')        
    else:
        try:
            shop = request.user.shop
            if not shop:
                messages.error(request, "No shop assigned to your account")
                return redirect('dashboard')
        except AttributeError:
            messages.error(request, "No shop assigned to your account")
            return redirect('dashboard')

    # Handle date filtering
    selected_date_str = request.GET.get('date')
    status_filter = request.GET.get('status', 'all') if request.user.role == 'supervisor' else 'verified'
    
    try:
        selected_date = (timezone.datetime.strptime(selected_date_str, '%Y-%m-%d').date() 
                       if selected_date_str else timezone.now().date())
    except ValueError:
        selected_date = timezone.now().date()
        messages.warning(request, "Invalid date format, showing today's expenses")

    # Handle verification POST request
    if request.method == 'POST' and request.user.role == 'supervisor':
        item_type = request.POST.get('item_type')
        action = request.POST.get('action')
        selected_items = request.POST.get('selected_items', '')
        item_ids = [id for id in selected_items.split(',') if id]
        
        if not item_ids:
            messages.error(request, "No items selected for verification")
            return redirect(f"{reverse('expense_list')}?date={selected_date.strftime('%Y-%m-%d')}&status={status_filter}")

        try:
            model = {
                'expense_item': ExpenseItem,
                'salary': SalaryExpense,
                'online_payment': OnlinePayment
            }.get(item_type)

            if not model:
                raise ValueError("Invalid item type")

            items = model.objects.filter(
                id__in=item_ids,
                expense__shop=shop
            )

            if not items.exists():
                messages.error(request, "No valid items found for verification")
                return redirect(f"{reverse('expense_list')}?date={selected_date.strftime('%Y-%m-%d')}&status={status_filter}")

            update_data = {}
            if action == 'verify':
                update_data = {
                    'is_verified': True,
                    'verified_by': request.user,
                    'verified_at': timezone.now()
                }
                success_message = f"Successfully verified {items.count()} items"
            elif action == 'unverify':
                update_data = {
                    'is_verified': False,
                    'verified_by': None,
                    'verified_at': None
                }
                success_message = f"Successfully unverified {items.count()} items"
            else:
                messages.error(request, "Invalid action specified")
                return redirect(f"{reverse('expense_list')}?date={selected_date.strftime('%Y-%m-%d')}&status={status_filter}")

            items.update(**update_data)
            messages.success(request, success_message)

        except Exception as e:
            messages.error(request, f"Error processing verification: {str(e)}")

        return redirect(f"{reverse('expense_list')}?date={selected_date.strftime('%Y-%m-%d')}&status={status_filter}")

    # Base queryset filters
    base_filters = {
        'expense__shop': shop,
        'date': selected_date
    }

    if request.user.role == 'admin':
        base_filters['is_verified'] = True
    
    elif request.user.role == 'supervisor' and status_filter != 'all':
        base_filters['is_verified'] = status_filter == 'verified'

    # Get filtered querysets
    item_expenses = ExpenseItem.objects.filter(**base_filters).select_related(
        'distributor', 'expense', 'expense__added_by', 'verified_by'
    ).order_by('-date')
    
    salary_entries = SalaryExpense.objects.filter(**base_filters).select_related(
        'employee', 'expense', 'expense__added_by', 'verified_by'
    ).order_by('-date')
    
    online_payments = OnlinePayment.objects.filter(**base_filters).select_related(
        'distributor', 'expense', 'expense__added_by', 'verified_by'
    ).order_by('-date')

    # Calculate financial totals with proper default values
    def calculate_totals(queryset):
        verified = queryset.filter(is_verified=True).aggregate(
            total=Sum('amount', output_field=DecimalField())
        )['total'] or Decimal('0.00')
        
        pending = queryset.filter(is_verified=False).aggregate(
            total=Sum('amount', output_field=DecimalField())
        )['total'] or Decimal('0.00')
        
        return verified, pending

    # Calculate totals for each expense type
    verified_items_total, pending_items_total = calculate_totals(
        ExpenseItem.objects.filter(expense__shop=shop, date=selected_date)
    )
    
    verified_salary_total, pending_salary_total = calculate_totals(
        SalaryExpense.objects.filter(expense__shop=shop, date=selected_date)
    )
    
    verified_online_total, pending_online_total = calculate_totals(
        OnlinePayment.objects.filter(expense__shop=shop, date=selected_date)
    )

    # Calculate overall totals
    total_verified_expense = (
        verified_items_total + 
        verified_salary_total + 
        verified_online_total
    )
    
    total_pending_expense = (
        pending_items_total + 
        pending_salary_total + 
        pending_online_total
    )

    # Pending counts for UI badges
    pending_counts = {
        'items': ExpenseItem.objects.filter(
            expense__shop=shop,
            date=selected_date,
            is_verified=False
        ).count(),
        'salaries': SalaryExpense.objects.filter(
            expense__shop=shop,
            date=selected_date,
            is_verified=False
        ).count(),
        'online': OnlinePayment.objects.filter(
            expense__shop=shop,
            date=selected_date,
            is_verified=False
        ).count()
    }

    context = {
        'item_expenses': item_expenses,
        'salary_entries': salary_entries,
        'online_payments': online_payments,
        'selected_date': selected_date,
        'status_filter': status_filter,
        'verified_items_total': verified_items_total,
        'pending_items_total': pending_items_total,
        'verified_salary_total': verified_salary_total,
        'pending_salary_total': pending_salary_total,
        'verified_online_total': verified_online_total,
        'pending_online_total': pending_online_total,
        'total_verified_expense': total_verified_expense,
        'total_pending_expense': total_pending_expense,
        'pending_items_count': pending_counts['items'],
        'pending_salaries_count': pending_counts['salaries'],
        'pending_online_count': pending_counts['online'],
        'shop': shop,
        'shop_id': shop.id,
        'is_supervisor': request.user.role == 'supervisor',
        'is_admin': request.user.role == 'admin',
        'is_staff': request.user.role == 'staff',
    }

    

    return render(request, 'expense_list.html', context)


from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_POST
from .models import ExpenseItem, SalaryExpense, OnlinePayment

@require_POST
def verify_expense_items(request):
    item_ids = request.POST.getlist('verify_items')
    action = request.POST.get('action')
    
    items = ExpenseItem.objects.filter(id__in=item_ids, expense__shop=request.user.shop)
    
    if action == 'verify':
        items.update(
            is_verified=True,
            verified_by=request.user,
            verified_at=timezone.now()
        )
        messages.success(request, f'{len(item_ids)} expense items verified')
    elif action == 'unverify':
        items.update(
            is_verified=False,
            verified_by=None,
            verified_at=None
        )
        messages.warning(request, f'{len(item_ids)} expense items unverified')
    
    return redirect(request.META.get('HTTP_REFERER', 'expense_list'))

@require_POST
def verify_salary_items(request):
    item_ids = request.POST.getlist('verify_salaries')
    action = request.POST.get('action')
    
    items = SalaryExpense.objects.filter(id__in=item_ids, expense__shop=request.user.shop)
    
    if action == 'verify':
        items.update(
            is_verified=True,
            verified_by=request.user,
            verified_at=timezone.now()
        )
        messages.success(request, f'{len(item_ids)} salary entries verified')
    elif action == 'unverify':
        items.update(
            is_verified=False,
            verified_by=None,
            verified_at=None
        )
        messages.warning(request, f'{len(item_ids)} salary entries unverified')
    
    return redirect(request.META.get('HTTP_REFERER', 'expense_list'))

@require_POST
def verify_online_items(request):
    item_ids = request.POST.getlist('verify_online')
    action = request.POST.get('action')
    
    items = OnlinePayment.objects.filter(id__in=item_ids, expense__shop=request.user.shop)
    
    if action == 'verify':
        items.update(
            is_verified=True,
            verified_by=request.user,
            verified_at=timezone.now()
        )
        messages.success(request, f'{len(item_ids)} online payments verified')
    elif action == 'unverify':
        items.update(
            is_verified=False,
            verified_by=None,
            verified_at=None
        )
        messages.warning(request, f'{len(item_ids)} online payments unverified')
    
    return redirect(request.META.get('HTTP_REFERER', 'expense_list'))


@login_required
def add_online_payment(request):
    shop = get_active_shop(request)
    if not shop:
        return redirect('dashboard')

    if request.method == 'POST':
        form = ExpenseForm(request.POST, shop=shop)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.shop = shop
            expense.added_by = request.user
            expense.save()
            
            # Process items from JSON
            items_json = request.POST.get('items_json')
            if items_json:
                try:
                    items_data = json.loads(items_json)
                    for index, item in enumerate(items_data):
                        distributor_id = item.get('distributorId')
                        invoice_number = item.get('invoiceNumber')
                        amount = Decimal(item.get('amount', 0))
                        date = item.get('date') or expense.date
                        
                        if distributor_id and amount:
                            distributor = get_object_or_404(Distributor, id=distributor_id, shop=shop,type='online')
                            OnlinePayment.objects.create(
                                expense=expense,
                                distributor=distributor,
                                invoice_number=invoice_number,
                                amount=amount,
                                date=date
                            )
                    
                    messages.success(request, "Online payment recorded successfully")
                    return redirect('expense_list')
                    
                except json.JSONDecodeError:
                    messages.error(request, "Invalid items data format")
                except Exception as e:
                    messages.error(request, f"Error processing payment: {str(e)}")
    else:
        form = ExpenseForm(shop=shop)
    
    distributors = Distributor.objects.filter(shop=shop,type='online')
    return render(request, 'add_online_payment.html', {
        'form': form,
        'distributors': distributors,
        'today_date': timezone.now().date().strftime('%Y-%m-%d'),
        'shop': shop
    })

@login_required
def daily_sale_summary(request):
    # Get the active shop
    if request.user.role == 'admin':
        shop_id = request.GET.get('shop_id') or request.session.get('active_shop_id')
        if not shop_id:
            messages.error(request, "Please select a shop first")
            return redirect('dashboard')
        shop = get_object_or_404(Shop, id=shop_id, admin=request.user)
        request.session['active_shop_id'] = shop.id  # Persist in session
    else:
        if not hasattr(request.user, 'shop'):
            messages.error(request, "No shop assigned to your account")
            return redirect('logout')
        shop = request.user.shop

    context = {
        'shop': shop,
        'calculated': False,
        'today': timezone.now().date()
    }

    if request.method == 'POST':
        try:
            # Get and validate input data
            date_str = request.POST.get('date', '')
            selected_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else timezone.now().date()
            
            cash_in_box = Decimal(request.POST.get('cash_in_box', 0))
            cash_in_account = Decimal(request.POST.get('cash_in_account', 0))

            # Calculate daily totals - UPDATED FOR NEW MODEL STRUCTURE
            expense_items_total = (
                ExpenseItem.objects
                .filter(expense__shop=shop, date=selected_date)
                .aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            )

            salary_total = (
                SalaryExpense.objects
                .filter(employee__shop=shop, date=selected_date)
                .aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            )

            online_payment_total = (
                OnlinePayment.objects
                .filter(expense__shop=shop, date=selected_date)
                .aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            )

            # Calculate financial metrics
            total_expense = expense_items_total + salary_total
            total_sale = cash_in_box + cash_in_account + total_expense
            daily_benefit = total_sale - total_expense - online_payment_total

            # Calculate monthly cumulative benefit
            start_of_month = selected_date.replace(day=1)
            previous_daily_benefits = (
                DailySaleSummary.objects
                .filter(shop=shop, date__range=(start_of_month, selected_date - timedelta(days=1)))
                .aggregate(total=Sum('daily_benefit'))['total'] or Decimal('0.00')
            )
            cumulative_monthly_benefit = previous_daily_benefits + daily_benefit

            # Save or update the summary
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

            recalculate_summaries(shop, selected_date + timedelta(days=1))
            
            messages.success(request, "Daily summary saved and recalculated successfully")

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
            messages.success(request, "Daily summary saved successfully")

        except (ValueError, TypeError) as e:
            messages.error(request, f"Invalid input data: {str(e)}")
        except Exception as e:
            messages.error(request, f"Error processing summary: {str(e)}")

    return render(request, 'sale_summary_form.html', context)

@login_required
def recalculate_all(request):
    if request.user.role != 'admin':
        return redirect('dashboard')
    
    shop = get_active_shop(request)
    if not shop:
        return redirect('dashboard')
    
    if request.method == 'POST':
        try:
            # Find the earliest date with data
            first_date = DailySaleSummary.objects.filter(
                shop=shop
            ).order_by('date').first().date
            
            recalculate_summaries(shop, first_date)
            messages.success(request, "All summaries recalculated successfully")
        except Exception as e:
            messages.error(request, f"Recalculation failed: {str(e)}")
            
    return redirect('view_daily_summary')

from datetime import date, timedelta  # Add this import at the top of your views.py
from django.utils import timezone
from django.db import transaction
from datetime import timedelta

@transaction.atomic
def recalculate_summaries(shop, start_date):
    """
    Recalculates all daily summaries from start_date onward
    """
    current_date = start_date
    today = timezone.now().date()
    
    while current_date <= today:
        # Get or create summary for this date
        summary, created = DailySaleSummary.objects.get_or_create(
            shop=shop,
            date=current_date,
            defaults={
                'remaining_cash': Decimal('0.00'),
                'cash_in_account': Decimal('0.00'),
                'total_sale': Decimal('0.00'),
                'daily_benefit': Decimal('0.00'),
                'cumulative_monthly_benefit': Decimal('0.00'),
            }
        )
        
        # Calculate daily totals
        expense_items_total = (
            ExpenseItem.objects
            .filter(expense__shop=shop, date=current_date)
            .aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        )

        salary_total = (
            SalaryExpense.objects
            .filter(employee__shop=shop, date=current_date)
            .aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        )

        online_payment_total = (
            OnlinePayment.objects
            .filter(expense__shop=shop, date=current_date)
            .aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        )

        total_expense = expense_items_total + salary_total
        total_sale = summary.remaining_cash + summary.cash_in_account + total_expense
        daily_benefit = total_sale - total_expense - online_payment_total

        # Calculate cumulative monthly benefit
        if current_date.day == 1:
            # First day of month starts fresh
            cumulative_monthly_benefit = daily_benefit
        else:
            # Get previous day's cumulative
            prev_day = current_date - timedelta(days=1)
            try:
                prev_summary = DailySaleSummary.objects.get(shop=shop, date=prev_day)
                cumulative_monthly_benefit = prev_summary.cumulative_monthly_benefit + daily_benefit
            except DailySaleSummary.DoesNotExist:
                cumulative_monthly_benefit = daily_benefit

        # Update the summary
        summary.total_sale = total_sale
        summary.daily_benefit = daily_benefit
        summary.cumulative_monthly_benefit = cumulative_monthly_benefit
        summary.save()
        
        current_date += timedelta(days=1)




@login_required
def view_daily_summary(request):
    # Get the active shop
    if request.user.role == 'admin':
        shop_id = request.GET.get('shop_id') or request.session.get('active_shop_id')
        if not shop_id:
            messages.error(request, "Please select a shop first")
            return redirect('dashboard')
        shop = get_object_or_404(Shop, id=shop_id, admin=request.user)
        request.session['active_shop_id'] = shop.id  # Persist in session
    else:
        if not hasattr(request.user, 'shop'):
            messages.error(request, "No shop assigned to your account")
            return redirect('logout')
        shop = request.user.shop

    # Handle date selection
    selected_date = None
    if request.method == 'POST':
        date_str = request.POST.get('date', '')
        try:
            selected_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            messages.error(request, "Invalid date format")
    
    if not selected_date:
        selected_date = timezone.now().date()

    # Try to get summary data
    summary = None
    message = None
    try:
        summary = DailySaleSummary.objects.get(shop=shop, date=selected_date)
    except DailySaleSummary.DoesNotExist:
        message = "No summary data found for the selected date."

    # Calculate daily totals - UPDATED FOR NEW MODEL STRUCTURE
    expense_items_total = (
                ExpenseItem.objects
                .filter(expense__shop=shop, date=selected_date)
                .aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            )

    salary_total = (
                SalaryExpense.objects
                .filter(employee__shop=shop, date=selected_date)
                .aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            )

    online_payment_total = (
                OnlinePayment.objects
                .filter(expense__shop=shop, date=selected_date)
                .aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            )

            # Calculate financial metrics
    total_expense = expense_items_total + salary_total
            # total_sale = cash_in_box + cash_in_account + total_expense
            # daily_benefit = total_sale - total_expense - online_payment_total

    # Prepare last 7 days data for chart
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

    # Prepare monthly cumulative data for chart
    monthly_data = []
    current_year = selected_date.year
    for month in range(1, 13):  # All 12 months
        # Get the first and last day of the month
        first_day = date(current_year, month, 1)
        if month == 12:
            last_day = date(current_year, month, 31)
        else:
            last_day = date(current_year, month+1, 1) - timedelta(days=1)
        
        # Get all summaries for this month up to selected date
        if first_day.year == selected_date.year and first_day.month == selected_date.month:
            last_day = selected_date  # Only include up to selected date for current month
        
        monthly_summaries = DailySaleSummary.objects.filter(
            shop=shop,
            date__range=[first_day, last_day]
        ).order_by('date')
        
        # Calculate cumulative benefit for the month
        cumulative_benefit = 0
        for summary in monthly_summaries:
            cumulative_benefit += float(summary.daily_benefit)
        
        monthly_data.append({
            'month': first_day,
            'cumulative_benefit': cumulative_benefit
        })

    return render(request, 'view_sale_summary.html', {
        'shop': shop,
        'selected_date': selected_date,
        'summary': summary,
        'message': message,
        'last_7_days': last_7_days,
        'monthly_data': monthly_data,
        'today': timezone.now().date(),
        'total_expense':total_expense,
        'online_payment_total':online_payment_total
    })



@login_required
def employee_list(request):
    shop = get_active_shop(request)
    if not shop:
        return redirect('dashboard')
    
    employees = Employee.objects.filter(shop=shop).order_by('name')
    return render(request, 'employees_list.html', {
        'employees': employees,
        'shop': shop
    })

@login_required
def add_employee(request):
    shop = get_active_shop(request)
    if not shop:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            employee = form.save(commit=False)
            employee.shop = shop
            employee.created_by = request.user
            employee.save()
            messages.success(request, f"Employee {employee.name} added successfully")
            return redirect('employee_list')
    else:
        form = EmployeeForm()
    
    return render(request, 'add_employees.html', {
        'form': form,
        'shop': shop
    })


@login_required
def distributor_list(request):
    shop = get_active_shop(request)
    if not shop:
        return redirect('dashboard')
    
    distributors = Distributor.objects.filter(shop=shop)
    return render(request, 'distributors_list.html', {
        'distributors': distributors,
        'shop': shop
    })

@login_required
def add_distributor(request):
    shop = get_active_shop(request)
    if not shop:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = DistributorForm(request.POST)
        if form.is_valid():
            distributor = form.save(commit=False)
            distributor.shop = shop
            distributor.save()
            return redirect('distributor_list')
    else:
        form = DistributorForm()
    
    return render(request, 'add_distributors.html', {
        'form': form,
        'shop': shop
    })

@login_required
def edit_distributor(request, pk):
    shop = get_active_shop(request)
    if not shop:
        return redirect('dashboard')
    
    distributor = get_object_or_404(Distributor, pk=pk, shop=shop)
    
    if request.method == 'POST':
        form = DistributorForm(request.POST, instance=distributor, shop=shop)
        if form.is_valid():
            form.save()
            messages.success(request, "Distributor updated successfully")
            return redirect('distributor_list')
    else:
        form = DistributorForm(instance=distributor, shop=shop)
    
    return render(request, 'distributors/distributor_form.html', {
        'form': form,
        'title': 'Edit Distributor',
        'shop': shop
    })

@login_required
def delete_distributor(request, pk):
    shop = get_active_shop(request)
    if not shop:
        return redirect('dashboard')
    
    distributor = get_object_or_404(Distributor, pk=pk, shop=shop)
    
    if request.method == 'POST':
        distributor.delete()
        messages.success(request, "Distributor deleted successfully")
        return redirect('distributor_list')
    
    return render(request, 'confirm_delete.html', {
        'distributor': distributor,
        'shop': shop
    })


# views.py
@login_required
def pending_approvals(request):
    if request.user.role != 'admin':
        return redirect('dashboard')
    
    # Get pending users for the admin's shops
    pending_users = CustomUser.objects.filter(
        Q(role='staff') | Q(role='supervisor'),
        approval_status='pending',
        shop__admin=request.user
    ).select_related('shop')
    
    return render(request, 'pending_approvals.html', {
        'pending_users': pending_users
    })
@login_required
def approve_user(request, user_id):
    if request.method != 'POST':
        return redirect('combined_approvals')
    
    if request.user.role != 'admin':
        messages.error(request, "Only admins can approve users")
        return redirect('dashboard')
    
    try:
        user = get_object_or_404(
            CustomUser,
            id=user_id,
            approval_status='pending',
            shop__admin=request.user
        )
        
        user.approval_status = 'approved'
        user.is_active = True
        user.save()
        
        messages.success(request, f"Approved user: {user.email}")
        shop_id = request.POST.get('shop_id', '')
        return redirect(f"{reverse('combined_approvals')}?shop_id={shop_id}")
    
    except Exception as e:
        messages.error(request, f"Approval failed: {str(e)}")
        return redirect('combined_approvals')
@login_required
def reject_user(request, user_id):
    if request.method != 'POST':
        return redirect('combined_approvals')
    
    if request.user.role != 'admin':
        messages.error(request, "Only admins can reject users")
        return redirect('dashboard')
    
    try:
        user = get_object_or_404(
            CustomUser,
            id=user_id,
            approval_status='pending',
            shop__admin=request.user
        )
        
        user.approval_status = 'rejected'
        user.save()
        
        messages.success(request, f"Rejected user: {user.email}")
        shop_id = request.POST.get('shop_id', '')
        return redirect(f"{reverse('combined_approvals')}?shop_id={shop_id}")
    
    except Exception as e:
        messages.error(request, f"Rejection failed: {str(e)}")
        return redirect('combined_approvals')
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import OnlinePayment, Shop

@login_required
def shop_bills_view(request, shop_id):
    shop = get_object_or_404(Shop, id=shop_id)
    
    # Get unpaid bills
    unpaid_bills = OnlinePayment.objects.filter(
        expense__shop=shop,
        status='unpaid'
    ).order_by('date')
    
    # Get paid bills (last 30 days)
    paid_bills = OnlinePayment.objects.filter(
        expense__shop=shop,
        status='paid'
    ).order_by('-paid_at')[:50]  # Limit to 50 most recent
    
    context = {
        'shop': shop,
        'unpaid_bills': unpaid_bills,
        'paid_bills': paid_bills,
    }
    return render(request, 'shop_bills.html', context)

from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
import traceback
# views.py
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)
@require_POST
@login_required
def mark_payment_paid(request, payment_id):
    try:
        # Get payment with safe attribute access
        payment = OnlinePayment.objects.select_related(
            'expense__shop',
            'distributor',
            'paid_by'
        ).get(pk=payment_id)
        
        logger.info(f"Processing payment {payment_id} - Current status: {payment.status}")

        # Verify critical relationships exist
        if not hasattr(payment, 'expense') or payment.expense is None:
            logger.error(f"Payment {payment_id} has no expense attached")
            return JsonResponse({
                'success': False,
                'message': 'Payment record is missing expense information'
            }, status=400)

        if not hasattr(payment.expense, 'shop') or payment.expense.shop is None:
            logger.error(f"Payment {payment_id} has no shop assigned")
            return JsonResponse({
                'success': False,
                'message': 'Payment record is missing shop information'
            }, status=400)

        # Verify user permissions
        try:
            if not request.user.shops.filter(id=payment.expense.shop.id).exists():
                logger.warning(f"Permission denied for user {request.user} on shop {payment.expense.shop}")
                return JsonResponse({
                    'success': False,
                    'message': 'You do not have permission for this payment'
                }, status=403)
        except Exception as e:
            logger.error(f"Permission check failed: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': 'Error verifying permissions'
            }, status=500)

        # Check payment status
        if payment.status == 'paid':
            return JsonResponse({
                'success': False,
                'message': 'Payment is already marked as paid'
            }, status=400)

        # Mark as paid - using direct assignment instead of model method
        payment.status = 'paid'
        payment.paid_by = request.user
        payment.paid_at = timezone.now()
        try:
            payment.save(update_fields=['status', 'paid_by', 'paid_at'])
        except Exception as e:
            logger.error(f"Failed to save payment: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': 'Failed to update payment status'
            }, status=500)

        # Prepare success response
        response_data = {
            'success': True,
            'message': f'Payment #{payment.invoice_number} marked as paid',
            'payment': {
                'invoice_number': payment.invoice_number or '-',
                'distributor': payment.distributor.name if payment.distributor else 'Unknown',
                'amount': str(payment.amount),
                'paid_at': payment.paid_at.strftime("%b %d, %Y") if payment.paid_at else 'Just now',
                'paid_by': payment.paid_by.get_full_name() if payment.paid_by else request.user.get_full_name()
            }
        }
        
        return JsonResponse(response_data)

    except OnlinePayment.DoesNotExist:
        logger.error(f"Payment not found: {payment_id}")
        return JsonResponse({
            'success': False,
            'message': 'Payment not found'
        }, status=404)
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}\n{traceback.format_exc()}")
        return JsonResponse({
            'success': False,
            'message': 'Internal server error'
        }, status=500)
    

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from .models import OnlinePayment, Shop  # Make sure to import your Shop model

class ShopBillsView(LoginRequiredMixin, TemplateView):
    template_name = 'shop_bills.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get shop_id from URL parameters or session
        shop_id = self.request.GET.get('shop_id') or self.request.session.get('active_shop_id')
        
        if not shop_id:
            # Handle case where no shop_id is provided
            # You might want to redirect or show an error
            pass
            
        # Get the shop object
        shop = get_object_or_404(Shop, id=shop_id)
        
        # Get unpaid bills
        unpaid_bills = OnlinePayment.objects.filter(
            status='unpaid',
            expense__shop=shop
        ).select_related('distributor', 'expense')
        
        # Get recently paid bills (last 10)
        paid_bills = OnlinePayment.objects.filter(
            status='paid',
            expense__shop=shop
        ).select_related('distributor', 'paid_by').order_by('-paid_at')[:10]
        
        context.update({
            'unpaid_bills': unpaid_bills,
            'paid_bills': paid_bills,
            'shop': shop  # Pass the actual shop object
        })
        return context
from django.http import JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

class MarkBillPaidView(LoginRequiredMixin, View):
    def post(self, request, bill_id):
        try:
            bill = OnlinePayment.objects.get(id=bill_id)
            if bill.status != 'paid':
                bill.status = 'paid'
                bill.paid_by = request.user
                bill.paid_at = timezone.now()
                bill.save()
                return JsonResponse({'success': True})
            return JsonResponse({'success': False, 'error': 'Bill already paid'})
        except OnlinePayment.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Bill not found'}, status=404)


@login_required
def request_shop_access(request):
    if request.user.role != 'supervisor':
        return redirect('dashboard')

    if request.method == 'POST':
        form = ShopAccessRequestForm(request.POST)
        if form.is_valid():
            try:
                # Create the access request directly without using form.save()
                access = SupervisorShopAccess.objects.create(
                    supervisor=request.user,
                    shop=form.cleaned_data['shop_code'],
                    is_approved=False
                )
                messages.success(request, "Shop access requested successfully. Waiting for admin approval.")
                return redirect('my_shop_access')
            except Exception as e:
                messages.error(request, f"Error requesting access: {str(e)}")
    else:
        form = ShopAccessRequestForm()

    return render(request, 'request_shop_access.html', {'form': form})

@login_required
def my_shop_access(request):
    if request.user.role != 'supervisor':
        return redirect('dashboard')

    accesses = SupervisorShopAccess.objects.filter(supervisor=request.user)
    return render(request, 'my_shop_access.html', {'accesses': accesses})

@login_required
def manage_supervisor_access(request):
    if request.user.role != 'admin':
        return redirect('dashboard')

    # Get pending access requests for shops this admin owns
    pending_requests = SupervisorShopAccess.objects.filter(
        shop__admin=request.user,
        is_approved=False
    ).select_related('supervisor', 'shop')

    return render(request, 'manage_supervisor_access.html', {
        'pending_requests': pending_requests
    })

@login_required
def approve_supervisor_access(request, access_id):
    if request.method != 'POST' or request.user.role != 'admin':
        return redirect('dashboard')

    try:
        access = SupervisorShopAccess.objects.get(
            id=access_id,
            shop__admin=request.user,
            is_approved=False
        )
        access.is_approved = True
        access.approved_at = timezone.now()
        access.approved_by = request.user
        access.save()
        messages.success(request, f"Access to {access.shop.name} approved for {access.supervisor.username}")
    except SupervisorShopAccess.DoesNotExist:
        messages.error(request, "Access request not found or already approved")

    return redirect('manage_supervisor_access')

@login_required
def reject_supervisor_access(request, access_id):
    if request.method != 'POST' or request.user.role != 'admin':
        return redirect('dashboard')

    try:
        access = SupervisorShopAccess.objects.get(
            id=access_id,
            shop__admin=request.user
        )
        access.delete()
        messages.success(request, f"Access request rejected")
    except SupervisorShopAccess.DoesNotExist:
        messages.error(request, "Access request not found")

    return redirect('manage_supervisor_access')
# @login_required
# def combined_approvals(request):
#     if request.user.role != 'admin':
#         return redirect('dashboard')
    
#     # Get pending user approvals
#     pending_users = CustomUser.objects.filter(
#         Q(role='staff') | Q(role='supervisor'),
#         approval_status='pending',
#         shop__admin=request.user
#     ).select_related('shop')
    
#     # Get pending supervisor access requests
#     pending_access_requests = SupervisorShopAccess.objects.filter(
#         shop__admin=request.user,
#         is_approved=False
#     ).select_related('supervisor', 'shop')
    
#     # Get approved users (staff and supervisors)
#     approved_users = CustomUser.objects.filter(
#         Q(role='staff') | Q(role='supervisor'),
#         approval_status='approved',
#         shop__admin=request.user
#     ).select_related('shop')
    
#     return render(request, 'combined_approvals.html', {
#         'pending_users': pending_users,
#         'pending_access_requests': pending_access_requests,
#         'approved_users': approved_users
#     })


@login_required
def combined_approvals(request):
    if request.user.role != 'admin':
        return redirect('dashboard')
    
    # Get pending user approvals
    pending_users = CustomUser.objects.filter(
        Q(role='staff') | Q(role='supervisor'),
        approval_status='pending',
        shop__admin=request.user
    ).select_related('shop')
    
    # Get pending supervisor access requests
    pending_access_requests = SupervisorShopAccess.objects.filter(
        shop__admin=request.user,
        is_approved=False
    ).select_related('supervisor', 'shop')
    
    # Get approved staff (non-supervisors)
    approved_staff = CustomUser.objects.filter(
        role='staff',
        approval_status='approved',
        shop__admin=request.user
    ).select_related('shop')
    
    # Get approved supervisors with their shop accesses
    approved_supervisors = CustomUser.objects.filter(
        role='supervisor',
        approval_status='approved'
    ).prefetch_related(
        'supervisor_accesses',
        'supervisor_accesses__shop'
    )
    
    # Create a list of supervisors with their shop accesses
    supervisors_with_shops = []
    for supervisor in approved_supervisors:
        accesses = SupervisorShopAccess.objects.filter(
            supervisor=supervisor,
            shop__admin=request.user,
            is_approved=True
        ).select_related('shop')
        if accesses.exists():
            supervisors_with_shops.append({
                'supervisor': supervisor,
                'shops': [access.shop for access in accesses]
            })
    
    return render(request, 'combined_approvals.html', {
        'pending_users': pending_users,
        'pending_access_requests': pending_access_requests,
        'approved_staff': approved_staff,
        'supervisors_with_shops': supervisors_with_shops
    })
@login_required
def revoke_supervisor_access(request, user_id):
    if request.method != 'POST' or request.user.role != 'admin':
        return redirect('dashboard')

    try:
        user = get_object_or_404(
            CustomUser,
            id=user_id,
            role='supervisor'
        )
        
        shop_id = request.GET.get('shop_id')
        
        if shop_id:
            # Revoke access for a specific shop
            shop = get_object_or_404(Shop, id=shop_id, admin=request.user)
            SupervisorShopAccess.objects.filter(
                supervisor=user,
                shop=shop
            ).delete()
            messages.success(request, f"Access revoked for {user.username} at {shop.name}")
        else:
            # Revoke all accesses (if no shop specified)
            SupervisorShopAccess.objects.filter(
                supervisor=user,
                shop__admin=request.user
            ).delete()
            messages.success(request, f"All access revoked for {user.username}")
            
    except Exception as e:
        messages.error(request, f"Error revoking access: {str(e)}")
    
    return redirect('combined_approvals')