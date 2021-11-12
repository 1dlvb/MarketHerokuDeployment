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
    LoginView,
    RegistrationView,
    ProfileView,

)

urlpatterns = [
    path('', views.index, name='index'),

    path('shop', views.shop, name='shop'),
    path('shop/products/<str:slug>/', ProductDetailView.as_view(), name='product_detail'),
    path('shop/category/<str:slug>/', CategoryDetailView.as_view(), name='category_detail'),

    path('about', views.about, name='about'),
    path('contact', views.contact, name='contact'),

    path('cart/', CartView.as_view(), name='cart'),
    path('add-to-cart/products/<str:slug>/', AddToCartView.as_view(), name='add_to_cart'),
    path('remove-from-cart/products/<str:slug>/', DeleteFromCartView.as_view(), name='delete-from-cart'),
    path('change-qty/products/<str:slug>/', ChangeQTYView.as_view(), name='change-qty'),
    path('shop-checkout/', CheckoutView.as_view(), name='shop-checkout'),
    path('make-order/', MakeOrderView.as_view(), name='make-order'),

    path('login/', LoginView.as_view(), name='login'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('logout/', views.logout_view, name='logout'),
    path('sign-in/', RegistrationView.as_view(), name='sign-in'),
]
