from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from unfold.admin import ModelAdmin
from .models import (
    Certificate,
    Enrollment,
    Formation,
    Lesson,
    LessonProgress,
    LessonResource,
    Payment,
)
from .services import cancel_enrollment, complete_enrollment, approve_payment, reject_payment


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0
    fields = ('order', 'title', 'summary', 'video_url', 'is_published')
    show_change_link = True


class LessonResourceInline(admin.TabularInline):
    model = LessonResource
    extra = 0


@admin.register(Formation)
class FormationAdmin(ModelAdmin):
    list_display = ('title', 'category', 'duration', 'level', 'delivery_mode', 'price', 'capacity', 'created_at')
    list_filter = ('category', 'level', 'created_at')
    search_fields = ('title', 'description', 'instructor')
    inlines = (LessonInline,)


@admin.register(Lesson)
class LessonAdmin(ModelAdmin):
    list_display = ('title', 'formation', 'order', 'is_published')
    list_filter = ('is_published', 'formation')
    search_fields = ('title', 'summary', 'content', 'formation__title')
    inlines = (LessonResourceInline,)


@admin.register(Enrollment)
class EnrollmentAdmin(ModelAdmin):
    list_display = ('student', 'formation', 'status', 'phone', 'created_at')
    list_filter = ('status', 'formation', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'user__email', 'phone', 'formation__title')
    readonly_fields = ('created_at', 'updated_at')
    actions = ('cancel_selected', 'complete_selected')

    @admin.display(description='apprenant')
    def student(self, obj):
        return obj.user.get_full_name() or obj.user.username

    @admin.action(description='Annuler et libérer les places sélectionnées')
    def cancel_selected(self, request, queryset):
        count = 0
        for enrollment in queryset:
            cancel_enrollment(enrollment.pk, reviewed_by=request.user)
            count += 1
        self.message_user(request, f'{count} inscription(s) annulée(s). Les places disponibles ont été proposées aux personnes en attente.')

    @admin.action(description='Terminer les formations sélectionnées et délivrer les attestations')
    def complete_selected(self, request, queryset):
        completed = 0
        for enrollment in queryset:
            try:
                complete_enrollment(enrollment.pk)
            except ValidationError:
                continue
            completed += 1
        self.message_user(request, f'{completed} attestation(s) délivrée(s).', level=messages.SUCCESS)


@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
    list_display = ('transaction_reference', 'student', 'formation', 'amount', 'currency', 'provider', 'status', 'created_at')
    list_filter = ('status', 'provider', 'currency', 'created_at')
    search_fields = ('transaction_reference', 'enrollment__user__email', 'enrollment__user__username', 'enrollment__formation__title')
    readonly_fields = ('enrollment', 'amount', 'currency', 'provider', 'transaction_reference', 'proof', 'status', 'created_at', 'reviewed_at', 'reviewed_by')
    actions = ('approve_selected', 'reject_selected')

    @admin.display(description='apprenant')
    def student(self, obj):
        return obj.enrollment.user.get_full_name() or obj.enrollment.user.username

    @admin.display(description='formation')
    def formation(self, obj):
        return obj.enrollment.formation

    @admin.action(description='Valider les paiements sélectionnés')
    def approve_selected(self, request, queryset):
        approved = 0
        for payment in queryset:
            try:
                approve_payment(payment.pk, request.user)
            except ValidationError:
                continue
            approved += 1
        self.message_user(request, f'{approved} paiement(s) validé(s). Les inscriptions correspondantes sont confirmées.')

    @admin.action(description='Rejeter les paiements sélectionnés')
    def reject_selected(self, request, queryset):
        rejected = 0
        for payment in queryset:
            try:
                reject_payment(payment.pk, request.user)
            except ValidationError:
                continue
            rejected += 1
        self.message_user(request, f'{rejected} paiement(s) rejeté(s).')


@admin.register(LessonResource)
class LessonResourceAdmin(ModelAdmin):
    list_display = ('title', 'lesson')
    search_fields = ('title', 'lesson__title', 'lesson__formation__title')


@admin.register(LessonProgress)
class LessonProgressAdmin(ModelAdmin):
    list_display = ('user', 'lesson', 'completed', 'completed_at')
    list_filter = ('completed', 'lesson__formation')
    search_fields = ('user__username', 'user__email', 'lesson__title')


@admin.register(Certificate)
class CertificateAdmin(ModelAdmin):
    list_display = ('certificate_number', 'student', 'formation', 'issued_at')
    search_fields = ('certificate_number', 'enrollment__user__email', 'enrollment__user__username', 'enrollment__formation__title')
    readonly_fields = ('enrollment', 'certificate_number', 'issued_at')

    @admin.display(description='apprenant')
    def student(self, obj):
        return obj.enrollment.user.get_full_name() or obj.enrollment.user.username

    @admin.display(description='formation')
    def formation(self, obj):
        return obj.enrollment.formation
