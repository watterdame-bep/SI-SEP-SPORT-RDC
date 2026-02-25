"""
Formulaires pour l'initialisation du système (Super Admin).
Ministère (institution mère) + trois comptes clés avec mots de passe temporaires générés.
"""
from django import forms
from django.contrib.auth import get_user_model

from gouvernance.models import ProvAdmin

User = get_user_model()


class MinistereSetupForm(forms.Form):
    """Formulaire institution : Ministère des Sports (nom, sigle, logo, adresse, contact)."""
    nom_officiel = forms.CharField(
        max_length=255,
        label='Nom officiel',
        initial='Ministère des Sports et Loisirs',
        widget=forms.TextInput(attrs={'placeholder': 'Ex. Ministère des Sports et Loisirs'}),
    )
    sigle = forms.CharField(
        max_length=50,
        label='Sigle',
        required=False,
        initial='MSL',
        widget=forms.TextInput(attrs={'placeholder': 'Ex. MSL'}),
    )
    logo = forms.ImageField(
        label='Logo',
        required=False,
        help_text='Logo de l\'institution (optionnel).',
    )
    adresse = forms.CharField(
        max_length=500,
        label='Adresse',
        required=False,
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Adresse physique du ministère'}),
    )
    email_officiel = forms.EmailField(
        label='Contact (e-mail officiel)',
        required=False,
        widget=forms.EmailInput(attrs={'placeholder': 'contact@min sports.gouv.cd'}),
    )
    telephone_off = forms.CharField(
        max_length=50,
        label='Téléphone officiel',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': '+243 ...'}),
    )


class CompteCleForm(forms.Form):
    """Un compte clé : nom complet et email (mot de passe généré côté vue)."""
    nom = forms.CharField(max_length=255, label='Nom complet', widget=forms.TextInput(attrs={'placeholder': 'Nom et prénom'}))
    email = forms.EmailField(label='E-mail', widget=forms.EmailInput(attrs={'placeholder': 'email@exemple.cd'}))


class SetupInitialForm(forms.Form):
    """
    Agrège : Ministère + Ministre + Secrétaire Général.
    Validation par e-mail : chaque compte reçoit un lien pour activer et définir son mot de passe.
    """
    # Ministère
    nom_officiel = forms.CharField(max_length=255, label='Nom officiel', initial='Ministère des Sports et Loisirs')
    sigle = forms.CharField(max_length=50, label='Sigle', required=False, initial='MSL')
    logo = forms.ImageField(label='Logo', required=False)
    adresse = forms.CharField(max_length=500, label='Adresse', required=False, widget=forms.Textarea(attrs={'rows': 2}))
    email_officiel = forms.EmailField(label='E-mail officiel', required=False)
    telephone_off = forms.CharField(max_length=50, label='Téléphone officiel', required=False)

    # Ministre
    ministre_nom = forms.CharField(max_length=255, label='Ministre — Nom')
    ministre_email = forms.EmailField(label='Ministre — E-mail')

    # Secrétaire Général (gestionnaire de données)
    sg_nom = forms.CharField(max_length=255, label='Secrétaire Général — Nom')
    sg_email = forms.EmailField(label='Secrétaire Général — E-mail')
    sg_gestionnaire_donnees = forms.BooleanField(
        initial=True,
        required=False,
        label='Activer les droits de gestionnaire de données (Secrétaire Général)',
    )


class FederationRegistrationForm(forms.Form):
    """
    Formulaire F03 — Enregistrement d'une Fédération (catalogue SI-SEP).
    Soumis par le Secrétaire Général ; l'institution est créée en ATTENTE_SIGNATURE.
    """
    nom_officiel = forms.CharField(
        max_length=255,
        label='Nom officiel de la fédération',
        widget=forms.TextInput(attrs={'placeholder': 'Ex. Fédération Congolaise de Football'}),
    )
    sigle = forms.CharField(
        max_length=50,
        label='Sigle',
        widget=forms.TextInput(attrs={'placeholder': 'Ex. FECFOOT'}),
    )
    discipline_sportive = forms.CharField(
        max_length=255,
        label='Discipline sportive',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Ex. Football'}),
    )
    siege = forms.CharField(
        max_length=500,
        label='Siège / Adresse',
        required=False,
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Adresse du siège'}),
    )
    email_officiel = forms.EmailField(
        label='E-mail officiel',
        required=False,
        widget=forms.EmailInput(attrs={'placeholder': 'contact@federation.cd'}),
    )
    telephone_off = forms.CharField(
        max_length=50,
        label='Téléphone officiel',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': '+243 ...'}),
    )
    date_creation = forms.DateField(
        label='Date de création',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    statut_juridique = forms.CharField(
        max_length=100,
        label='Statut juridique',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Ex. ASBL'}),
    )


TYPE_ENTITE_CHOICES = [
    ('DIRECTEUR_CABINET', 'Directeur de Cabinet'),
    ('DIRECTEUR_PROVINCIAL', 'Direction provinciale'),
    ('INSPECTEUR_GENERAL', 'Inspection générale'),
]


class CreerCompteEntiteForm(forms.Form):
    """
    Création d'un compte pour une entité du ministère (Directeur de Cabinet,
    Direction provinciale, Inspection générale). Soumis par le Secrétaire Général.
    """
    type_entite = forms.ChoiceField(
        label='Type d\'entité',
        choices=TYPE_ENTITE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    nom = forms.CharField(
        max_length=255,
        label='Nom complet',
        widget=forms.TextInput(attrs={'placeholder': 'Nom et prénom'}),
    )
    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={'placeholder': 'email@exemple.gouv.cd'}),
    )
    province = forms.ModelChoiceField(
        queryset=ProvAdmin.objects.none(),
        label='Division provinciale',
        required=False,
        empty_label='---------',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['province'].queryset = ProvAdmin.objects.all().order_by('designation')

    def clean(self):
        data = super().clean()
        if data.get('type_entite') == 'DIRECTEUR_PROVINCIAL' and not data.get('province'):
            self.add_error('province', 'Veuillez sélectionner une division provinciale.')
        return data


class SetPasswordVerificationForm(forms.Form):
    """Formulaire pour définir le mot de passe après clic sur le lien de validation e-mail."""
    password = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(attrs={'placeholder': 'Choisissez un mot de passe', 'autocomplete': 'new-password'}),
        min_length=8,
    )
    password_confirm = forms.CharField(
        label='Confirmer le mot de passe',
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirmez le mot de passe', 'autocomplete': 'new-password'}),
    )

    def clean(self):
        data = super().clean()
        if data.get('password') != data.get('password_confirm'):
            raise forms.ValidationError('Les deux mots de passe ne correspondent pas.')
        return data
