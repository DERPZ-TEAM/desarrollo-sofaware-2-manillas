from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Perfil

User = get_user_model()


@receiver(post_save, sender=User)
def crear_perfil(sender, instance, created, **kwargs):
    if created:
        rol = Perfil.ROL_ADMIN if instance.is_staff else Perfil.ROL_CLIENTE
        Perfil.objects.get_or_create(usuario=instance, defaults={'rol': rol})
    elif hasattr(instance, 'perfil'):
        rol = Perfil.ROL_ADMIN if instance.is_staff else Perfil.ROL_CLIENTE
        if instance.perfil.rol != rol:
            instance.perfil.rol = rol
            instance.perfil.save(update_fields=['rol'])
