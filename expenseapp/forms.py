from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser,Shop,Category,Expense

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

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.EmailField(label="Email")  # since login is by email


class ShopForm(forms.ModelForm):
    class Meta:
        model = Shop
        fields = ['name', 'owner_name', 'phone', 'email', 'address']

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']

# forms.py
from django import forms
from django.forms import inlineformset_factory
from .models import Expense, ExpenseItem

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['shop', 'date']  # added_by will be set in the view

class ExpenseItemForm(forms.ModelForm):
    class Meta:
        model = ExpenseItem
        fields = ['category', 'quantity', 'price']

ExpenseItemFormSet = inlineformset_factory(
    Expense, ExpenseItem,
    form=ExpenseItemForm,
    extra=1,  # number of empty forms shown
    can_delete=True
)
