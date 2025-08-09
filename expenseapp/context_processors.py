# In your_app/context_processors.py

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