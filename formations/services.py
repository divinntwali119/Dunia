import logging

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from .models import Certificate, Enrollment, Formation, Lesson, LessonProgress, Payment


logger = logging.getLogger(__name__)
ACTIVE_ENROLLMENT_STATUSES = (Enrollment.Status.PENDING, Enrollment.Status.CONFIRMED)


def _absolute_url(path):
    return f'{settings.SITE_URL.rstrip("/")}{path}'


def _email_student(enrollment, subject, message):
    email = enrollment.user.email
    if not email:
        return
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=True)


def _schedule_student_push(user, title, message, path):
    from news.notifications import send_push_notification

    transaction.on_commit(lambda: send_push_notification(title, message, path, recipient=user))


def _available_seat(formation):
    if formation.capacity is None:
        return True
    occupied = formation.enrollments.filter(status__in=ACTIVE_ENROLLMENT_STATUSES).count()
    return occupied < formation.capacity


def _promote_waitlisted_locked(formation):
    while _available_seat(formation):
        enrollment = (
            Enrollment.objects.select_for_update()
            .filter(formation=formation, status=Enrollment.Status.WAITLISTED)
            .order_by('created_at', 'pk')
            .first()
        )
        if enrollment is None:
            return
        enrollment.status = (
            Enrollment.Status.PENDING if formation.price > 0 else Enrollment.Status.CONFIRMED
        )
        enrollment.save(update_fields=['status', 'updated_at'])
        path = reverse('formations:student_dashboard')
        transaction.on_commit(lambda item=enrollment: _email_student(
            item,
            'Une place est disponible chez Dunia',
            f"Une place s'est libérée pour la formation « {item.formation.title} ». "
            f"Votre inscription est maintenant au statut : {item.get_status_display()}.\n\n"
            f"Consultez votre espace apprenant : {_absolute_url(path)}",
        ))
        _schedule_student_push(
            enrollment.user,
            'Une place est disponible chez Dunia',
            f"Une place s'est libérée pour « {formation.title} ». Votre inscription a été mise à jour.",
            path,
        )


def register_student(user, formation_id, phone):
    with transaction.atomic():
        formation = Formation.objects.select_for_update().get(pk=formation_id)
        enrollment = (
            Enrollment.objects.select_for_update()
            .filter(user=user, formation=formation)
            .first()
        )
        if enrollment and enrollment.status != Enrollment.Status.CANCELLED:
            raise ValidationError('Vous avez déjà une inscription pour cette formation.')

        status = (
            Enrollment.Status.WAITLISTED if not _available_seat(formation)
            else Enrollment.Status.PENDING if formation.price > 0
            else Enrollment.Status.CONFIRMED
        )
        if enrollment:
            enrollment.phone = phone
            enrollment.status = status
            enrollment.save(update_fields=['phone', 'status', 'updated_at'])
        else:
            enrollment = Enrollment.objects.create(
                user=user,
                formation=formation,
                phone=phone,
                status=status,
            )

        dashboard_url = _absolute_url(reverse('formations:student_dashboard'))
        transaction.on_commit(lambda item=enrollment: _email_student(
            item,
            f"Demande d'inscription — {item.formation.title}",
            f"Bonjour {item.user.get_full_name() or item.user.username},\n\n"
            f"Votre demande pour « {item.formation.title} » a été enregistrée. "
            f"Statut : {item.get_status_display()}.\n\n"
            f"Suivez votre inscription dans votre espace apprenant : {dashboard_url}\n\nDunia",
        ))
        _schedule_student_push(
            user,
            f"Inscription reçue — {formation.title}",
            f"Votre demande d'inscription est enregistrée. Statut : {enrollment.get_status_display()}.",
            reverse('formations:student_dashboard'),
        )
        return enrollment


def cancel_enrollment(enrollment_id, reviewed_by=None):
    with transaction.atomic():
        enrollment = Enrollment.objects.select_for_update().select_related('formation').get(pk=enrollment_id)
        formation = Formation.objects.select_for_update().get(pk=enrollment.formation_id)
        if enrollment.status in (Enrollment.Status.CANCELLED, Enrollment.Status.COMPLETED):
            return enrollment
        enrollment.status = Enrollment.Status.CANCELLED
        enrollment.save(update_fields=['status', 'updated_at'])
        Payment.objects.filter(
            enrollment=enrollment,
            status=Payment.Status.PENDING,
        ).update(status=Payment.Status.CANCELLED, reviewed_at=timezone.now(), reviewed_by=reviewed_by)
        _promote_waitlisted_locked(formation)
        return enrollment


