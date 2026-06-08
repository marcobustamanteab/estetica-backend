import threading
import logging
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)

User = get_user_model()


@receiver(pre_save, sender=User)
def store_old_email(_sender, instance, **_kwargs):
    """Guarda el email anterior para detectar cambios en post_save."""
    if not instance.pk:
        return
    try:
        instance._old_email = User.objects.get(pk=instance.pk).email
    except User.DoesNotExist:
        instance._old_email = None


@receiver(post_save, sender=User)
def handle_user_saved(_sender, instance, created, **_kwargs):
    if instance.is_superuser:
        return
    if not instance.email:
        return

    if created:
        # Usuario nuevo: crear y compartir calendario
        if not instance.google_calendar_id:
            _run_in_thread(_setup_employee_google_calendar, instance.id)
    else:
        # Usuario existente: recompartir si cambió el email
        old_email = getattr(instance, '_old_email', None)
        if old_email and old_email != instance.email:
            _run_in_thread(
                _reshare_calendar_on_email_change,
                instance.id, old_email, instance.email
            )


def _run_in_thread(fn, *args):
    thread = threading.Thread(target=fn, args=args, daemon=False)
    thread.start()


def _setup_employee_google_calendar(user_id):
    try:
        from services.google_calendar_service import GoogleCalendarService

        user = User.objects.get(pk=user_id)
        if user.google_calendar_id:
            return

        logger.info(f"📅 Creando calendario Google para: {user.get_full_name()} ({user.email})")
        svc = GoogleCalendarService()
        calendar_id = svc.create_employee_calendar(
            user.get_full_name() or user.username,
            user.email
        )
        if calendar_id:
            user.google_calendar_id = calendar_id
            user.save(update_fields=['google_calendar_id'])
            logger.info(f"✅ Calendario creado y compartido con {user.email}")
        else:
            logger.error(f"❌ No se pudo crear calendario para {user.username}")

    except Exception as e:
        logger.error(f"❌ Error creando calendario para usuario {user_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())


def _reshare_calendar_on_email_change(user_id, old_email, new_email):
    try:
        from services.google_calendar_service import GoogleCalendarService

        user = User.objects.get(pk=user_id)
        if not user.google_calendar_id:
            # No tenía calendario aún: crearlo directamente con el nuevo email
            logger.info(f"📅 Sin calendario previo, creando para nuevo email: {new_email}")
            svc = GoogleCalendarService()
            calendar_id = svc.create_employee_calendar(
                user.get_full_name() or user.username,
                new_email
            )
            if calendar_id:
                user.google_calendar_id = calendar_id
                user.save(update_fields=['google_calendar_id'])
            return

        logger.info(f"🔄 Email cambiado ({old_email} → {new_email}), actualizando acceso al calendario...")
        svc = GoogleCalendarService()
        svc.update_calendar_sharing(user.google_calendar_id, old_email, new_email)

    except Exception as e:
        logger.error(f"❌ Error actualizando calendario tras cambio de email (user {user_id}): {e}")
        import traceback
        logger.error(traceback.format_exc())
