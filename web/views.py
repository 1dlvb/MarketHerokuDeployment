from django.db import transaction, OperationalError
from django.shortcuts import render, get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.views.generic import DetailView, View
from django.http import HttpResponseRedirect, Http404, HttpResponseNotFound
from django.contrib import messages
import MySQLdb

from .models import Products, Bikes, Cranksets, Forks, Wheels, Accessories, GlassesAndMasks, LatestProducts, Category, \
    Customer, Cart, CartProduct
from .mixins import CategoryDetailMixin, CartMixin
from .forms import OrderForm
from .utils import recalc_cart


# home page
def index(request):
    products_for_home_page = []
    if Category.objects.get_categories_for_main_and_shop_pages():
        categories = Category.objects.get_categories_for_main_and_shop_pages()
        context = {
            'products': LatestProducts.objects.get_products_to_show_on_the_page(True, 'bikes', 'forks', 'wheels',
                                                                                with_respect_to='bikes'),
            'categories': categories,


        }
    else:
        context = {}

    return render(request, 'web/index.html', context=context)


# Category detail page
class CategoryDetailView(CartMixin, CategoryDetailMixin, DetailView):

    model = Category
    queryset = Category.objects.all()
    context_object_name = 'category'
    slug_url_kwarg = 'slug'


# shop page
def shop(request):
    categories = Category.objects.get_categories_for_main_and_shop_pages()

    context = {
        'products': LatestProducts.objects.get_products_to_show_on_the_page(False, 'bikes', 'forks', 'wheels',
                                                                            'accessories', 'glassesandmasks',
                                                                            'cranksets'),
        'categories': categories,

    }
    return render(request, 'web/shop.html', context=context)


# Product detail page
class ProductDetailView(CartMixin, CategoryDetailMixin, DetailView):
    CT_MODEL_MODEL_CLASS = {
        'bikes': Bikes,
        'cranksets': Cranksets,
        'wheels': Wheels,
        'forks': Forks,
        'accessories': Accessories,
        'glasses_and_masks': GlassesAndMasks,
    }

    def dispatch(self, request, *args, **kwargs):
        self.model = self.CT_MODEL_MODEL_CLASS[kwargs['ct_model']]
        self.queryset = self.model._base_manager.all()
        return super().dispatch(request, *args, **kwargs)

    context_object_name = 'product'
    template_name = 'web/shop-single-product.html'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['ct_model'] = self.model._meta.model_name
        return context


# Add to cart
class AddToCartView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        ct_model, product_slug = kwargs.get('ct_model'), kwargs.get('slug')
        content_type = ContentType.objects.get(model=ct_model)
        product = content_type.model_class().objects.get(slug=product_slug)
        cart_product, created = CartProduct.objects.get_or_create(
            customer=self.cart.owner,
            cart=self.cart,
            content_type=content_type,
            object_id=product.id,
        )
        if created:
            self.cart.products.add(cart_product)
        recalc_cart(self.cart)
        return HttpResponseRedirect('/cart/')


class DeleteFromCartView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        ct_model, product_slug = kwargs.get('ct_model'), kwargs.get('slug')
        content_type = ContentType.objects.get(model=ct_model)
        product = content_type.model_class().objects.get(slug=product_slug)
        cart_product = CartProduct.objects.get(
            customer=self.cart.owner,
            cart=self.cart,
            content_type=content_type,
            object_id=product.id,
        )
        self.cart.products.remove(cart_product)
        cart_product.delete()
        recalc_cart(self.cart)
        return HttpResponseRedirect('/cart/')


class ChangeQTYView(CartMixin, View):

    def post(self, request, *args, **kwargs):
        ct_model, product_slug = kwargs.get('ct_model'), kwargs.get('slug')
        content_type = ContentType.objects.get(model=ct_model)
        product = content_type.model_class().objects.get(slug=product_slug)
        cart_product = CartProduct.objects.get(
            customer=self.cart.owner,
            cart=self.cart,
            content_type=content_type,
            object_id=product.id,
        )
        qty = int(request.POST.get('qty'))
        cart_product.quantity = qty
        cart_product.save()
        recalc_cart(self.cart)
        return HttpResponseRedirect('/cart/')


# Cart page
class CartView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        categories = Category.objects.get_categories_for_main_and_shop_pages()
        context = {
            'cart': self.cart,
            'categories': categories
        }
        return render(request, 'web/shop-cart.html', context=context)


# Shop checkout page
class CheckoutView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        categories = Category.objects.get_categories_for_main_and_shop_pages()
        form = OrderForm(request.POST or None)
        context = {
            'cart': self.cart,
            'categories': categories,
            'form': form,
        }
        return render(request, 'web/shop-checkout.html', context=context)


class MakeOrderView(CartMixin, View):

    errorCode = []
    @transaction.atomic
    def post(self, request, *arg, **kwargs):
        try:
            form = OrderForm(request.POST or None)
            customer = Customer.objects.get(user=request.user)
            if form.is_valid():
                new_order = form.save(commit=False)
                new_order.customer = customer
                new_order.first_name = form.cleaned_data['first_name']
                new_order.second_name = form.cleaned_data['second_name']
                new_order.phone_number = form.cleaned_data['phone_number']
                new_order.address = form.cleaned_data['address']
                new_order.buying_type = form.cleaned_data['buying_type']
                new_order.order_date = form.cleaned_data['order_date']
                new_order.save()

                self.cart.in_order = True
                self.cart.save()
                new_order.cart = self.cart
                new_order.save()

                customer.orders.add(new_order)
                messages.info(request, "Thank you for your order! Hope to see you here again!")
                return HttpResponseRedirect('/')
            messages.info(request, "There is some error! Check if you entered data correctly!")
            return HttpResponseRedirect('/shop-checkout')
        except OperationalError:
            return HttpResponseNotFound('<h1>Page not found<h1>')


# about page
def about(request):
    context = {
    }
    return render(request, 'web/about.html', context=context)


# contact page
def contact(request):
    context = {
    }
    return render(request, 'web/contact.html', context=context)
