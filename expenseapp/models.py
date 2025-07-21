from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.conf import settings

from django.utils.crypto import get_random_string

class Shop(models.Model):
    name = models.CharField(max_length=100)
    owner_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    shop_code = models.CharField(max_length=10, unique=True, default=get_random_string(8))
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.shop_code})"


# CATEGORY_TYPES = (
#     ('income', 'Income'),
#     ('expense', 'Expense'),
# )

# class Category(models.Model):
#     shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
#     name = models.CharField(max_length=100)
#     # category_type = models.CharField(max_length=10, choices=CATEGORY_TYPES)

#     def __str__(self):
#         return f"{self.name} ({self.category_type})"

class Category(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.name} ({self.shop})"

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
        ('staff', 'Staff'),
    )

    shop = models.ForeignKey(Shop, on_delete=models.SET_NULL, null=True, blank=True)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='staff')

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = CustomUserManager()

    def __str__(self):
        return self.email

class Expense(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    added_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Expense on {self.date} by {self.shop.name}"

class ExpenseItem(models.Model):
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name='items')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def amount(self):
        return self.quantity * self.price

    def __str__(self):
        return f"{self.category.name} - {self.quantity} x {self.price}"

class SalaryExpense(models.Model):
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name='salaries')
    employee = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'staff'})
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.employee.username} - {self.amount} on {self.date}"


class OnlinePayment(models.Model):
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name='online_payments')
    bill_number = models.CharField(max_length=100, blank=True, null=True)
    bill_image = models.ImageField(upload_to='bill_images/', blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def amount(self):
        return self.quantity * self.price
    
    def __str__(self):
        return f"{self.category.name} - {self.quantity} x {self.price}"

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

