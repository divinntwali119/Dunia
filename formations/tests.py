from decimal import Decimal
import queue
import threading
from urllib.parse import urlparse

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core import mail
from django.db import connections
from django.test import TestCase, override_settings
from django.test import TransactionTestCase, skipUnlessDBFeature
from django.urls import reverse

from .models import Certificate, Enrollment, Formation, Lesson, LessonProgress, LessonResource, Payment
from .services import approve_payment, cancel_enrollment, mark_lesson_completed, reject_payment


@override_settings(DEBUG=True)
class FormationPagesTests(TestCase):
    def test_empty_catalog(self):
        response = self.client.get(reverse('formations:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Aucune formation trouvée')
        self.assertNotContains(response, 'id="formation-')

    def test_catalog_uses_database_fields_and_optional_images(self):
        first = Formation.objects.create(
            title='Design pratique', description='Apprendre les outils de design.',
            category=Formation.Category.DESIGN, duration='4 jours',
        )
        latest = Formation.objects.create(
            title='Python avancé', description='Construire une application.',
            category=Formation.Category.DEVELOPMENT, level=Formation.Level.ADVANCED,
            image='formation_images/python.png',
        )
        response = self.client.get(reverse('formations:list'))
        self.assertEqual(list(response.context['formations']), [latest, first])
        for text in [first.title, first.description, '4 jours', 'Avancé',
                     'data-category="design"', '/media/formation_images/python.png',
                     '/static/images/logo-dunia.png']:
            self.assertContains(response, text)

    def test_catalog_card_links_to_a_detailed_formation_page(self):
        formation = Formation.objects.create(title='Design & UI + UX #1', description='Atelier')
        response = self.client.get(reverse('formations:list'))
        self.assertContains(response, f'href="{reverse("formations:detail", args=[formation.pk])}"')
        detail = self.client.get(reverse('formations:detail', args=[formation.pk]))
        self.assertContains(detail, 'Design &amp; UI + UX #1')
        self.assertContains(detail, 'Créer un compte apprenant')

    def test_admin_can_create_a_formation_shown_in_catalog(self):
        self.assertTrue(admin.site.is_registered(Formation))
        user = get_user_model().objects.create_superuser('editor', 'editor@example.com', 'test-password')
        self.client.force_login(user)
        response = self.client.post(reverse('admin:formations_formation_add'), {
            'title': 'Nouvelle formation', 'description': 'Formation publiée depuis l’admin.',
            'category': Formation.Category.AI, 'duration': '2 jours',
            'level': Formation.Level.BEGINNER, '_save': 'Enregistrer',
            'delivery_mode': Formation.DeliveryMode.ONLINE,
            'price': '0.00',
            'currency': Formation.Currency.USD,
            'lessons-TOTAL_FORMS': '0',
            'lessons-INITIAL_FORMS': '0',
            'lessons-MIN_NUM_FORMS': '0',
            'lessons-MAX_NUM_FORMS': '1000',
        })
        self.assertEqual(response.status_code, 302)
        self.assertContains(self.client.get(reverse('formations:list')), 'Nouvelle formation')


@override_settings(DEBUG=True, EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class EnrollmentAndLearningTests(TestCase):
    def make_student(self, username):
        return get_user_model().objects.create_user(
            username=username,
            email=f'{username}@example.com',
            password='test-password-123',
            first_name=username.title(),
        )

    def request_enrollment(self, student, formation):
        self.client.force_login(student)
        return self.client.post(reverse('formations:enroll', args=[formation.pk]), {
            'phone': '+243 900 000 000',
            'consent': 'on',
        })

    def test_free_formation_confirms_registration_and_full_course_adds_waitlist(self):
        formation = Formation.objects.create(title='Atelier Python', description='Cours pratique', capacity=1)
        first = self.make_student('first')
        second = self.make_student('second')

        response = self.request_enrollment(first, formation)
        self.assertRedirects(response, reverse('formations:student_dashboard'))
        self.assertEqual(Enrollment.objects.get(user=first).status, Enrollment.Status.CONFIRMED)

        response = self.request_enrollment(second, formation)
        self.assertRedirects(response, reverse('formations:student_dashboard'))
        queued = Enrollment.objects.get(user=second)
        self.assertEqual(queued.status, Enrollment.Status.WAITLISTED)

        cancel_enrollment(Enrollment.objects.get(user=first).pk)
        queued.refresh_from_db()
        self.assertEqual(queued.status, Enrollment.Status.CONFIRMED)

    def test_paid_registration_records_mobile_money_and_admin_approval_confirms_it(self):
        formation = Formation.objects.create(
            title='Python Django', description='Construire un site.',
            price=Decimal('25.00'), currency=Formation.Currency.USD,
        )
        student = self.make_student('paid')
        response = self.request_enrollment(student, formation)
        self.assertRedirects(response, reverse('formations:student_dashboard'))
        enrollment = Enrollment.objects.get(user=student)
        self.assertEqual(enrollment.status, Enrollment.Status.PENDING)

        response = self.client.post(reverse('formations:payment', args=[enrollment.pk]), {
            'provider': Payment.Provider.MPESA,
            'transaction_reference': 'MPESA-TEST-001',
        })
        self.assertRedirects(response, reverse('formations:student_dashboard'))
        payment = Payment.objects.get(enrollment=enrollment)
        self.assertEqual(payment.amount, Decimal('25.00'))
        self.assertEqual(payment.status, Payment.Status.PENDING)

        reviewer = get_user_model().objects.create_superuser('reviewer', 'reviewer@example.com', 'test-password')
        approve_payment(payment.pk, reviewer)
        payment.refresh_from_db()
        enrollment.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.APPROVED)
        self.assertEqual(enrollment.status, Enrollment.Status.CONFIRMED)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_rejected_payment_keeps_enrollment_pending_and_allows_a_retry(self):
        formation = Formation.objects.create(
            title='Montage vidéo', description='Apprendre le montage.', price=Decimal('15.00'),
        )
        student = self.make_student('retry')
        enrollment = Enrollment.objects.create(
            user=student, formation=formation, phone='+243 900 000 000', status=Enrollment.Status.PENDING,
        )
        lesson = Lesson.objects.create(formation=formation, title='Premiers pas')
        payment = Payment.objects.create(
            enrollment=enrollment, amount=formation.price, currency=formation.currency,
            provider=Payment.Provider.MPESA, transaction_reference='MPESA-REJECT-001',
        )
        reviewer = get_user_model().objects.create_superuser('payment-reviewer', 'reviewer@example.com', 'test-password')

        reject_payment(payment.pk, reviewer)
        payment.refresh_from_db()
        enrollment.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.REJECTED)
        self.assertEqual(payment.reviewed_by, reviewer)
        self.assertIsNotNone(payment.reviewed_at)
        self.assertEqual(enrollment.status, Enrollment.Status.PENDING)

        self.client.force_login(student)
        self.assertEqual(self.client.get(reverse('formations:lesson', args=[lesson.pk])).status_code, 404)
        response = self.client.post(reverse('formations:payment', args=[enrollment.pk]), {
            'provider': Payment.Provider.MPESA,
            'transaction_reference': 'MPESA-RETRY-002',
        })
        self.assertRedirects(response, reverse('formations:student_dashboard'))
        self.assertTrue(enrollment.payments.filter(status=Payment.Status.PENDING).exists())

    def test_private_lesson_resources_are_only_downloadable_by_enrolled_students(self):
        student = self.make_student('resourceowner')
        other_student = self.make_student('resourceoutsider')
        formation = Formation.objects.create(title='Ressources privées', description='Supports de cours.')
        lesson = Lesson.objects.create(formation=formation, title='Support')
        resource = LessonResource.objects.create(lesson=lesson, title='Notes du cours')
        file_content = b'Contenu pedagogique prive.'
        resource.file.save('notes.txt', SimpleUploadedFile('notes.txt', file_content), save=True)
        self.addCleanup(resource.file.storage.delete, resource.file.name)
        enrollment = Enrollment.objects.create(
            user=student, formation=formation, phone='+243 900 000 000', status=Enrollment.Status.CONFIRMED,
        )
        private_url = reverse('formations:private_media', kwargs={'file_path': resource.file.name})
        resource_url = reverse('formations:resource_download', args=[resource.pk])

        self.client.force_login(other_student)
        self.assertEqual(self.client.get(private_url).status_code, 404)
        self.assertEqual(self.client.get(resource_url).status_code, 404)

        self.client.force_login(student)
        private_response = self.client.get(private_url)
        self.assertEqual(private_response.status_code, 200)
        self.assertEqual(b''.join(private_response.streaming_content), file_content)
        resource_response = self.client.get(resource_url)
        self.assertEqual(resource_response.status_code, 200)
        self.assertEqual(b''.join(resource_response.streaming_content), file_content)

    def test_learner_progress_creates_and_verifies_certificate(self):
        student = self.make_student('learner')
        other_student = self.make_student('other')
        formation = Formation.objects.create(title='Web', description='HTML et CSS')
        enrollment = Enrollment.objects.create(
            user=student, formation=formation, phone='+243 900 000 000', status=Enrollment.Status.CONFIRMED,
        )
        first = Lesson.objects.create(formation=formation, title='HTML', order=1)
        second = Lesson.objects.create(formation=formation, title='CSS', order=2)

        self.client.force_login(other_student)
        self.assertEqual(self.client.get(reverse('formations:lesson', args=[first.pk])).status_code, 404)

        certificate = mark_lesson_completed(student, first.pk)
        self.assertIsNone(certificate)
        self.assertEqual(enrollment.progress_percent, 50)
        certificate = mark_lesson_completed(student, second.pk)
        self.assertIsInstance(certificate, Certificate)
        enrollment.refresh_from_db()
        self.assertEqual(enrollment.status, Enrollment.Status.COMPLETED)

        response = self.client.get(reverse('formations:certificate', args=[certificate.certificate_number]))
        self.assertContains(response, 'Attestation de réussite')
        self.assertContains(response, student.get_full_name())
        self.assertEqual(LessonProgress.objects.filter(user=student, completed=True).count(), 2)

    def test_dashboard_requires_login_and_signup_creates_authenticated_account(self):
        response = self.client.get(reverse('formations:student_dashboard'))
        self.assertRedirects(response, f"{reverse('formations:login')}?next={reverse('formations:student_dashboard')}")

        response = self.client.post(reverse('formations:signup'), {
            'username': 'newstudent',
            'first_name': 'Amina',
            'last_name': 'Learner',
            'email': 'amina@example.com',
            'password1': 'A-strong-test-pass-327!',
            'password2': 'A-strong-test-pass-327!',
        })
        self.assertRedirects(response, reverse('formations:student_dashboard'))
        self.assertTrue(get_user_model().objects.filter(username='newstudent').exists())
        self.assertTrue(self.client.session.get('_auth_user_id'))


