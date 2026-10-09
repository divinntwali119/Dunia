from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import IntegrityError
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone
from django.views.decorators.http import require_POST, require_http_methods

from .forms import EnrollmentForm, PaymentForm, StudentSignUpForm
from .models import Certificate, Enrollment, Formation, Lesson, LessonProgress, LessonResource, Payment
from .services import mark_lesson_completed, register_student


class StudentLoginView(LoginView):
    template_name = 'formations/login.html'
    authentication_form = AuthenticationForm
    redirect_authenticated_user = True


def formations(request):
    return render(request, 'formations/formations.html', {
        'formations': Formation.objects.all(),
    })


def formation_detail(request, pk):
    formation = get_object_or_404(
        Formation.objects.prefetch_related('lessons'),
        pk=pk,
    )
    occupied_seats = formation.enrollments.filter(
        status__in=(Enrollment.Status.PENDING, Enrollment.Status.CONFIRMED)
    ).count()
    return render(request, 'formations/detail.html', {
        'formation': formation,
        'occupied_seats': occupied_seats,
        'available_seats': max(formation.capacity - occupied_seats, 0) if formation.capacity is not None else None,
        'lessons': formation.lessons.filter(is_published=True),
        'existing_enrollment': (
            Enrollment.objects.filter(user=request.user, formation=formation)
            .exclude(status=Enrollment.Status.CANCELLED).first()
            if request.user.is_authenticated else None
        ),
    })


@require_http_methods(['GET', 'POST'])
def student_signup(request):
    if request.user.is_authenticated:
        return redirect('formations:student_dashboard')
    next_url = request.POST.get('next') or request.GET.get('next', '')
    if not url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        next_url = ''
    form = StudentSignUpForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Votre espace apprenant est créé. Vous pouvez maintenant vous inscrire aux formations.')
        if user.email:
            try:
                send_mail(
                    'Bienvenue sur Dunia',
                    f"Bonjour {user.get_full_name() or user.username},\n\n"
                    "Votre compte apprenant Dunia est prêt. Consultez les formations, suivez vos cours et votre progression.\n\n"
                    f"{settings.SITE_URL.rstrip('/')}{reverse('formations:student_dashboard')}\n\nDunia",
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=True,
                )
            except Exception:
                pass
        return redirect(next_url or 'formations:student_dashboard')
    return render(request, 'formations/signup.html', {'form': form, 'next': next_url})


@login_required
def student_dashboard(request):
    enrollments = (
        Enrollment.objects.filter(user=request.user)
        .select_related('formation', 'certificate')
        .prefetch_related('payments')
    )
    return render(request, 'formations/dashboard.html', {'enrollments': enrollments})


@login_required
@require_http_methods(['GET', 'POST'])
def enroll(request, formation_id):
    formation = get_object_or_404(Formation, pk=formation_id)
    existing = Enrollment.objects.filter(user=request.user, formation=formation).exclude(
        status=Enrollment.Status.CANCELLED
    ).first()
    if existing:
        messages.info(request, f"Votre inscription existe déjà : {existing.get_status_display()}.")
        return redirect('formations:student_dashboard')

    form = EnrollmentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            enrollment = register_student(request.user, formation.pk, form.cleaned_data['phone'])
        except ValidationError as error:
            form.add_error(None, error.messages[0])
        except IntegrityError:
            form.add_error(None, 'Une inscription existe déjà pour cette formation.')
        else:
            if enrollment.status == Enrollment.Status.WAITLISTED:
                messages.info(request, "La formation est complète. Votre demande a été ajoutée à la liste d'attente.")
            elif enrollment.status == Enrollment.Status.PENDING:
                messages.success(request, 'Demande enregistrée. Soumettez votre référence Mobile Money pour validation.')
            else:
                messages.success(request, 'Votre inscription gratuite est confirmée. Bienvenue chez Dunia !')
            return redirect('formations:student_dashboard')
    return render(request, 'formations/enroll.html', {'formation': formation, 'form': form})


