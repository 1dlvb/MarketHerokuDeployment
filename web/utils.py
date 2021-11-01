from django.db import models


def recalc_cart(cart):
    cart_data = cart.products.aggregate(models.Sum('final_price'), models.Count('id'))
    if cart_data.get('final_price__sum'):
        cart.final_price = round(cart_data['final_price__sum'] + cart.shipping_price, 2)
    else:
        cart.final_price = 0
    cart.total_products = cart_data['id__count']
    cart.save()