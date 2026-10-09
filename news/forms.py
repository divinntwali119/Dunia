from django import forms


class NewsletterSubscribeForm(forms.Form):
    email = forms.EmailField(label='Adresse e-mail')
    consent = forms.BooleanField(
        label="J'accepte de recevoir par e-mail les actualités et nouvelles formations de Dunia.",
    )