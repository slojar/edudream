from threading import Thread
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import *


@receiver(post_save, sender=Country)
def country_post_save(sender, instance, **kwargs):
    if not Country.objects.filter(is_default=True).exists():
        instance.is_default = True
        instance.save()
    
    if instance.is_default:
        Country.objects.filter(is_default=True).exclude(id=instance.id).update(is_default=False)
        

