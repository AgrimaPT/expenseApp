from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.conf import settings
from django.utils.crypto import get_random_string
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.utils.crypto import get_random_string

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('supervisor', 'Supervisor'),
        ('staff', 'Staff'),
        ('partner', 'Partner'),
    )

    APPROVAL_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='staff')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    approval_status = models.CharField(
        max_length=10, 
        choices=APPROVAL_STATUS_CHOICES, 
        default='pending'
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = CustomUserManager()

    def __str__(self):
        return self.email

# Define Shop model after CustomUser
class Shop(models.Model):
    name = models.CharField(max_length=100)
    owner_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    shop_code = models.CharField(max_length=10, unique=True, default=get_random_string(8))
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    admin = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='admin_shops', null=True)
    def __str__(self):
        return f"{self.name} ({self.shop_code})"

# Now add the shop field to CustomUser after Shop is defined
CustomUser.add_to_class('shop', models.ForeignKey(
    Shop, 
    on_delete=models.SET_NULL, 
    null=True, 
    blank=True,
    related_name='staff_members'
))


# models.py
class SupervisorShopAccess(models.Model):
    supervisor = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'supervisor'},
        related_name='supervisor_accesses'
    )
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE,related_name='supervisor_accesses')
    is_approved = models.BooleanField(default=False)
    requested_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_accesses'
    )

    class Meta:
        unique_together = ['supervisor', 'shop']
        verbose_name_plural = 'Supervisor Shop Accesses'

    def __str__(self):
        return f"{self.supervisor} -> {self.shop} ({'Approved' if self.is_approved else 'Pending'})"


# models.py


# Create PartnerShopAccess model (similar to SupervisorShopAccess)
class PartnerShopAccess(models.Model):
    partner = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'partner'},
        related_name='partner_accesses'
    )
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='partner_accesses')
    is_approved = models.BooleanField(default=False)
    requested_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_partner_accesses'
    )

    class Meta:
        unique_together = ['partner', 'shop']
        verbose_name_plural = 'Partner Shop Accesses'

    def __str__(self):
        return f"{self.partner} -> {self.shop} ({'Approved' if self.is_approved else 'Pending'})"


# class Category(models.Model):
#     shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
#     name = models.CharField(max_length=100)
    
#     def __str__(self):
#         return f"{self.name} ({self.shop})"
    
class Distributor(models.Model):
    DISTRIBUTOR_TYPES = (
        ('online', 'Online'),
        ('local', 'Local'),
    )
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='distributors')
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=DISTRIBUTOR_TYPES)
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"
    
class Employee(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='employees')
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    position = models.CharField(max_length=100, blank=True,null=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.phone}) - {self.shop.name}"

class Expense(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    added_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Expense on {self.date} by {self.shop.name}"

# class ExpenseItem(models.Model):
#     expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name='items')
#     category = models.ForeignKey(Category, on_delete=models.CASCADE)
#     quantity = models.DecimalField(max_digits=10, decimal_places=2)
#     price = models.DecimalField(max_digits=10, decimal_places=2)

#     @property
#     def amount(self):
#         return self.quantity * self.price

#     def __str__(self):
#         return f"{self.category.name} - {self.quantity} x {self.price}"


class ExpenseItem(models.Model):
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name='items')
    distributor = models.ForeignKey(Distributor, on_delete=models.CASCADE,null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.now)
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='verified_expense_items'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.distributor.name} - {self.amount} - {self.date}"

    def save(self, *args, **kwargs):
        # Ensure distributor belongs to the same shop as the expense
        if self.distributor.shop != self.expense.shop:
            raise ValueError("Distributor must belong to the same shop as the expense")
        super().save(*args, **kwargs)

class SalaryExpense(models.Model):
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name='salaries')
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE)
    # employee = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'staff'})
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.now)
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='verified_salaries'
    )
    verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.employee.name} - {self.amount} on {self.date}"

# class OnlinePayment(models.Model):
#     expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name='online_payments')
#     bill_number = models.CharField(max_length=100, blank=True, null=True)
#     bill_image = models.ImageField(upload_to='bill_images/', blank=True, null=True)
#     category = models.ForeignKey(Category, on_delete=models.CASCADE)
#     quantity = models.DecimalField(max_digits=10, decimal_places=2)
#     price = models.DecimalField(max_digits=10, decimal_places=2)

#     @property
#     def amount(self):
#         return self.quantity * self.price
    
#     def __str__(self):
#         return f"{self.category.name} - {self.quantity} x {self.price}"
class OnlinePayment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
    ]
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name='online_payments')
    distributor = models.ForeignKey(Distributor, on_delete=models.CASCADE,null=True, blank=True)
    invoice_number = models.CharField(max_length=100,null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.now)
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='verified_online_payments'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=10,
        choices=PAYMENT_STATUS_CHOICES,
        default='unpaid'
    )
    paid_at = models.DateTimeField(null=True, blank=True)
    paid_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='paid_online_payments'
    )

    def __str__(self):
        return f"{self.distributor.name} - {self.invoice_number} - {self.amount}"

    def save(self, *args, **kwargs):
    # Only check distributor relation if both exist
        if self.distributor and hasattr(self, 'expense') and self.expense:
            if self.distributor.shop != self.expense.shop:
                raise ValueError("Distributor must belong to the same shop as the expense")
        
        # # Record payment timestamp when status changes to paid
        # if self.pk:  # Only for existing instances
        #     original = OnlinePayment.objects.get(pk=self.pk)
        #     if original.status != 'paid' and self.status == 'paid':
        #         self.paid_at = timezone.now()
        # elif self.status == 'paid':  # New instance being created as paid
        #     self.paid_at = timezone.now()
            
        super().save(*args, **kwargs)

    def get_payment_status_display(self):
        """Get human-readable payment status with icons"""
        if self.status == 'paid':
            return mark_safe(f'<span class="badge bg-success"><i class="fas fa-check-circle me-1"></i> Paid</span>')
        return mark_safe(f'<span class="badge bg-danger"><i class="fas fa-exclamation-circle me-1"></i> Unpaid</span>')


        
    def mark_as_paid(self, user):
        """More robust version of mark_as_paid"""
        if self.status != 'paid':
            self.status = 'paid'
            self.paid_by = user
            self.paid_at = timezone.now()
            self.save(update_fields=['status', 'paid_by', 'paid_at'])


class DailySaleSummary(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    date = models.DateField()
    remaining_cash = models.DecimalField(max_digits=10, decimal_places=2)
    cash_in_account = models.DecimalField(max_digits=10, decimal_places=2)
    total_sale = models.DecimalField(max_digits=12, decimal_places=2)
    daily_benefit = models.DecimalField(max_digits=12, decimal_places=2)
    cumulative_monthly_benefit = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        unique_together = ['shop', 'date']

