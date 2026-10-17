"""
Señales = funciones que Django ejecuta automáticamente cuando pasa algo.

Aquí: cada vez que se guarda un usuario (auth_user), nos aseguramos de que
tenga su Perfil y de que el rol y el campo is_staff coincidan.
"""
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Perfil

User = get_user_model()


@receiver(post_save, sender=User)
def sincronizar_perfil(sender, instance, created, **kwargs):
    rol_esperado = Perfil.ROL_ADMIN if (instance.is_staff or instance.is_superuser) else Perfil.ROL_CLIENTE
    perfil, nuevo = Perfil.objects.get_or_create(usuario=instance, defaults={'rol': rol_esperado})
    if not nuevo and perfil.rol != rol_esperado:
        perfil.rol = rol_esperado
        perfil.save(update_fields=['rol', 'actualizado'])
