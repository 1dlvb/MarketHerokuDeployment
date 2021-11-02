from django.db import models
from django.core.exceptions import ValidationError
from django.core.files.images import get_image_dimensions
from multiselectfield import MultiSelectField
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
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


# get models for count
def get_models_for_count(*model_names):
    return [models.Count(model_name) for model_name in model_names]


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
#
def get_product_url(obj, view_name):
    ct_model = obj.__class__._meta.model_name
    return reverse(view_name, kwargs={'ct_model': ct_model, 'slug': obj.slug})


# Latest Products Manager
class LatestProductsManager:

    @staticmethod
    def get_products_to_show_on_the_page(limit_or_not, *args, **kwargs):
        with_respect_to = kwargs.get('with_respect_to')
        products = []
        ct_models = ContentType.objects.filter(model__in=args)
        if limit_or_not is False:
            for ct_model in ct_models:
                model_products = ct_model.model_class()._base_manager.all().order_by('-id')
                products.extend(model_products)
        elif limit_or_not is True:
            for ct_model in ct_models:
                model_products = ct_model.model_class()._base_manager.all().order_by('-id')[:5]
                products.extend(model_products)
            pass
        if with_respect_to:
            ct_model = ContentType.objects.filter(model=with_respect_to)
            if ct_model.exists():
                if with_respect_to in args:
                    return sorted(products, key=lambda x: x.__class__._meta.model_name.startswith(with_respect_to),
                                  reverse=True)
        return products


# Latest Products
class LatestProducts:
    objects = LatestProductsManager()


class CategoryManager(models.Manager):

    CATEGORY_NAME_COUNT_NAME = {
        'Bikes': 'bikes__count',
        'Wheels': 'wheels__count',
        'Accessories': 'accessories__count',
        'Glasses and Masks': 'glassesandmasks__count',
        'Forks': 'forks__count',
        'Cranksets': 'cranksets__count',
    }

    def get_queryset(self):
        return super().get_queryset()

    def get_categories_for_main_and_shop_pages(self):
        models = get_models_for_count('bikes', 'wheels', 'glassesandmasks', 'forks', 'cranksets', 'accessories')
        qs = list(self.get_queryset().annotate(*models))
        data = [
            dict(name=c.name, url=c.get_absolute_url(), count=getattr(c, self.CATEGORY_NAME_COUNT_NAME[c.name]))
            for c in qs
        ]

        return data


# Category
class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name='Category name')
    slug = models.SlugField(unique=True)
    objects = CategoryManager()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"

    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'slug': self.slug})


class Products(models.Model):
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

    def clean(self):
        check_image(self.thumbnail_image, 360, 480)
        check_image(self.big_image, 600, 800)

    class Meta:
        abstract = True

    def get_model_name(self):
        return self.__class__.__name__.lower()


# Cart Product
class CartProduct(models.Model):
    customer = models.ForeignKey('Customer', verbose_name='Customer', on_delete=models.CASCADE)
    cart = models.ForeignKey('Cart', verbose_name='Cart', on_delete=models.CASCADE, related_name='related_products')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Product')
    final_price = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Final price')

    def __str__(self):
        return 'Product {} for cart)'.format(self.content_object.title)

    def save(self, *args, **kwargs):
        self.final_price = self.quantity * self.content_object.price
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
    second_name = models.CharField(max_length=255, verbose_name='Second Name')
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


# Bikes
class Bikes(Products):
    Brakes = models.CharField(max_length=100)
    Fork = models.CharField(max_length=100)
    Transmission = models.CharField(max_length=100)
    Frame_material = MultiSelectField(choices=MATERIAL,
                                      max_choices=1,
                                      default=1)
    Wheel_size = MultiSelectField(choices=WHEEL_SIZE,
                                  max_choices=1,
                                  default=1)

    def get_absolute_url(self):
        return get_product_url(self, 'shop_product_detail')

    def __str__(self):
        return "{} : {}".format(self.category.name, self.title)

    class Meta:
        verbose_name_plural = "Bikes"


# Cranksets
class Cranksets(Products):
    Chainline = models.CharField(max_length=50)
    Material = MultiSelectField(choices=MATERIAL,
                                max_choices=1,
                                default=1)

    def get_absolute_url(self):
        return get_product_url(self, 'shop_product_detail')

    def __str__(self):
        return "{} : {}".format(self.category.name, self.title)

    class Meta:
        verbose_name_plural = "Cranksets"


# Forks
class Forks(Products):
    Travel = models.CharField(max_length=10)
    Steerer_Diameter = models.CharField(max_length=35)
    Wheel_size = MultiSelectField(choices=WHEEL_SIZE,
                                  max_choices=1,
                                  default=1)

    def get_absolute_url(self):
        return get_product_url(self, 'shop_product_detail')

    def __str__(self):
        return "{} : {}".format(self.category.name, self.title)

    class Meta:
        verbose_name_plural = "Forks"


# Wheels
class Wheels(Products):
    Brake_Rotor_Mount_Type = models.CharField(max_length=10)
    Rim_Internal_Width = models.DecimalField(max_digits=4, decimal_places=2)
    Tubeless_Ready = models.BooleanField()
    Material = MultiSelectField(choices=MATERIAL,
                                max_choices=1,
                                default=1)
    Wheel_size = MultiSelectField(choices=WHEEL_SIZE,
                                  max_choices=1,
                                  default=1)

    def get_absolute_url(self):
        return get_product_url(self, 'shop_product_detail')

    def __str__(self):
        return "{} : {}".format(self.category.name, self.title)

    class Meta:
        verbose_name_plural = "Wheels"


# Accessories
class Accessories(Products):
    type = models.CharField(max_length=25)

    def get_absolute_url(self):
        return get_product_url(self, 'shop_product_detail')

    def __str__(self):
        return "{} : {}".format(self.category.name, self.title)

    class Meta:
        verbose_name_plural = "Accessories"


# Glasses and Masks
class GlassesAndMasks(Products):
    color = models.CharField(max_length=35)
    Change_lenses = models.BooleanField(blank=False)

    def get_absolute_url(self):
        return get_product_url(self, 'shop_product_detail')

    def __str__(self):
        return "{} : {}".format(self.category.name, self.title)

    class Meta:
        verbose_name_plural = "Glasses and Masks"
