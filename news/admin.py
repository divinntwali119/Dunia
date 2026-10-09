from django.contrib import admin, messages
from unfold.admin import ModelAdmin

from .models import News, NewsletterSubscriber, PushNotification, PushSubscription
from .notifications import deliver_push_notification


@admin.register(News)
class NewsAdmin(ModelAdmin):
    list_display = ('title', 'category', 'published_date')
    search_fields = ('title', 'description')
    list_filter = ('category', 'published_date')


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(ModelAdmin):
    list_display = ('email', 'is_active', 'is_confirmed', 'consented_at', 'confirmed_at', 'unsubscribed_at')
    list_filter = ('is_active', 'is_confirmed', 'consented_at')
    search_fields = ('email',)
    readonly_fields = ('token', 'consented_at', 'confirmed_at', 'unsubscribed_at')


@admin.register(PushSubscription)
class PushSubscriptionAdmin(ModelAdmin):
    list_display = ('id', 'user', 'is_active', 'user_agent', 'updated_at')
    list_filter = ('is_active', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email', 'endpoint')
    readonly_fields = ('endpoint', 'p256dh', 'auth', 'user_agent', 'created_at', 'updated_at')
    actions = ('deactivate_selected',)

    @admin.action(description='Désactiver les abonnements sélectionnés')
    def deactivate_selected(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} appareil(s) désactivé(s).', messages.SUCCESS)


@admin.register(PushNotification)
class PushNotificationAdmin(ModelAdmin):
    list_display = ('title', 'recipient', 'sent_at', 'delivered_count', 'failed_count', 'created_at')
    list_filter = ('sent_at', 'created_at')
    search_fields = ('title', 'body', 'recipient__username', 'recipient__email')
    readonly_fields = ('created_by', 'created_at', 'sent_at', 'delivered_count', 'failed_count')
    autocomplete_fields = ('recipient',)
    actions = ('send_selected_notifications',)

    @admin.action(description='Envoyer les notifications non envoyées sur les appareils')
    def send_selected_notifications(self, request, queryset):
        delivered = 0
        failed = 0
        pending = list(queryset.filter(sent_at__isnull=True).values_list('pk', flat=True))
        for notification_id in pending:
            result = deliver_push_notification(notification_id)
            if result['sent']:
                delivered += result['delivered']
                failed += result['failed']
        self.message_user(
            request,
            f'{len(pending)} campagne(s) traitée(s) : {delivered} envoi(s) accepté(s), {failed} échec(s).',
            messages.SUCCESS if pending else messages.INFO,
        )

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
