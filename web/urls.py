from django.urls import path
from . import views
from .views import (
    ProductDetailView,
    CategoryDetailView,
    CartView,
    AddToCartView,
    DeleteFromCartView,
    ChangeQTYView,
    CheckoutView,
    MakeOrderView,
)

urlpatterns = [
    path('', views.index, name='index'),
    path('shop/', views.shop, name='shop'),
    path('shop/products/<str:ct_model>/<str:slug>/', ProductDetailView.as_view(), name='shop_product_detail'),
    path('shop/category/<str:slug>/', CategoryDetailView.as_view(), name='category_detail'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('cart/', CartView.as_view(), name='cart'),
    path('add-to-cart/products/<str:ct_model>/<str:slug>/', AddToCartView.as_view(), name='add_to_cart'),
    path('remove-from-cart/products/<str:ct_model>/<str:slug>/', DeleteFromCartView.as_view(), name='delete-from-cart'),
    path('change-qty/products/<str:ct_model>/<str:slug>/', ChangeQTYView.as_view(), name='change-qty'),
    path('shop-checkout/', CheckoutView.as_view(), name='shop-checkout'),
    path('make-order/', MakeOrderView.as_view(), name='make-order'),

]
