from django.urls import path
from . import views
from .views import ShopBillsView,MarkBillPaidView

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('staff-signup/', views.staff_signup_view, name='staff_signup'),
    path('supervisor-signup/', views.supervisor_signup_view, name='supervisor_signup'),
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




    path('my-shops/', views.shop_list, name='shop_list'),
    path('shops/edit/<int:shop_id>/', views.edit_shop, name='edit_shop'),
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/add/', views.add_employee, name='add_employee'),

    path('distributors/', views.distributor_list, name='distributor_list'),
    path('distributors/add/', views.add_distributor, name='add_distributor'),
    path('distributors/<int:pk>/edit/', views.edit_distributor, name='edit_distributor'),
    path('distributors/<int:pk>/delete/', views.delete_distributor, name='delete_distributor'),


   # urls.py
    # path('approvals/', views.pending_approvals, name='pending_approvals'),
    

    path('expenses/verify-items/', views.verify_expense_items, name='verify_expense_items'),
    path('expenses/verify-salaries/', views.verify_salary_items, name='verify_salary_items'),
    path('expenses/verify-online/', views.verify_online_items, name='verify_online_items'),

    path('shop/<int:shop_id>/bills/', views.shop_bills_view, name='shop_bills'),
    path('payments/<int:payment_id>/mark-paid/', views.mark_payment_paid, name='mark_payment_paid'),

    path('shop-bills/', ShopBillsView.as_view(), name='shop_bills'),
    path('mark-bill-paid/<int:bill_id>/', MarkBillPaidView.as_view(), name='mark_bill_paid'),



    path('request-shop-access/', views.request_shop_access, name='request_shop_access'),
    path('my-shop-access/', views.my_shop_access, name='my_shop_access'),
    path('manage-supervisor-access/', views.manage_supervisor_access, name='manage_supervisor_access'),
    path('approve-supervisor-access/<int:access_id>/', views.approve_supervisor_access, name='approve_supervisor_access'),
    path('reject-supervisor-access/<int:access_id>/', views.reject_supervisor_access, name='reject_supervisor_access'),

    path('approvals/', views.combined_approvals, name='combined_approvals'),
    path('approvals/approve/<int:user_id>/', views.approve_user, name='approve_user'),
    path('approvals/reject/<int:user_id>/', views.reject_user, name='reject_user'),

    path('approvals/revoke/<int:user_id>/', views.revoke_supervisor_access, name='revoke_supervisor_access'),

]
