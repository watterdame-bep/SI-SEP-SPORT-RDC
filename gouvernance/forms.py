from django import forms
from gouvernance.models import Institution, Personne, Agent, Fonction, ProvAdmin, TypeCompetition
from infrastructures.models import Infrastructure


class EnregistrerAgentForm(forms.Form):
    """Formulaire pour enregistrer un agent du Cabinet."""
    
    # Informations Personnelles
    nom = forms.CharField(
        max_length=100,
        label="Nom",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom'})
    )
    postnom = forms.CharField(
        max_length=100,
        label="Postnom",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Postnom'})
    )
    prenom = forms.CharField(
        max_length=100,
        label="Prénom",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom'})
    )
    sexe = forms.ChoiceField(
        choices=[('', '---'), ('M', 'Masculin'), ('F', 'Féminin')],
        label="Sexe",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label="Email",
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    telephone = forms.CharField(
        max_length=50,
        label="Téléphone",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Téléphone'})
    )
    
    # Informations d'Agent
    matricule = forms.CharField(
        max_length=50,
        label="Matricule",
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: MIN-2026-001'})
    )
    
    # Fonction
    fonction = forms.ModelChoiceField(
        queryset=Fonction.objects.all(),
        label="Fonction",
        required=True,
        empty_label="Sélectionner une fonction",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, institution=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.institution = institution
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Vérifier que le matricule est unique
        matricule = cleaned_data.get('matricule')
        if matricule:
            existing = Agent.objects.filter(matricule=matricule)
            if existing.exists():
                raise forms.ValidationError("Ce matricule existe déjà.")
        
        return cleaned_data
    
    def save(self, institution):
        """Crée une Personne et un Agent."""
        # Créer la Personne
        personne = Personne.objects.create(
            nom=self.cleaned_data['nom'],
            postnom=self.cleaned_data.get('postnom', ''),
            prenom=self.cleaned_data.get('prenom', ''),
            sexe=self.cleaned_data.get('sexe', ''),
            email=self.cleaned_data.get('email', ''),
            telephone=self.cleaned_data.get('telephone', ''),
        )
        
        # Créer l'Agent
        agent = Agent.objects.create(
            personne=personne,
            institution=institution,
            matricule=self.cleaned_data['matricule'],
        )
        
        # Créer le Membre
        fonction = self.cleaned_data.get('fonction')
        if fonction:
            from gouvernance.models import Membre
            Membre.objects.get_or_create(
                personne=personne,
                institution=institution,
                fonction=fonction
            )
        
        return agent


class ModifierAgentForm(forms.Form):
    """Formulaire pour modifier les informations d'un agent."""
    
    # Informations Personnelles
    nom = forms.CharField(
        max_length=100,
        label="Nom",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom'})
    )
    postnom = forms.CharField(
        max_length=100,
        label="Postnom",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Postnom'})
    )
    prenom = forms.CharField(
        max_length=100,
        label="Prénom",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom'})
    )
    sexe = forms.ChoiceField(
        choices=[('', '---'), ('M', 'Masculin'), ('F', 'Féminin')],
        label="Sexe",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label="Email",
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    telephone = forms.CharField(
        max_length=50,
        label="Téléphone",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Téléphone'})
    )
    
    # Informations d'Agent
    matricule = forms.CharField(
        max_length=50,
        label="Matricule",
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: MIN-2026-001'})
    )
    
    # Fonction
    fonction = forms.ModelChoiceField(
        queryset=Fonction.objects.all(),
        label="Fonction",
        required=True,
        empty_label="Sélectionner une fonction",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, agent=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.agent = agent
        
        # Pré-remplir les champs
        if agent:
            self.fields['nom'].initial = agent.personne.nom
            self.fields['postnom'].initial = agent.personne.postnom
            self.fields['prenom'].initial = agent.personne.prenom
            self.fields['sexe'].initial = agent.personne.sexe
            self.fields['email'].initial = agent.personne.email
            self.fields['telephone'].initial = agent.personne.telephone
            self.fields['matricule'].initial = agent.matricule
            
            # Récupérer la fonction actuelle
            from gouvernance.models import Membre
            membre = Membre.objects.filter(personne=agent.personne).first()
            if membre:
                self.fields['fonction'].initial = membre.fonction
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Vérifier que le matricule est unique (sauf pour l'agent actuel)
        matricule = cleaned_data.get('matricule')
        if matricule and self.agent:
            existing = Agent.objects.filter(matricule=matricule).exclude(uid=self.agent.uid)
            if existing.exists():
                raise forms.ValidationError("Ce matricule existe déjà.")
        
        return cleaned_data
    
    def save(self):
        """Met à jour les informations de l'agent."""
        if not self.agent:
            return None
        
        # Mettre à jour la Personne
        self.agent.personne.nom = self.cleaned_data['nom']
        self.agent.personne.postnom = self.cleaned_data.get('postnom', '')
        self.agent.personne.prenom = self.cleaned_data.get('prenom', '')
        self.agent.personne.sexe = self.cleaned_data.get('sexe', '')
        self.agent.personne.email = self.cleaned_data.get('email', '')
        self.agent.personne.telephone = self.cleaned_data.get('telephone', '')
        self.agent.personne.save()
        
        # Mettre à jour l'Agent
        self.agent.matricule = self.cleaned_data['matricule']
        self.agent.save()
        
        # Mettre à jour le Membre
        fonction = self.cleaned_data.get('fonction')
        if fonction:
            from gouvernance.models import Membre
            Membre.objects.filter(personne=self.agent.personne).update(fonction=fonction)
        
        return self.agent

class CreerDivisionProvincialForm(forms.Form):
    """Formulaire pour créer une Division Provinciale."""
    
    # Province Administrative
    province_admin = forms.ModelChoiceField(
        queryset=ProvAdmin.objects.all().order_by('designation'),
        label="Province Administrative",
        required=True,
        empty_label="Sélectionner une province",
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue text-sm'})
    )
    
    # Informations du Chef de Division
    nom_chef = forms.CharField(
        max_length=100,
        label="Nom du Chef de Division",
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue text-sm', 'placeholder': 'Nom complet'})
    )
    postnom_chef = forms.CharField(
        max_length=100,
        label="Postnom",
        required=False,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue text-sm', 'placeholder': 'Postnom'})
    )
    prenom_chef = forms.CharField(
        max_length=100,
        label="Prénom",
        required=False,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue text-sm', 'placeholder': 'Prénom'})
    )
    matricule_chef = forms.CharField(
        max_length=50,
        label="Matricule du Chef",
        required=True,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue text-sm', 'placeholder': 'Ex: DIV-PROV-2026-001'})
    )
    email_chef = forms.EmailField(
        label="Email du Chef",
        required=True,
        widget=forms.EmailInput(attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue text-sm', 'placeholder': 'Email'})
    )
    telephone_chef = forms.CharField(
        max_length=50,
        label="Téléphone du Chef",
        required=False,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue text-sm', 'placeholder': 'Téléphone'})
    )
    
    # Localisation
    adresse_division = forms.CharField(
        max_length=500,
        label="Adresse physique de la Division",
        required=True,
        widget=forms.Textarea(attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue text-sm', 'rows': 3, 'placeholder': 'Adresse complète'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Vérifier que le matricule est unique
        matricule = cleaned_data.get('matricule_chef')
        if matricule:
            existing = Agent.objects.filter(matricule=matricule)
            if existing.exists():
                raise forms.ValidationError("Ce matricule existe déjà.")
        
        # Vérifier que l'email n'existe pas
        email = cleaned_data.get('email_chef')
        if email:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError("Cet email est déjà utilisé.")
        
        return cleaned_data


class CreerFederationForm(forms.ModelForm):
    """Formulaire pour créer/modifier une fédération avec sélection des provinces d'implantation."""
    
    provinces_implantation = forms.ModelMultipleChoiceField(
        queryset=ProvAdmin.objects.all().order_by('designation'),
        label="Provinces d'implantation",
        required=True,
        help_text="Sélectionnez les provinces où la fédération prétend être installée (minimum 6 pour une Fédération Nationale)",
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = Institution
        fields = [
            'code',
            'nom_officiel',
            'sigle',
            'disciplines',
            'provinces_implantation',
            'nom_president',
            'telephone_president',
            'email_officiel',
            'site_web',
            'document_statuts',
            'document_pv_ag',
            'document_liste_membres',
            'document_certificat',
        ]
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Code unique'}),
            'nom_officiel': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom officiel'}),
            'sigle': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sigle'}),
            'disciplines': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
            'nom_president': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom du Président'}),
            'telephone_president': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Téléphone'}),
            'email_officiel': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'site_web': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Site web'}),
            'document_statuts': forms.FileInput(attrs={'class': 'form-control'}),
            'document_pv_ag': forms.FileInput(attrs={'class': 'form-control'}),
            'document_liste_membres': forms.FileInput(attrs={'class': 'form-control'}),
            'document_certificat': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def clean_provinces_implantation(self):
        provinces = self.cleaned_data.get('provinces_implantation')
        if provinces and len(provinces) < 6:
            # Avertissement mais pas erreur - on peut créer une fédération avec moins de 6 provinces
            # mais elle ne sera pas considérée comme "Nationale"
            pass
        return provinces


class CreerLigueProvincialForm(forms.Form):
    """Formulaire pour créer une Ligue Provinciale - Adapté du formulaire de fédération."""
    
    # ===== ÉTAPE 1: IDENTITÉ =====
    # Province Administrative
    province_admin = forms.ModelChoiceField(
        queryset=ProvAdmin.objects.all().order_by('designation'),
        label="Province Administrative",
        required=True,
        empty_label="Sélectionner une province",
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue text-sm'})
    )
    
    # Nom de la Ligue
    nom_ligue = forms.CharField(
        max_length=255,
        label="Nom officiel de la Ligue",
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue text-sm', 'placeholder': 'Ex: Ligue Provinciale de Kinshasa'})
    )
    
    # Sigle (optionnel)
    sigle_ligue = forms.CharField(
        max_length=50,
        label="Sigle",
        required=False,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue text-sm uppercase', 'placeholder': 'Ex: LPK'})
    )
    
    # Disciplines (pré-remplies, non éditables)
    disciplines = forms.ModelMultipleChoiceField(
        queryset=None,  # Sera défini dans __init__
        label="Disciplines sportives",
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input', 'disabled': 'disabled'}),
        help_text="Disciplines héritées de la fédération (non modifiables)"
    )
    
    # Statut juridique
    statut_juridique = forms.CharField(
        max_length=100,
        label="Statut juridique",
        required=False,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue text-sm', 'placeholder': 'Ex: Association sans but lucratif'})
    )
    
    # Date de création
    date_creation = forms.DateField(
        label="Date de création",
        required=False,
        widget=forms.DateInput(attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue text-sm', 'type': 'date'})
    )
    
    # ===== ÉTAPE 2: COORDONNÉES =====
    # Téléphone officiel
    telephone_off = forms.CharField(
        max_length=50,
        label="Téléphone officiel",
        required=True,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue text-sm', 'placeholder': 'Ex: +243 123 456 789'})
    )
    
    # Email officiel
    email_officiel = forms.EmailField(
        label="Email officiel",
        required=True,
        widget=forms.EmailInput(attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue text-sm', 'placeholder': 'Ex: contact@ligue.cd'})
    )
    
    # Site web
    site_web = forms.URLField(
        label="Site web",
        required=False,
        widget=forms.URLInput(attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue text-sm', 'placeholder': 'Ex: https://www.ligue.cd'})
    )
    
    # ===== ÉTAPE 3: RESPONSABLES =====
    # Nom du Président Provincial
    nom_president = forms.CharField(
        max_length=255,
        label="Nom du Président Provincial",
        required=True,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue text-sm', 'placeholder': 'Ex: Jean KABILA'})
    )
    
    # Téléphone du Président
    telephone_president = forms.CharField(
        max_length=50,
        label="Téléphone du Président",
        required=False,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue text-sm', 'placeholder': 'Ex: +243 123 456 789'})
    )
    
    # ===== ÉTAPE 4: DOCUMENTS =====
    # Statuts
    document_statuts = forms.FileField(
        label="Statuts de la ligue",
        required=False,
        widget=forms.FileInput(attrs={'class': 'upload-input', 'accept': '.pdf', 'id': 'doc-statuts'})
    )
    
    # PV AG
    document_pv_ag = forms.FileField(
        label="PV de l'Assemblée Générale",
        required=False,
        widget=forms.FileInput(attrs={'class': 'upload-input', 'accept': '.pdf', 'id': 'doc-pv'})
    )
    
    # Liste des membres
    document_liste_membres = forms.FileField(
        label="Liste des membres",
        required=False,
        widget=forms.FileInput(attrs={'class': 'upload-input', 'accept': '.pdf', 'id': 'doc-membres'})
    )
    
    def __init__(self, *args, federation=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Pré-remplir les disciplines de la fédération
        if federation:
            self.fields['disciplines'].queryset = federation.disciplines.all()
            self.fields['disciplines'].initial = federation.disciplines.all()
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Vérifier que l'email officiel n'existe pas
        email = cleaned_data.get('email_officiel')
        if email:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError("Cet email est déjà utilisé.")
        
        return cleaned_data


class ClubCreationForm(forms.Form):
    """Formulaire pour créer un club - Étape 1: Informations de base."""
    
    nom_officiel = forms.CharField(
        max_length=255,
        label="Nom officiel du club",
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue text-sm', 'placeholder': 'Ex: Club Sportif de Kinshasa'})
    )
    
    sigle = forms.CharField(
        max_length=50,
        label="Sigle",
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue text-sm uppercase', 'placeholder': 'Ex: CSK'})
    )
    
    code = forms.CharField(
        max_length=50,
        label="Code unique",
        required=False,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg bg-slate-100 cursor-not-allowed text-sm', 'readonly': 'readonly', 'placeholder': 'Généré automatiquement'})
    )
    
    statut_juridique = forms.CharField(
        max_length=100,
        label="Statut juridique",
        required=False,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue text-sm', 'placeholder': 'Ex: Association sans but lucratif'})
    )
    
    date_creation = forms.DateField(
        label="Date de création",
        required=False,
        widget=forms.DateInput(attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue text-sm', 'type': 'date'})
    )
    
    nombre_pers_admin = forms.IntegerField(
        label="Nombre de personnel administratif",
        required=False,
        min_value=0,
        initial=0,
        widget=forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue text-sm', 'placeholder': 'Ex: 5'})
    )
    
    nombre_pers_tech = forms.IntegerField(
        label="Nombre de personnel technique",
        required=False,
        min_value=0,
        initial=0,
        widget=forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue text-sm', 'placeholder': 'Ex: 10'})
    )
    
    partenaire = forms.CharField(
        max_length=255,
        label="Partenaires",
        required=False,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue text-sm', 'placeholder': 'Ex: Sponsors, Partenaires...'})
    )
    
    email_officiel = forms.EmailField(
        label="Email officiel",
        required=False,
        widget=forms.EmailInput(attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue text-sm', 'placeholder': 'Ex: contact@club.cd'})
    )
    
    telephone_off = forms.CharField(
        max_length=50,
        label="Téléphone officiel",
        required=False,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue text-sm', 'placeholder': 'Ex: +243 123 456 789'})
    )
    
    site_web = forms.URLField(
        label="Site web",
        required=False,
        widget=forms.URLInput(attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue text-sm', 'placeholder': 'Ex: https://www.club.cd'})
    )
    
    logo = forms.ImageField(
        label="Logo du club",
        required=False,
        widget=forms.FileInput(attrs={'class': 'upload-input', 'accept': 'image/*', 'id': 'doc-logo'})
    )


class ClubAddressForm(forms.Form):
    """Formulaire pour créer un club - Étape 2: Adresse et localisation."""
    
    # Localisation - Cascading selects
    province = forms.ModelChoiceField(
        queryset=ProvAdmin.objects.all().order_by('designation'),
        label="Province",
        required=True,
        empty_label="Sélectionner une province",
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue text-sm', 'id': 'province-select'})
    )
    
    territoire = forms.CharField(
        max_length=255,
        label="Territoire/Ville",
        required=False,
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue text-sm', 'id': 'territoire-select'})
    )
    
    secteur = forms.CharField(
        max_length=255,
        label="Secteur/Commune",
        required=False,
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue text-sm', 'id': 'secteur-select'})
    )
    
    groupement_quartier = forms.CharField(
        max_length=255,
        label="Groupement/Quartier",
        required=False,
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue text-sm', 'id': 'groupement-select'})
    )
    
    avenue = forms.CharField(
        max_length=255,
        label="Avenue/Rue",
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue text-sm', 'placeholder': 'Ex: Avenue de la Paix'})
    )
    
    numero = forms.CharField(
        max_length=50,
        label="Numéro",
        required=False,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue text-sm', 'placeholder': 'Ex: 123'})
    )
    
    # Responsables
    nom_president = forms.CharField(
        max_length=255,
        label="Nom du Président du Club",
        required=True,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue text-sm', 'placeholder': 'Ex: Jean KABILA'})
    )
    
    telephone_president = forms.CharField(
        max_length=50,
        label="Téléphone du Président",
        required=False,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue text-sm', 'placeholder': 'Ex: +243 123 456 789'})
    )
    
    nationalite_president = forms.CharField(
        max_length=100,
        label="Nationalité du Président",
        required=False,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue text-sm', 'placeholder': 'Ex: Congolaise'})
    )
    
    # Agrément
    type_agrement_sollicite = forms.ChoiceField(
        choices=[('', '---'), ('PROVISOIRE', 'Agrément provisoire'), ('DEFINITIF', 'Agrément définitif')],
        label="Type d'agrément sollicité",
        required=False,
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue text-sm'})
    )
    
    date_demande_agrement = forms.DateField(
        label="Date de demande d'agrément",
        required=False,
        widget=forms.DateInput(attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue text-sm', 'type': 'date'})
    )
    
    duree_sollicitee = forms.ChoiceField(
        choices=[('2', '2 ans'), ('4', '4 ans'), ('6', '6 ans')],
        label="Durée sollicitée (années)",
        initial='4',
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue text-sm'})
    )
    
    def __init__(self, *args, ligue=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.ligue = ligue
        
        # Pre-fill province with ligue's province if available
        if ligue and ligue.province_admin:
            self.fields['province'].initial = ligue.province_admin


class ClubDisciplinesForm(forms.Form):
    """Formulaire pour créer un club - Étape 3: Disciplines et confirmation."""
    
    disciplines = forms.ModelMultipleChoiceField(
        queryset=None,  # Sera défini dans __init__
        label="Disciplines sportives",
        required=True,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        help_text="Sélectionnez les disciplines pratiquées par le club"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from gouvernance.models.discipline import DisciplineSport
        self.fields['disciplines'].queryset = DisciplineSport.objects.filter(actif=True).order_by('designation')


class ClubDocumentsForm(forms.Form):
    """Formulaire pour créer un club - Étape 3: Documents."""
    
    statut_club = forms.FileField(
        label="Statut du club",
        required=False,
        widget=forms.FileInput(attrs={'class': 'upload-input', 'accept': '.pdf', 'id': 'doc-statut'})
    )
    
    reglement_interieur = forms.FileField(
        label="Règlement intérieur",
        required=False,
        widget=forms.FileInput(attrs={'class': 'upload-input', 'accept': '.pdf', 'id': 'doc-reglement'})
    )
    
    pv_assemblee_generale = forms.FileField(
        label="PV de l'Assemblée Générale",
        required=False,
        widget=forms.FileInput(attrs={'class': 'upload-input', 'accept': '.pdf', 'id': 'doc-pv'})
    )
    
    contrat_bail = forms.FileField(
        label="Contrat de bail",
        required=False,
        widget=forms.FileInput(attrs={'class': 'upload-input', 'accept': '.pdf', 'id': 'doc-bail'})
    )
    
    liste_membres_fondateurs = forms.FileField(
        label="Liste des membres fondateurs",
        required=False,
        widget=forms.FileInput(attrs={'class': 'upload-input', 'accept': '.pdf', 'id': 'doc-membres'})
    )
    
    certificat_nationalite = forms.FileField(
        label="Certificat de nationalité",
        required=False,
        widget=forms.FileInput(attrs={'class': 'upload-input', 'accept': '.pdf', 'id': 'doc-nationalite'})
    )
    
    liste_athletes = forms.FileField(
        label="Liste des athlètes",
        required=False,
        widget=forms.FileInput(attrs={'class': 'upload-input', 'accept': '.pdf', 'id': 'doc-athletes'})
    )
    
    disciplines = forms.ModelMultipleChoiceField(
        queryset=None,  # Sera défini dans __init__
        label="Disciplines sportives",
        required=True,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        help_text="Sélectionnez les disciplines pratiquées par le club"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from gouvernance.models.discipline import DisciplineSport
        self.fields['disciplines'].queryset = DisciplineSport.objects.filter(actif=True).order_by('designation')
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Valider la taille des fichiers (max 10MB)
        file_fields = [
            'statut_club', 'reglement_interieur', 'pv_assemblee_generale',
            'contrat_bail', 'liste_membres_fondateurs', 'certificat_nationalite',
            'liste_athletes'
        ]
        
        for field_name in file_fields:
            file = cleaned_data.get(field_name)
            if file and file.size > 10 * 1024 * 1024:  # 10MB
                raise forms.ValidationError(f"Le fichier {field_name} est trop volumineux. Taille maximale: 10MB.")
        
        return cleaned_data



class AthleteForm(forms.Form):
    """Formulaire pour enregistrer un athlète (crée Personne + Athlete)."""
    
    # Informations personnelles (Personne)
    nom = forms.CharField(
        max_length=100,
        label='Nom *',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue',
            'placeholder': 'Nom de famille'
        })
    )
    postnom = forms.CharField(
        max_length=100,
        required=False,
        label='Postnom',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue',
            'placeholder': 'Postnom'
        })
    )
    prenom = forms.CharField(
        max_length=100,
        label='Prénom *',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue',
            'placeholder': 'Prénom'
        })
    )
    sexe = forms.ChoiceField(
        choices=[('', '---'), ('M', 'Masculin'), ('F', 'Féminin')],
        label='Sexe *',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue'
        })
    )
    date_naissance = forms.DateField(
        label='Date de naissance *',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue'
        })
    )
    lieu_naissance = forms.CharField(
        max_length=255,
        label='Lieu de naissance *',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue',
            'placeholder': 'Ville/Territoire de naissance'
        })
    )
    telephone = forms.CharField(
        max_length=50,
        required=False,
        label='Téléphone',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue',
            'placeholder': '+243 XXX XXX XXX'
        })
    )
    email = forms.EmailField(
        required=False,
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue',
            'placeholder': 'email@example.com'
        })
    )
    photo = forms.ImageField(
        required=False,
        label='Photo d\'identité',
        widget=forms.FileInput(attrs={
            'class': 'hidden',
            'accept': 'image/*',
            'id': 'photo-input-file'
        })
    )
    
    # Adresse
    province = forms.ModelChoiceField(
        queryset=None,  # Sera défini dans __init__
        label='Province *',
        required=True,
        empty_label='Sélectionner une province',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue',
            'id': 'athlete-province-select'
        })
    )
    territoire = forms.CharField(
        max_length=255,
        label='Territoire/Ville *',
        required=True,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue',
            'id': 'athlete-territoire-select'
        })
    )
    secteur = forms.CharField(
        max_length=255,
        label='Secteur/Commune',
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue',
            'id': 'athlete-secteur-select'
        })
    )
    groupement_quartier = forms.CharField(
        max_length=255,
        label='Groupement/Quartier',
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue',
            'id': 'athlete-groupement-select'
        })
    )
    avenue = forms.CharField(
        max_length=255,
        label='Avenue/Rue',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue',
            'placeholder': 'Ex: Avenue de la Paix'
        })
    )
    numero = forms.CharField(
        max_length=50,
        label='Numéro',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue',
            'placeholder': 'Ex: 123'
        })
    )
    
    # Informations sportives (Athlete)
    discipline = forms.ModelChoiceField(
        queryset=None,  # Sera défini dans __init__
        label='Discipline sportive *',
        required=True,
        empty_label='Sélectionner une discipline',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue'
        })
    )
    numero_maillot = forms.IntegerField(
        required=False,
        label='Numéro de maillot',
        min_value=1,
        max_value=99,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue',
            'placeholder': '1-99',
            'min': '1',
            'max': '99',
            'id': 'numero-maillot-input',
            'maxlength': '2'
        })
    )
    poste = forms.CharField(
        max_length=100,
        required=False,
        label='Poste/Spécialité',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue',
            'placeholder': 'Ex: Gardien, Attaquant, 100m, etc.'
        })
    )
    categorie = forms.ChoiceField(
        choices=[
            ('', '---'),
            ('SENIOR', 'Senior'),
            ('JUNIOR', 'Junior'),
            ('CADET', 'Cadet'),
            ('MINIME', 'Minime'),
            ('BENJAMIN', 'Benjamin'),
            ('POUSSIN', 'Poussin'),
        ],
        label='Catégorie *',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue'
        })
    )
    
    # Informations médicales
    groupe_sanguin = forms.ChoiceField(
        choices=[
            ('', '---'),
            ('A+', 'A+'),
            ('A-', 'A-'),
            ('B+', 'B+'),
            ('B-', 'B-'),
            ('AB+', 'AB+'),
            ('AB-', 'AB-'),
            ('O+', 'O+'),
            ('O-', 'O-'),
        ],
        required=False,
        label='Groupe sanguin',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue'
        })
    )
    allergies = forms.CharField(
        required=False,
        label='Allergies',
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue',
            'rows': 2,
            'placeholder': 'Allergies connues (médicaments, aliments, etc.)'
        })
    )
    
    def __init__(self, *args, club=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Définir les provinces disponibles
        from gouvernance.models import ProvAdmin
        self.fields['province'].queryset = ProvAdmin.objects.all().order_by('designation')
        
        # Définir les disciplines disponibles (celles du club via sa ligue/fédération)
        if club:
            from gouvernance.models import DisciplineSport
            # Récupérer les disciplines de la ligue parente ou toutes les disciplines actives
            if club.institution_tutelle:
                disciplines_club = club.institution_tutelle.disciplines.filter(actif=True)
                self.fields['discipline'].queryset = disciplines_club
                
                # Pré-remplir avec la première discipline du club si une seule existe
                if disciplines_club.count() == 1:
                    self.fields['discipline'].initial = disciplines_club.first()
                    # Rendre le champ en lecture seule si une seule discipline
                    self.fields['discipline'].widget.attrs['readonly'] = 'readonly'
                    self.fields['discipline'].widget.attrs['class'] += ' bg-slate-100 cursor-not-allowed'
            else:
                self.fields['discipline'].queryset = DisciplineSport.objects.filter(actif=True)
        else:
            from gouvernance.models import DisciplineSport
            self.fields['discipline'].queryset = DisciplineSport.objects.filter(actif=True)
    
    def save(self, club):
        """Crée une Personne et un Athlete."""
        from gouvernance.models import Personne, Athlete, AdresseContact, GroupementQuartier
        from django.db import transaction
        
        with transaction.atomic():
            # Créer l'adresse si les informations sont fournies
            adresse = None
            if self.cleaned_data.get('province') and self.cleaned_data.get('territoire'):
                # Récupérer ou créer le GroupementQuartier si fourni
                groupement_quartier_obj = None
                if self.cleaned_data.get('groupement_quartier'):
                    try:
                        groupement_quartier_obj = GroupementQuartier.objects.get(
                            uid=self.cleaned_data['groupement_quartier']
                        )
                    except (GroupementQuartier.DoesNotExist, ValueError):
                        pass
                
                adresse = AdresseContact.objects.create(
                    avenue=self.cleaned_data.get('avenue', ''),
                    numero=self.cleaned_data.get('numero') if self.cleaned_data.get('numero') else None,
                    commune=self.cleaned_data.get('territoire', ''),
                    groupement_quartier=groupement_quartier_obj
                )
            
            # Créer la Personne
            personne = Personne.objects.create(
                nom=self.cleaned_data['nom'],
                postnom=self.cleaned_data.get('postnom', ''),
                prenom=self.cleaned_data['prenom'],
                sexe=self.cleaned_data['sexe'],
                date_naissance=self.cleaned_data['date_naissance'],
                telephone=self.cleaned_data.get('telephone', ''),
                email=self.cleaned_data.get('email', ''),
                photo=self.cleaned_data.get('photo'),
                adresse=adresse
            )
            
            # Créer l'Athlete
            athlete = Athlete.objects.create(
                personne=personne,
                club=club,
                discipline=self.cleaned_data.get('discipline'),
                numero_maillot=self.cleaned_data.get('numero_maillot'),
                poste=self.cleaned_data.get('poste', ''),
                categorie=self.cleaned_data['categorie'],
                groupe_sanguin=self.cleaned_data.get('groupe_sanguin', ''),
                allergies=self.cleaned_data.get('allergies', ''),
                statut_certification='PROVISOIRE'  # Statut initial
            )
            
            return athlete


class LigueEvenementForm(forms.Form):
    """Formulaire pour créer un événement sportif (match, compétition) par la ligue."""
    TYPE_EVENEMENT_CHOICES = [
        ('MATCH', 'Match'),
        ('COMPETITION_ATHLETISME', "Compétition d'athlétisme"),
        ('COMPETITION', 'Compétition sportive'),
        ('GALA', 'Gala / Cérémonie'),
        ('AUTRE', 'Autre'),
    ]
    infrastructure = forms.ModelChoiceField(
        queryset=Infrastructure.objects.none(),  # Sera remplacé dans __init__ (infrastructures de la province)
        label='Lieu (infrastructure) *',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue'
        })
    )

    def __init__(self, *args, queryset_infrastructure=None, **kwargs):
        super().__init__(*args, **kwargs)
        if queryset_infrastructure is not None:
            self.fields['infrastructure'].queryset = queryset_infrastructure
    titre = forms.CharField(
        max_length=255,
        label='Titre de l\'événement *',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue',
            'placeholder': 'Ex: Match RDC vs Sénégal, Championnat provincial...'
        })
    )
    type_evenement = forms.ChoiceField(
        choices=TYPE_EVENEMENT_CHOICES,
        label='Type *',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue'
        })
    )
    date_evenement = forms.DateField(
        label='Date *',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue'
        })
    )
    heure_debut = forms.TimeField(
        required=False,
        label='Heure de début',
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue'
        })
    )
    description = forms.CharField(
        required=False,
        label='Description',
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue',
            'rows': 3,
            'placeholder': 'Détails complémentaires...'
        })
    )


