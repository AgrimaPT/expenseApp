from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser,Shop,Distributor,Expense,Employee,SupervisorShopAccess
from django.utils.crypto import get_random_string

class SignupForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['email', 'username', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'admin'  # force role as admin
        if commit:
            user.save()
        return user

  
class StaffSignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    shop_code = forms.CharField(max_length=10)

    class Meta:
        model = CustomUser
        fields = ['email', 'username', 'password', 'shop_code']

    # def save(self, commit=True):
    #     user = super().save(commit=False)
    #     user.set_password(self.cleaned_data['password'])
    #     if commit:
    #         user.save()
    #     return user

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.role = 'staff'
        user.is_active = False  # Should match approval_status
        user.approval_status = 'pending'  # Explicitly set
        if commit:
            user.save()
        return user
    


# forms.py
class SupervisorSignupForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
        min_length=8,
        help_text="Password must be at least 8 characters long"
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput,
        help_text="Enter the same password as above for verification"
    )

    class Meta:
        model = CustomUser
        fields = ['email', 'username']

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.role = 'supervisor'
        user.is_active = True  # Needs admin approval
        user.approval_status = 'approved'
        
        if commit:
            user.save()
        return user
    


# forms.py
class ShopAccessRequestForm(forms.ModelForm):
    shop_code = forms.CharField(
        max_length=10,
        help_text="Enter the shop code you want to access"
    )

    class Meta:
        model = SupervisorShopAccess
        fields = ['shop_code']

    def clean_shop_code(self):
        shop_code = self.cleaned_data['shop_code'].strip()
        try:
            return Shop.objects.get(shop_code=shop_code)
        except Shop.DoesNotExist:
            raise forms.ValidationError("Invalid shop code. Please check and try again.")

    # def save(self, supervisor, commit=True):
    #     access = super().save(commit=False)
    #     access.supervisor = supervisor
    #     access.shop = self.cleaned_data['shop_code']
        
    #     if commit:
    #         access.save()
    #     return access


class LoginForm(AuthenticationForm):
    username = forms.EmailField(label="Email")  # since login is by email


class ShopForm(forms.ModelForm):
    class Meta:
        model = Shop
        fields = ['name', 'owner_name', 'phone', 'email', 'address']
        
    def save(self, commit=True):
        shop = super().save(commit=False)
        if not shop.shop_code:  # Only generate if not already set
            shop.shop_code = get_random_string(8).upper()
        if commit:
            shop.save()
        return shop
# class CategoryForm(forms.ModelForm):
#     class Meta:
#         model = Category
#         fields = ['name']

# forms.py
from django import forms
from django.forms import inlineformset_factory
from .models import Expense, ExpenseItem

# class ExpenseForm(forms.ModelForm):
#     class Meta:
#         model = Expense
#         fields = ['shop', 'date']  # added_by will be set in the view


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['date']  # removed 'shop' since we'll set it in the view

    def __init__(self, *args, **kwargs):
        self.shop = kwargs.pop('shop', None)  # Remove shop from kwargs
        super().__init__(*args, **kwargs)
        self.fields['date'].widget = forms.DateInput(attrs={'type': 'date'})

# class ExpenseItemForm(forms.ModelForm):
#     class Meta:
#         model = ExpenseItem
#         fields = ['category', 'quantity', 'price']

# ExpenseItemFormSet = inlineformset_factory(
#     Expense, ExpenseItem,
#     form=ExpenseItemForm,
#     extra=1,  # number of empty forms shown
#     can_delete=True
# )


class ExpenseItemForm(forms.ModelForm):
    class Meta:
        model = ExpenseItem
        fields = ['distributor', 'amount', 'date',]

ExpenseItemFormSet = inlineformset_factory(
    Expense, ExpenseItem,
    form=ExpenseItemForm,
    extra=1,  # number of empty forms shown
    can_delete=True
)

from django import forms

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['name', 'phone', 'position', 'is_active']
        widgets = {
            'phone': forms.TextInput(attrs={'placeholder': '9876543210'}),
            'position': forms.TextInput(attrs={'placeholder': 'e.g. Cashier, Manager'}),
        }
from django import forms
from .models import Distributor

class DistributorForm(forms.ModelForm):
    class Meta:
        model = Distributor
        fields = ['name', 'type', 'contact_person', 'phone']
        widgets = {
            'type': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'name': 'Distributor Name',
            'type': 'Distributor Type',
            'contact_person': 'Contact Person',
            'phone': 'Phone Number',
        }

    def __init__(self, *args, **kwargs):
        self.shop = kwargs.pop('shop', None)
        super(DistributorForm, self).__init__(*args, **kwargs)
        
        # If you want to customize the type field choices
        self.fields['type'].choices = Distributor.DISTRIBUTOR_TYPES

    def save(self, commit=True):
        distributor = super().save(commit=False)
        if self.shop:
            distributor.shop = self.shop
        if commit:
            distributor.save()
        return distributor