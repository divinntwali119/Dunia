(() => {
    const panel = document.getElementById('pushSettings');
    if (!panel) return;

    const status = document.getElementById('pushStatus');
    const enableButton = document.getElementById('pushEnableButton');
    const disableButton = document.getElementById('pushDisableButton');
    const publicKey = panel.dataset.publicKey || '';
    const csrfToken = document.querySelector('[name="csrfmiddlewaretoken"]')?.value || '';
    let removedLegacySubscription = false;

    function showStatus(message, isError = false) {
        if (!status) return;
        status.textContent = message;
        status.classList.toggle('border-red-200', isError);
        status.classList.toggle('bg-red-50', isError);
        status.classList.toggle('text-red-800', isError);
        status.classList.toggle('border-slate-200', !isError);
        status.classList.toggle('bg-white', !isError);
        status.classList.toggle('text-slate-600', !isError);
    }

    function setSubscribed(isSubscribed) {
        enableButton?.classList.toggle('hidden', isSubscribed);
        disableButton?.classList.toggle('hidden', !isSubscribed);
    }

    function decodeApplicationServerKey(encodedKey) {
        const padding = '='.repeat((4 - (encodedKey.length % 4)) % 4);
        const base64 = (encodedKey + padding).replace(/-/g, '+').replace(/_/g, '/');
        const raw = window.atob(base64);
        return Uint8Array.from(raw, (character) => character.charCodeAt(0));
    }

    function usesCurrentApplicationServerKey(subscription) {
        const currentKey = subscription.options?.applicationServerKey;
        if (!currentKey) return false;
        const actualKey = new Uint8Array(currentKey);
        const expectedKey = decodeApplicationServerKey(publicKey);
        return actualKey.length === expectedKey.length
            && actualKey.every((byte, index) => byte === expectedKey[index]);
    }

    function getCsrfToken() {
        if (csrfToken) return csrfToken;
        const cookie = document.cookie.split('; ').find((item) => item.startsWith('csrftoken='));
        return cookie ? decodeURIComponent(cookie.split('=').slice(1).join('=')) : '';
    }

    async function sendToBackend(url, payload) {
        const response = await fetch(url, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken(),
            },
            body: JSON.stringify(payload),
        });
        const result = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(result.error || 'Le serveur n’a pas accepté cette demande.');
        return result;
    }

    async function currentSubscription() {
        const registration = await navigator.serviceWorker.ready;
        const subscription = await registration.pushManager.getSubscription();
        if (subscription && !usesCurrentApplicationServerKey(subscription)) {
            await sendToBackend('/news/push/unsubscribe/', { endpoint: subscription.endpoint });
            await subscription.unsubscribe();
            removedLegacySubscription = true;
            return null;
        }
        return subscription;
    }

    async function synchronizeExistingSubscription() {
        const subscription = await currentSubscription();
        setSubscribed(Boolean(subscription));
        if (subscription) {
            await sendToBackend('/news/push/subscribe/', subscription.toJSON());
            showStatus('Les notifications sont actives sur cet appareil.');
        } else if (removedLegacySubscription) {
            showStatus('L’ancien abonnement a été retiré. Cliquez sur « Activer » pour utiliser les notifications Dunia.');
        } else if (Notification.permission === 'denied') {
            showStatus('Les notifications sont bloquées dans les réglages de ce navigateur.', true);
        } else {
            showStatus('Les notifications sont désactivées sur cet appareil.');
        }
    }

    async function enableNotifications() {
        if (!('Notification' in window) || !('serviceWorker' in navigator) || !('PushManager' in window)) {
            showStatus('Ce navigateur ne prend pas en charge les notifications Web Push.', true);
            return;
        }
        const isAppleMobile = /iphone|ipad|ipod/i.test(navigator.userAgent)
            || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
        const isInstalled = navigator.standalone === true || window.matchMedia('(display-mode: standalone)').matches;
        if (isAppleMobile && !isInstalled) {
            showStatus('Sur iPhone/iPad, ajoutez d’abord Dunia à l’écran d’accueil et ouvrez l’application installée.', true);
            return;
        }
        if (Notification.permission === 'denied') {
            showStatus('Les notifications sont bloquées. Autorisez-les dans les réglages du navigateur, puis réessayez.', true);
            return;
        }

        enableButton.disabled = true;
        enableButton.classList.add('opacity-60');
        try {
            const permission = Notification.permission === 'granted'
                ? 'granted'
                : await Notification.requestPermission();
            if (permission !== 'granted') {
                showStatus('L’autorisation de notifications n’a pas été accordée.', true);
                return;
            }

            const registration = await navigator.serviceWorker.ready;
            let subscription = await currentSubscription();
            if (!subscription) {
                subscription = await registration.pushManager.subscribe({
                    userVisibleOnly: true,
                    applicationServerKey: decodeApplicationServerKey(publicKey),
                });
            }
            await sendToBackend('/news/push/subscribe/', subscription.toJSON());
            setSubscribed(true);
            showStatus('C’est activé ! Cet appareil recevra les notifications Dunia.');
        } catch (error) {
            showStatus(error.message || 'Impossible d’activer les notifications. Vérifiez la connexion et réessayez.', true);
        } finally {
            enableButton.disabled = false;
            enableButton.classList.remove('opacity-60');
        }
    }

    async function disableNotifications() {
        disableButton.disabled = true;
        try {
            const subscription = await currentSubscription();
            if (subscription) {
                await sendToBackend('/news/push/unsubscribe/', { endpoint: subscription.endpoint });
                await subscription.unsubscribe();
            }
            setSubscribed(false);
            showStatus('Les notifications sont désactivées sur cet appareil.');
        } catch (error) {
            showStatus(error.message || 'Impossible de désactiver les notifications.', true);
        } finally {
            disableButton.disabled = false;
        }
    }

    if (panel.dataset.enabled !== 'true' || !publicKey) {
        setSubscribed(false);
        return;
    }
    if (!('Notification' in window) || !('serviceWorker' in navigator) || !('PushManager' in window)) {
        showStatus('Ce navigateur ne prend pas en charge les notifications Web Push.', true);
        if (enableButton) enableButton.disabled = true;
        return;
    }

    enableButton?.addEventListener('click', enableNotifications);
    disableButton?.addEventListener('click', disableNotifications);
    synchronizeExistingSubscription().catch((error) => {
        showStatus(error.message || 'Impossible de vérifier l’abonnement sur cet appareil.', true);
    });
})();