# ---------- Compétitions (types, compétitions par saison, calendrier) ----------

class TypeCompetitionForm(forms.Form):
    """Formulaire pour ajouter un type de compétition (ligue)."""
    designation = forms.CharField(
        max_length=255,
        label='Intitulé du type *',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue',
            'placeholder': 'Ex: Championnat provincial, Coupe de la ligue',
        })
    )
    code = forms.CharField(
        max_length=50,
        required=False,
        label='Code (optionnel)',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue',
            'placeholder': 'Ex: CHAMP-PROV',
        })
    )
    ordre = forms.IntegerField(
        initial=0,
        label='Ordre d\'affichage',
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue',
        })
    )


class LigueCompetitionForm(forms.Form):
    """Créer une compétition (type + saison + catégorie + titre)."""
    type_competition = forms.ModelChoiceField(
        queryset=TypeCompetition.objects.none(),
        label='Type de compétition *',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue'
        })
    )
    saison = forms.CharField(
        max_length=20,
        label='Saison / Année sportive *',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue',
            'placeholder': 'Ex: 2024-2025 ou 2024',
        })
    )
    categorie = forms.ChoiceField(
        label='Catégorie',
        choices=[('SENIOR', 'Sénior'), ('JUNIOR', 'Junior'), ('TOUS', 'Toutes catégories')],
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue'
        })
    )
    titre = forms.CharField(
        max_length=255,
        label='Titre de la compétition *',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue',
            'placeholder': 'Ex: Championnat provincial Kinshasa 2024-2025',
        })
    )
    description = forms.CharField(
        required=False,
        label='Description',
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue',
            'rows': 3,
        })
    )

    def __init__(self, *args, queryset_types=None, **kwargs):
        super().__init__(*args, **kwargs)
        if queryset_types is not None:
            self.fields['type_competition'].queryset = queryset_types


