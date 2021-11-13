from django.db import models
from django.core.exceptions import ValidationError
from django.core.files.images import get_image_dimensions
from multiselectfield import MultiSelectField
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone


User = get_user_model()

# --------------- #
# Category        |
# Product         |
# CartProduct     |
# Cart            |
# Order           |
# --------------- #
# Customer        |
# Specifications  |
# --------------- #

# FUNCTIONS

# check image size function
def check_image(image, size_w, size_h):
    if not image:
        raise ValidationError("No image!")
    else:
        w, h = get_image_dimensions(image)
        if w != size_w:
            raise ValidationError("The image is {0} pixel wide. It's supposed to be {1}px".format(w, size_w))
        if h != size_h:
            raise ValidationError("The image is {0} pixel height. It's supposed to be {1}px".format(h, size_h))


# CLASSES and MODELS

# Category
class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name='Category name')
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"

    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'slug': self.slug})


class Product(models.Model):
    title = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)
    description = models.TextField(max_length=500)
    detailed_description = models.TextField(max_length=1500, blank=True)

    availability = models.PositiveIntegerField(default=0)

    thumbnail_image = models.ImageField(upload_to='img/', null=False, blank=False)
    big_image = models.ImageField(upload_to='img/', null=False, blank=False)

    price = models.DecimalField(decimal_places=2, max_digits=8, default=0)
    old_price = models.DecimalField(decimal_places=2, max_digits=12, default=0)

    category = models.ForeignKey(Category, verbose_name='Category', on_delete=models.CASCADE)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('product_detail', kwargs={'slug': self.slug})

    def clean(self):
        check_image(self.thumbnail_image, 360, 480)
        check_image(self.big_image, 600, 800)

    def get_model_name(self):
        return self.__class__.__name__.lower()


# Cart Product
class CartProduct(models.Model):
    customer = models.ForeignKey('Customer', verbose_name='Customer', on_delete=models.CASCADE)
    cart = models.ForeignKey('Cart', verbose_name='Cart', on_delete=models.CASCADE, related_name='related_products')
    product = models.ForeignKey(Product, verbose_name='Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, verbose_name='Product')
    final_price = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Final price')

    def __str__(self):
        return 'Product {} for cart'.format(self.product.title)

    def save(self, *args, **kwargs):
        self.final_price = self.quantity * self.product.price
        super().save(*args, **kwargs)


# Cart
class Cart(models.Model):
    owner = models.ForeignKey('Customer', verbose_name='Owner', null=True, on_delete=models.CASCADE)
    products = models.ManyToManyField(CartProduct, blank=True, related_name='related_cart')
    total_products = models.PositiveIntegerField(default=0)
    final_price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Final price', default=0)
    in_order = models.BooleanField(default=False)
    shipping_price = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Shipping price')
    for_anonymous_users = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name_plural = "Cart"


# Customer
class Customer(models.Model):
    user = models.ForeignKey(User, verbose_name='User', on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    address = models.CharField(max_length=20, null=True, blank=True)
    orders = models.ManyToManyField('Order', verbose_name="Customer's orders", related_name='related_customer')

    def __str__(self):
        return 'Buyer: {} {}'.format(self.user.first_name, self.user.last_name)


# Order
class Order(models.Model):

    STATUS_NEW = 'new'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_READY = 'is_ready'
    STATUS_COMPLETED = 'is_completed'

    BUYING_TYPE_SELF = 'self'
    BUYING_TYPE_DELIVERY = 'delivery'

    STATUS_CHOICES = (
        (STATUS_NEW, 'New order'),
        (STATUS_IN_PROGRESS, 'Order in progress'),
        (STATUS_READY, 'Order is ready'),
        (STATUS_COMPLETED, 'Order completed'),
    )

    BUYING_TYPE_CHOICES = (
        (BUYING_TYPE_SELF, 'Pickup'),
        (STATUS_IN_PROGRESS, 'Delivery'),
    )

    customer = models.ForeignKey(Customer, verbose_name='Buyer', related_name='related_orders', on_delete=models.CASCADE)
    first_name = models.CharField(max_length=255, verbose_name='Name')
    last_name = models.CharField(max_length=255, verbose_name='Last Name')
    phone_number = models.CharField(max_length=22, verbose_name='Phone Number')
    cart = models.ForeignKey(Cart, verbose_name='Cart', on_delete=models.CASCADE, null=True, blank=True)
    address = models.CharField(max_length=255, verbose_name='Address, ZIP Code', null=True, blank=True)
    status = models.CharField(
        max_length=255,
        verbose_name='Order status',
        choices=STATUS_CHOICES,
        default=STATUS_NEW)
    buying_type = models.CharField(
            max_length=255,
            verbose_name='Order type',
            choices=BUYING_TYPE_CHOICES,
            default=BUYING_TYPE_SELF)
    comment = models.TextField(verbose_name='Comment for order', blank=True, null=True)
    created_at = models.DateTimeField(auto_now=True, verbose_name='Order creation date')
    order_date = models.DateField(verbose_name='Date of receipt of the order', default=timezone.now)

    def __str__(self):
        return str(self.id)


###################
MATERIAL = ((1, 'Carbon'),
            (2, 'Aluminium'),
            (3, 'Titan'),
            (4, 'Steel'))

WHEEL_SIZE = ((1, '24'),
              (2, '26'),
              (3, '27.5'),
              (4, '29'))

