from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import RegexValidator

from .models import Payment


class StudentSignUpForm(UserCreationForm):
    email = forms.EmailField(label='Adresse e-mail')

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ('username', 'first_name', 'last_name', 'email')
        labels = {
            'username': "Nom d'utilisateur",
            'first_name': 'Prénom',
            'last_name': 'Nom',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault(
                'class',
                'w-full rounded-xl border border-slate-300 px-4 py-3 text-sm text-slate-900 '
                'focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100',
            )

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if get_user_model().objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Un compte utilise déjà cette adresse e-mail.')
        return email


class EnrollmentForm(forms.Form):
    phone = forms.CharField(
        label='Téléphone / WhatsApp',
        max_length=32,
        validators=[RegexValidator(r'^\+?[0-9\s().-]{7,32}$', 'Entrez un numéro de téléphone valide.')],
        widget=forms.TextInput(attrs={'autocomplete': 'tel', 'placeholder': '+243 ...'}),
    )
    consent = forms.BooleanField(
        label="J'accepte d'être contacté au sujet de cette inscription et confirme l'exactitude de mes informations.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault(
                'class',
                'rounded-xl border border-slate-300 px-4 py-3 text-sm text-slate-900 '
                'focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100',
            )


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ('provider', 'transaction_reference', 'proof')
        labels = {
            'provider': 'Opérateur Mobile Money',
            'transaction_reference': 'Référence de transaction',
            'proof': 'Capture ou reçu (facultatif)',
        }
        widgets = {
            'transaction_reference': forms.TextInput(attrs={'autocomplete': 'off'}),
        }

    def clean_transaction_reference(self):
        reference = self.cleaned_data['transaction_reference'].strip()
        if Payment.objects.filter(transaction_reference__iexact=reference).exists():
            raise forms.ValidationError('Cette référence de transaction a déjà été soumise.')
        return reference

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault(
                'class',
                'w-full rounded-xl border border-slate-300 px-4 py-3 text-sm text-slate-900 '
                'focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100',
            )