@override_settings(DEBUG=True, EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class PasswordResetTests(TestCase):
    def test_reset_email_link_allows_the_user_to_set_a_new_password(self):
        user = get_user_model().objects.create_user(
            username='resetstudent',
            email='resetstudent@example.com',
            password='Old-test-password-327!',
        )
        reset_url = reverse('formations:password_reset')

        response = self.client.get(reset_url)
        self.assertContains(response, 'Réinitialiser le mot de passe')
        self.assertContains(response, 'name="email"')

        response = self.client.post(reset_url, {'email': user.email})
        self.assertRedirects(response, reverse('formations:password_reset_done'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Réinitialisation du mot de passe Dunia')

        reset_link = next(
            line.strip()
            for line in mail.outbox[0].body.splitlines()
            if '/formations/reinitialiser/' in line
        )
        response = self.client.get(urlparse(reset_link).path)
        self.assertEqual(response.status_code, 302)
        confirm_url = response.url
        response = self.client.get(confirm_url)
        self.assertContains(response, 'Choisir un nouveau mot de passe')

        new_password = 'New-test-password-for-Dunia-327!'
        response = self.client.post(confirm_url, {
            'new_password1': new_password,
            'new_password2': new_password,
        })
        self.assertRedirects(response, reverse('formations:password_reset_complete'))
        user.refresh_from_db()
        self.assertTrue(user.check_password(new_password))

    def test_reset_response_does_not_reveal_unknown_email_addresses(self):
        response = self.client.post(reverse('formations:password_reset'), {
            'email': 'unknown@example.com',
        })

        self.assertRedirects(response, reverse('formations:password_reset_done'))
        self.assertEqual(len(mail.outbox), 0)
        self.assertContains(self.client.get(reverse('formations:password_reset_done')),
                            'Si un compte correspond à cette adresse')


@skipUnlessDBFeature('has_select_for_update')
class ConcurrentEnrollmentCapacityTests(TransactionTestCase):
    def test_concurrent_registrations_do_not_exceed_formation_capacity(self):
        formation = Formation.objects.create(title='Atelier concurrent', description='Places limitées.', capacity=1)
        users = [
            get_user_model().objects.create_user(f'parallel-{index}', password='test-password-123')
            for index in range(2)
        ]
        barrier = threading.Barrier(3)
        outcomes = queue.Queue()

        def register(user_id):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                user = get_user_model().objects.get(pk=user_id)
                enrollment = register_student(user, formation.pk, '+243 900 000 000')
                outcomes.put(enrollment.status)
            except Exception as error:
                outcomes.put(error)
            finally:
                close_old_connections()

        threads = [
            threading.Thread(target=register, args=(user.pk,), daemon=True)
            for user in users
        ]
        for thread in threads:
            thread.start()
        barrier.wait(timeout=10)
        for thread in threads:
            thread.join(timeout=15)

        self.assertFalse(any(thread.is_alive() for thread in threads), 'Une inscription concurrente est restée bloquée.')
        results = [outcomes.get(timeout=1) for _ in threads]
        errors = [result for result in results if isinstance(result, Exception)]
        self.assertEqual(errors, [])
        self.assertCountEqual(results, [Enrollment.Status.CONFIRMED, Enrollment.Status.WAITLISTED])
        self.assertEqual(
            Enrollment.objects.filter(
                formation=formation,
                status__in=(Enrollment.Status.PENDING, Enrollment.Status.CONFIRMED),
            ).count(),
            1,
        )
