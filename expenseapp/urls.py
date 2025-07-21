from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('staff-signup/', views.staff_signup_view, name='staff_signup'),
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('create-shop/', views.create_shop, name='create_shop'),  # ✅ This fixes the error
    path('manage-staff/', views.manage_staff_view, name='manage_staff'),
    path('categories/', views.category_list_view, name='category_list'),
    path('categories/add/', views.add_category_view, name='add_category'),
    path('categories/edit/<int:category_id>/', views.edit_category_view, name='edit_category'),
    path('categories/delete/<int:category_id>/', views.delete_category_view, name='delete_category'),
    path('expenses/add/', views.add_expense, name='add_expense'),
    path('expenses/', views.expense_list, name='expense_list'),
    path('mark-salary/', views.mark_daily_salary, name='mark_salary'),
    path('add-online-payment/', views.add_online_payment, name='add_online_payment'),
    path('sale-summary/', views.daily_sale_summary, name='daily_sale_summary'),
    path('view-summary/', views.view_daily_summary, name='view_daily_summary'),


]
