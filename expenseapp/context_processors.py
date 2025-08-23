# In your_app/context_processors.py
from django.db.models import Q
from .models import CustomUser, SupervisorShopAccess

from .models import Shop
def shop_context(request):
    context = {}
    if request.user.is_authenticated:
        if request.user.role == 'admin':
            shop_id = request.session.get('active_shop_id')
            if shop_id:
                try:
                    context['active_shop'] = Shop.objects.get(id=shop_id, admin=request.user)
                except Shop.DoesNotExist:
                    pass
        elif hasattr(request.user, 'shop'):
            context['active_shop'] = request.user.shop
    return context

# def pending_requests(request):
#     context = {}
#     if request.user.is_authenticated and request.user.role == 'admin':
#         pending_users_count = CustomUser.objects.filter(
#             Q(role='staff') | Q(role='supervisor'),
#             approval_status='pending',
#             shop__admin=request.user
#         ).count()
        
#         pending_access_requests_count = SupervisorShopAccess.objects.filter(
#             shop__admin=request.user,
#             is_approved=False
#         ).count()
        
#         context['pending_requests_count'] = pending_users_count + pending_access_requests_count
#     else:
#         context['pending_requests_count'] = 0
#     return context


# In your_app/context_processors.py
from django.db.models import Q
from .models import CustomUser, SupervisorShopAccess, PartnerShopAccess

def pending_requests(request):
    context = {}
    if request.user.is_authenticated and request.user.role == 'admin':
        # Count pending user approvals (staff and supervisor)
        pending_users_count = CustomUser.objects.filter(
            Q(role='staff') | Q(role='supervisor') | Q(role='partner'),
            approval_status='pending',
            shop__admin=request.user
        ).count()
        
        # Count pending supervisor access requests
        pending_supervisor_requests_count = SupervisorShopAccess.objects.filter(
            shop__admin=request.user,
            is_approved=False
        ).count()
        
        # Count pending partner access requests
        pending_partner_requests_count = PartnerShopAccess.objects.filter(
            shop__admin=request.user,
            is_approved=False
        ).count()
        
        # Total all pending requests
        context['pending_requests_count'] = (
            pending_users_count + 
            pending_supervisor_requests_count + 
            pending_partner_requests_count
        )
    else:
        context['pending_requests_count'] = 0
    return context