@login_required
@require_http_methods(['GET', 'POST'])
def submit_payment(request, enrollment_id):
    enrollment = get_object_or_404(
        Enrollment.objects.select_related('formation'),
        pk=enrollment_id,
        user=request.user,
    )
    if enrollment.formation.price <= 0 or enrollment.status != Enrollment.Status.PENDING:
        messages.error(request, 'Aucun paiement ne peut être soumis pour cette inscription.')
        return redirect('formations:student_dashboard')

    has_pending_payment = enrollment.payments.filter(status=Payment.Status.PENDING).exists()
    if has_pending_payment:
        messages.info(request, 'Votre preuve de paiement est déjà soumise et attend une vérification.')

    form = PaymentForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and not has_pending_payment and form.is_valid():
        payment = form.save(commit=False)
        payment.enrollment = enrollment
        payment.amount = enrollment.formation.price
        payment.currency = enrollment.formation.currency
        try:
            payment.save()
        except IntegrityError:
            form.add_error('transaction_reference', 'Cette référence a déjà été utilisée.')
        else:
            messages.success(request, 'Référence reçue. Votre inscription sera confirmée après vérification manuelle.')
            return redirect('formations:student_dashboard')
    return render(request, 'formations/payment.html', {
        'enrollment': enrollment,
        'form': form,
        'has_pending_payment': has_pending_payment,
        'mobile_money_instructions': settings.MOBILE_MONEY_INSTRUCTIONS,
    })


@login_required
def lesson_detail(request, lesson_id):
    lesson = get_object_or_404(Lesson.objects.select_related('formation'), pk=lesson_id, is_published=True)
    enrollment = get_object_or_404(
        Enrollment.objects.select_related('formation'),
        user=request.user,
        formation=lesson.formation,
        status__in=(Enrollment.Status.CONFIRMED, Enrollment.Status.COMPLETED),
    )
    progress = LessonProgress.objects.filter(user=request.user, lesson=lesson).first()
    lessons = list(lesson.formation.lessons.filter(is_published=True))
    completed_ids = set(LessonProgress.objects.filter(
        user=request.user,
        lesson__in=lessons,
        completed=True,
    ).values_list('lesson_id', flat=True))
    return render(request, 'formations/lesson.html', {
        'lesson': lesson,
        'enrollment': enrollment,
        'lessons': lessons,
        'completed_ids': completed_ids,
        'is_completed': bool(progress and progress.completed),
    })


@login_required
@require_POST
def complete_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, pk=lesson_id, is_published=True)
    try:
        certificate = mark_lesson_completed(request.user, lesson.pk)
    except (Lesson.DoesNotExist, ValidationError) as error:
        message = error.messages[0] if isinstance(error, ValidationError) else 'Cette leçon est indisponible.'
        messages.error(request, message)
    else:
        messages.success(
            request,
            'Félicitations, votre attestation est disponible !' if certificate else 'Leçon marquée comme terminée.',
        )
    return redirect('formations:lesson', lesson_id=lesson.pk)


@login_required
def download_resource(request, resource_id):
    resource = get_object_or_404(
        LessonResource.objects.select_related('lesson__formation'),
        pk=resource_id,
    )
    allowed = Enrollment.objects.filter(
        user=request.user,
        formation=resource.lesson.formation,
        status__in=(Enrollment.Status.CONFIRMED, Enrollment.Status.COMPLETED),
    ).exists()
    if not allowed:
        raise Http404
    if not resource.file:
        raise Http404
    try:
        file_object = resource.file.open('rb')
    except (FileNotFoundError, OSError):
        raise Http404
    return FileResponse(file_object, as_attachment=True, filename=Path(resource.file.name).name)


@login_required
def download_private_file(request, file_path):
    resource = LessonResource.objects.select_related('lesson__formation').filter(file=file_path).first()
    if resource:
        allowed = request.user.is_staff or Enrollment.objects.filter(
            user=request.user,
            formation=resource.lesson.formation,
            status__in=(Enrollment.Status.CONFIRMED, Enrollment.Status.COMPLETED),
        ).exists()
        private_file = resource.file
    else:
        payment = Payment.objects.select_related('enrollment').filter(proof=file_path).first()
        if not payment:
            raise Http404
        allowed = request.user.is_staff or payment.enrollment.user_id == request.user.pk
        private_file = payment.proof
    if not allowed or not private_file:
        raise Http404
    try:
        file_object = private_file.open('rb')
    except (FileNotFoundError, OSError):
        raise Http404
    return FileResponse(file_object, as_attachment=True, filename=Path(private_file.name).name)


def verify_certificate(request, certificate_number):
    certificate = get_object_or_404(
        Certificate.objects.select_related('enrollment__user', 'enrollment__formation'),
        certificate_number=certificate_number,
    )
    return render(request, 'formations/certificate.html', {'certificate': certificate})