class CalendrierCompetitionForm(forms.Form):
    """Ajouter une date au calendrier d'une compétition."""
    date = forms.DateField(
        label='Date *',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue'
        })
    )
    heure_debut = forms.TimeField(
        required=False,
        label='Heure',
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue'
        })
    )
    libelle = forms.CharField(
        max_length=255,
        label='Libellé *',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue',
            'placeholder': 'Ex: Journée 1, Phase de poules',
        })
    )
    infrastructure = forms.ModelChoiceField(
        queryset=Infrastructure.objects.none(),
        required=False,
        label='Lieu (infrastructure)',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue'
        })
    )
    ordre = forms.IntegerField(
        initial=0,
        label='Ordre',
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue'
        })
    )

    def __init__(self, *args, queryset_infrastructure=None, **kwargs):
        super().__init__(*args, **kwargs)
        if queryset_infrastructure is not None:
            self.fields['infrastructure'].queryset = queryset_infrastructure


class JourneeForm(forms.Form):
    """Ajouter une journée à une compétition."""
    libelle = forms.CharField(
        max_length=255,
        label='Libellé de la journée *',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue',
            'placeholder': 'Ex: 1ère Journée, Phase de poules',
        })
    )
    ordre = forms.IntegerField(initial=0, label='Ordre', widget=forms.NumberInput(attrs={
        'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue',
    }))


class RencontreForm(forms.Form):
    """Créer une rencontre (match) : équipes, stade, date/heure."""
    equipe_a = forms.ModelChoiceField(
        queryset=Institution.objects.none(),
        label='Équipe A (domicile) *',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue'
        })
    )
    equipe_b = forms.ModelChoiceField(
        queryset=Institution.objects.none(),
        label='Équipe B (extérieur) *',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue'
        })
    )
    stade = forms.ModelChoiceField(
        queryset=Infrastructure.objects.none(),
        required=True,
        label='Stade *',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue'
        })
    )
    date_heure = forms.DateTimeField(
        label='Date et heure du match *',
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue'
        })
    )

    def __init__(self, *args, queryset_clubs=None, queryset_stades=None, **kwargs):
        super().__init__(*args, **kwargs)
        if queryset_clubs is not None:
            self.fields['equipe_a'].queryset = queryset_clubs
            self.fields['equipe_b'].queryset = queryset_clubs
        if queryset_stades is not None:
            self.fields['stade'].queryset = queryset_stades
