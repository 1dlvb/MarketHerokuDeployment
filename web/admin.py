from django.contrib import admin
from django import forms
from django.forms import ModelChoiceField

from .models import *

# Register your models here.


# We make only a category of bikes for bikes
class BikesAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'category':
            return ModelChoiceField(Category.objects.filter(slug='Bikes'))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# We make only a category of wheels for wheels
class WheelsAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'category':
            return ModelChoiceField(Category.objects.filter(slug='Wheels'))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# We make only a category of GlassesAndMasks for GlassesAndMasks
class GlassesAndMasksAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'category':
            return ModelChoiceField(Category.objects.filter(slug='GlassesAndMasks'))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# We make only a category of Forks for Forks
class ForksAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'category':
            return ModelChoiceField(Category.objects.filter(slug='Forks'))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# We make only a category of Cranksets for Cranksets
class CranksetsAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'category':
            return ModelChoiceField(Category.objects.filter(slug='Cranksets'))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# We make only a category of Accessories for Accessories
class AccessoriesAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'category':
            return ModelChoiceField(Category.objects.filter(slug='Accessories'))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(Category)
admin.site.register(Customer)
admin.site.register(Cart)
admin.site.register(CartProduct)
admin.site.register(Order)

admin.site.register(Bikes, BikesAdmin)
admin.site.register(Cranksets, CranksetsAdmin)
admin.site.register(Forks, ForksAdmin)
admin.site.register(Wheels, WheelsAdmin)
admin.site.register(Accessories, AccessoriesAdmin)
admin.site.register(GlassesAndMasks, GlassesAndMasksAdmin)

