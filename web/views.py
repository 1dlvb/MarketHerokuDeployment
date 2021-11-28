from django.db import transaction, OperationalError
from django.db.models import Q
from django.shortcuts import render
from django.views.generic import DetailView, View
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.template.defaulttags import register
from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string


from .models import Product, Customer, Cart, CartProduct, Category, Order
from .mixins import CartMixin
from .forms import OrderForm, LoginForm, RegistrationForm, ContactForm
from .utils import recalc_cart
from decouple import config as cfg


@register.filter
def get_range(value):
    return range(value)


# home page
def index(request):
    products_for_home_page = []
    if Category.objects.all():
        categories = Category.objects.all()
        context = {
            'products': Product.objects.all(),
            'categories': categories,


        }
    else:
        context = {}

    return render(request, 'web/index.html', context=context)


# ###### CATEGORY VIEWS ###### #
# Category detail page
class CategoryDetailView(CartMixin, DetailView):

    model = Category
    queryset = Category.objects.all()
    context_object_name = 'category'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('search')
        category = self.get_object()
        context['cart'] = self.cart
        context['categories'] = self.model.objects.all()
        if not query and not self.request.GET:
            context['category_products'] = category.product_set.all()
            return context
        if query:
            products = category.product_set.filter(Q(title__icontains=query))
            context['category_products'] = products
            return context
        url_kwargs = {}
        for item in self.request.GET:
            if len(self.request.GET.getlist(item)) > 1:
                url_kwargs[item] = self.request.GET.getlist(item)
            else:
                url_kwargs[item] = self.request.GET.get(item)
        q_condition_queries = Q()
        for key, value in url_kwargs.items():
            if isinstance(value, list):
                q_condition_queries.add(Q(**{'value__in': value}), Q.OR)
            else:
                q_condition_queries.add(Q(**{'value': value}), Q.OR)
        return context


# ###### SHOP VIEWS ###### #
# shop page
def shop(request):
    categories = Category.objects.all()

    context = {
        'products': Product.objects.all(),
        'categories': categories,

    }
    return render(request, 'web/shop.html', context=context)


# Product detail page
class ProductDetailView(CartMixin, DetailView):
    model = Product
    context_object_name = 'product'
    template_name = 'web/shop-single-product.html'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['cart'] = self.cart
        return context


# ###### CART VIEWS ###### #
# Add to cart
class AddToCartView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        product_slug = kwargs.get('slug')
        product = Product.objects.get(slug=product_slug)
        cart_product, created = CartProduct.objects.get_or_create(
            customer=self.cart.owner,
            cart=self.cart,
            product=product,
        )
        if created:
            self.cart.products.add(cart_product)
        recalc_cart(self.cart)
        return HttpResponseRedirect('/cart/')


class DeleteFromCartView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        product_slug = kwargs.get('slug')
        product = Product.objects.get(slug=product_slug)
        cart_product = CartProduct.objects.get(
            customer=self.cart.owner,
            cart=self.cart,
            product=product,
        )
        self.cart.products.remove(cart_product)
        cart_product.delete()
        recalc_cart(self.cart)
        return HttpResponseRedirect('/cart/')


class ChangeQTYView(CartMixin, View):

    def post(self, request, *args, **kwargs):
        product_slug = kwargs.get('slug')
        product = Product.objects.get(slug=product_slug)
        cart_product = CartProduct.objects.get(
            customer=self.cart.owner,
            cart=self.cart,
            product=product,
        )
        qty = int(request.POST.get('qty'))
        cart_product.quantity = qty
        cart_product.save()
        recalc_cart(self.cart)
        return HttpResponseRedirect('/cart/')


# Cart page
class CartView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        categories = Category.objects.all()
        context = {
            'cart': self.cart,
            'categories': categories
        }
        return render(request, 'web/shop-cart.html', context=context)


# Shop checkout page
class CheckoutView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        categories = Category.objects.all()
        form = OrderForm(request.POST or None)
        context = {
            'cart': self.cart,
            'categories': categories,
            'form': form,
        }
        return render(request, 'web/shop-checkout.html', context=context)


class MakeOrderView(CartMixin, View):

    @transaction.atomic
    def post(self, request, *arg, **kwargs):
        try:
            form = OrderForm(request.POST or None)
            customer = Customer.objects.get(user=request.user)
            if form.is_valid():
                new_order = form.save(commit=False)
                new_order.customer = customer
                new_order.first_name = form.cleaned_data['first_name']
                new_order.last_name = form.cleaned_data['last_name']
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
            return render(request, 'web/page-not-found.html')


# ###### AUTH VIEWS ###### #
# Registration page
class RegistrationView(View):

    def get(self, request, *args, **kwargs):
        form = RegistrationForm(request.POST or None)
        categories = Category.objects.all()
        context = {
            'form': form,
            'categories': categories,
        }
        return render(request, 'web/registration.html', context=context)

    def post(self, request, *args, **kwargs):
        form = RegistrationForm(request.POST or None)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.username = form.cleaned_data['username']
            new_user.email = form.cleaned_data['email']
            new_user.first_name = form.cleaned_data['first_name']
            new_user.last_name = form.cleaned_data['last_name']
            new_user.save()
            new_user.set_password(form.cleaned_data['password'])
            new_user.save()
            Customer.objects.create(
                user=new_user,
                phone_number=form.cleaned_data['phone_number'],
            )
            user = authenticate(
                  username=form.cleaned_data['username'],
                  password=form.cleaned_data['password']
            )
            login(request, user)
            return HttpResponseRedirect('/')

        context = {
            'form': form,
            'categories': Category.objects.all(),
        }
        return render(request, 'web/registration.html', context=context)


# Login page
class LoginView(View):

    def get(self, request, *args, **kwargs):
        form = LoginForm(request.POST or None)
        categories = Category.objects.all()
        context = {
            'form': form,
            'categories': categories,
        }
        return render(request, 'web/login.html', context=context)

    def post(self, request, *args, **kwargs):
        form = LoginForm(request.POST or None)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(
                username=username,
                password=password
            )
            if user:
                login(request, user)
                return HttpResponseRedirect('/')
        context = {
            'form': form,
        }
        return render(request, 'web/login.html', context)


def logout_view(request):
    logout(request)
    return HttpResponseRedirect('/')


class ProfileView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        customer = Customer.objects.get(user=request.user)
        orders = Order.objects.filter(customer=customer).order_by('-created_at')
        categories = Category.objects.all()
        context = {
            'orders': orders,
            'cart': self.cart,
            'categories': categories,
        }
        return render(request, 'web/profile.html', context=context)


# ###### OTHER VIEWS ###### #
# about page
def about(request):
    context = {
    }
    return render(request, 'web/about.html', context=context)


# contact page
def contact(request):
    if request.method == 'POST':
        name = request.POST.get('full-name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        checkbox = request.POST.get('checkbox')

        context = {
            'name': name,
            'email': email,
            'subject': subject,
            'message': message,
            'checkbox': checkbox,
        }
        if request.user.username:
            username = request.user.username
        else:
            username = ' '
        message = f"MESSAGE: {message}\n\n\n\n EMAIL: {email}\n USERNAME: {username}\n"
        email = EmailMessage(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [cfg('EMAIL_HOST_USER')])
        email.fail_silently = False
        email.send()
        return render(request, 'web/contact.html', context=context)

    context = {}
    return render(request, 'web/contact.html', context=context)