def approve_payment(payment_id, reviewed_by):
    with transaction.atomic():
        payment = Payment.objects.select_for_update().select_related('enrollment__formation', 'enrollment__user').get(
            pk=payment_id
        )
        enrollment = Enrollment.objects.select_for_update().get(pk=payment.enrollment_id)
        if payment.status != Payment.Status.PENDING:
            raise ValidationError('Ce paiement a déjà été traité.')
        if enrollment.status != Enrollment.Status.PENDING:
            raise ValidationError("L'inscription n'est plus en attente de paiement.")

        payment.status = Payment.Status.APPROVED
        payment.reviewed_at = timezone.now()
        payment.reviewed_by = reviewed_by
        payment.save(update_fields=['status', 'reviewed_at', 'reviewed_by'])
        enrollment.status = Enrollment.Status.CONFIRMED
        enrollment.save(update_fields=['status', 'updated_at'])
        dashboard_url = _absolute_url(reverse('formations:student_dashboard'))
        transaction.on_commit(lambda item=enrollment: _email_student(
            item,
            f"Paiement confirmé — {item.formation.title}",
            f"Votre paiement pour « {item.formation.title} » a été vérifié. "
            f"Votre inscription est confirmée.\n\nAccéder à vos cours : {dashboard_url}\n\nDunia",
        ))
        _schedule_student_push(
            enrollment.user,
            f"Paiement confirmé — {enrollment.formation.title}",
            'Votre paiement a été vérifié. Votre inscription est confirmée et vos cours sont disponibles.',
            reverse('formations:student_dashboard'),
        )
        return payment


def reject_payment(payment_id, reviewed_by):
    with transaction.atomic():
        payment = Payment.objects.select_for_update().select_related('enrollment__formation').get(pk=payment_id)
        if payment.status != Payment.Status.PENDING:
            raise ValidationError('Ce paiement a déjà été traité.')
        payment.status = Payment.Status.REJECTED
        payment.reviewed_at = timezone.now()
        payment.reviewed_by = reviewed_by
        payment.save(update_fields=['status', 'reviewed_at', 'reviewed_by'])
        dashboard_url = _absolute_url(reverse('formations:student_dashboard'))
        transaction.on_commit(lambda item=payment.enrollment: _email_student(
            item,
            f"Vérification de paiement — {item.formation.title}",
            f"Nous n'avons pas pu confirmer le paiement déclaré pour « {item.formation.title} ». "
            "Vous pouvez soumettre une nouvelle référence ou contacter Dunia.\n\n"
            f"Votre espace apprenant : {dashboard_url}",
        ))
        _schedule_student_push(
            payment.enrollment.user,
            f"Paiement à vérifier — {payment.enrollment.formation.title}",
            'Votre preuve de paiement n’a pas pu être confirmée. Vous pouvez soumettre une nouvelle référence.',
            reverse('formations:student_dashboard'),
        )
        return payment


def complete_enrollment(enrollment_id):
    with transaction.atomic():
        enrollment = Enrollment.objects.select_for_update().get(pk=enrollment_id)
        if enrollment.status not in (Enrollment.Status.CONFIRMED, Enrollment.Status.COMPLETED):
            raise ValidationError('Seule une inscription confirmée peut être terminée.')
        enrollment.status = Enrollment.Status.COMPLETED
        enrollment.save(update_fields=['status', 'updated_at'])
        certificate, _ = Certificate.objects.get_or_create(enrollment=enrollment)
        dashboard_url = _absolute_url(reverse('formations:student_dashboard'))
        transaction.on_commit(lambda item=enrollment: _email_student(
            item,
            f"Votre attestation Dunia — {item.formation.title}",
            f"Félicitations ! Votre formation « {item.formation.title} » est terminée. "
            f"Votre attestation est disponible dans votre espace apprenant : {dashboard_url}\n\n"
            f"Numéro de vérification : {certificate.certificate_number}\n\nDunia",
        ))
        _schedule_student_push(
            enrollment.user,
            f"Attestation disponible — {enrollment.formation.title}",
            'Félicitations ! Votre attestation de réussite est disponible dans votre espace apprenant.',
            reverse('formations:student_dashboard'),
        )
        return certificate


def mark_lesson_completed(user, lesson_id):
    lesson = Lesson.objects.get(pk=lesson_id, is_published=True)
    with transaction.atomic():
        enrollment = Enrollment.objects.select_for_update().filter(
            user=user,
            formation=lesson.formation,
            status=Enrollment.Status.CONFIRMED,
        ).first()
        if enrollment is None:
            raise ValidationError('Une inscription confirmée est nécessaire pour valider cette leçon.')
        LessonProgress.objects.update_or_create(
            user=user,
            lesson=lesson,
            defaults={'completed': True, 'completed_at': timezone.now()},
        )
        total_lessons = Lesson.objects.filter(formation=lesson.formation, is_published=True).count()
        completed_lessons = LessonProgress.objects.filter(
            user=user,
            lesson__formation=lesson.formation,
            lesson__is_published=True,
            completed=True,
        ).count()
        if total_lessons and completed_lessons >= total_lessons:
            return complete_enrollment(enrollment.pk)
    return None