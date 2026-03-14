"""
Formulaires pour le module Infrastructures Sportives.
"""
from django import forms
from .models import Infrastructure, TypeInfrastructure, PhotoInfrastructure


class InfrastructureForm(forms.ModelForm):
    """
    Formulaire pour créer/modifier une infrastructure avec géolocalisation.
    """
    
    class Meta:
        model = Infrastructure
        fields = [
            'code_homologation',
            'nom',
            'type_infrastructure',
            'description',
            'latitude',
            'longitude',
            'province_admin',
            'territoire',
            'secteur',
            'quartier',
            'avenue',
            'numero',
            'proprietaire_type',
            'proprietaire',
            'gestionnaire_type',
            'gestionnaire_prenom',
            'gestionnaire_nom',
            'gestionnaire_postnom',
            'gestionnaire_sexe',
            'telephone_gestionnaire',
            'email_gestionnaire',
            'etat_viabilite',
            'type_sol',
            'interet_national',
            'capacite_spectateurs',
            'surface_sportive',
            'equipements_disponibles',
            'eclairage',
            'vestiaires',
            'securite',
        ]
        widgets = {
            'code_homologation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: STAD-KIN-001',
                'readonly': 'readonly',
            }),
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de l\'infrastructure',
            }),
            'type_infrastructure': forms.Select(attrs={
                'class': 'form-control',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description détaillée de l\'infrastructure',
            }),
            'latitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Latitude (ex: -4.321000)',
                'step': '0.000001',
                'id': 'id_latitude',
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Longitude (ex: 15.312500)',
                'step': '0.000001',
                'id': 'id_longitude',
            }),
            'province_admin': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_province_admin',
            }),
            'territoire': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_territoire',
            }),
            'secteur': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_secteur',
            }),
            'quartier': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_quartier',
            }),
            'avenue': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de l\'avenue/rue',
            }),
            'numero': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Numéro',
            }),
            'proprietaire_type': forms.Select(attrs={
                'class': 'form-control',
            }),
            'proprietaire': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Propriétaire',
                'readonly': 'readonly',
            }),
            'gestionnaire_type': forms.Select(attrs={
                'class': 'form-control',
            }),
            'gestionnaire_prenom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Prénom',
            }),
            'gestionnaire_nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom',
            }),
            'gestionnaire_postnom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Postnom',
            }),
            'gestionnaire_sexe': forms.Select(attrs={
                'class': 'form-control',
            }),
            'telephone_gestionnaire': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: +243 123 456 789',
                'type': 'tel',
            }),
            'email_gestionnaire': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: contact@example.com',
                'type': 'email',
            }),
            'etat_viabilite': forms.Select(attrs={
                'class': 'form-control',
            }),
            'type_sol': forms.Select(attrs={
                'class': 'form-control',
            }),
            'interet_national': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'capacite_spectateurs': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 5000',
            }),
            'surface_sportive': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 100m x 60m',
            }),
            'equipements_disponibles': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ex: Buts, filets, bancs, etc.',
            }),
            'eclairage': forms.Select(attrs={
                'class': 'form-control',
            }),
            'vestiaires': forms.Select(attrs={
                'class': 'form-control',
            }),
            'securite': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ex: Clôture, gardiens, extincteurs, etc.',
            }),
        }

    def __init__(self, *args, **kwargs):
        user_role = kwargs.pop('user_role', None)
        self.user_role = user_role
        super().__init__(*args, **kwargs)
        
        # Le code_homologation sera généré automatiquement, donc le rendre optionnel
        self.fields['code_homologation'].required = False
        
        # Rendre les champs optionnels si nécessaire
        self.fields['description'].required = False
        self.fields['avenue'].required = False
        self.fields['numero'].required = False
        self.fields['territoire'].required = False
        self.fields['secteur'].required = False
        self.fields['quartier'].required = False
        self.fields['type_sol'].required = False
        self.fields['interet_national'].required = False
        self.fields['capacite_spectateurs'].required = False
        self.fields['surface_sportive'].required = False
        self.fields['equipements_disponibles'].required = False
        self.fields['eclairage'].required = False
        self.fields['vestiaires'].required = False
        self.fields['securite'].required = False
        self.fields['proprietaire_type'].required = False
        self.fields['proprietaire'].required = False
        self.fields['gestionnaire_type'].required = False
        self.fields['gestionnaire_prenom'].required = False
        self.fields['gestionnaire_nom'].required = False
        self.fields['gestionnaire_postnom'].required = False
        self.fields['gestionnaire_sexe'].required = False
        self.fields['telephone_gestionnaire'].required = False
        self.fields['email_gestionnaire'].required = False
        
        # Ajouter des labels personnalisés
        self.fields['latitude'].label = 'Latitude'
        self.fields['longitude'].label = 'Longitude'
        self.fields['etat_viabilite'].label = 'État de Viabilité'
        self.fields['type_sol'].label = 'Type de Sol'
        self.fields['province_admin'].label = 'Province'
        self.fields['territoire'].label = 'Territoire/Ville'
        self.fields['secteur'].label = 'Secteur'
        self.fields['quartier'].label = 'Quartier/Groupement'
        self.fields['avenue'].label = 'Avenue/Rue'
        self.fields['numero'].label = 'Numéro'
        self.fields['proprietaire_type'].label = 'Type de Propriétaire'
        self.fields['proprietaire'].label = 'Propriétaire'
        self.fields['gestionnaire_type'].label = 'Type de Gestionnaire'
        self.fields['gestionnaire_prenom'].label = 'Prénom du Gestionnaire'
        self.fields['gestionnaire_nom'].label = 'Nom du Gestionnaire'
        self.fields['gestionnaire_postnom'].label = 'Postnom du Gestionnaire'
        self.fields['gestionnaire_sexe'].label = 'Sexe du Gestionnaire'
        self.fields['telephone_gestionnaire'].label = 'Téléphone du Gestionnaire'
        self.fields['email_gestionnaire'].label = 'Email du Gestionnaire'
        self.fields['interet_national'].label = 'Infrastructure d\'Intérêt National'
        
        # Désactiver le champ interet_national pour les Directeurs Provinciaux
        if user_role == 'directeur_provincial':
            self.fields['interet_national'].disabled = True
            self.fields['interet_national'].help_text = 'Ce champ ne peut être modifié que par le Secrétaire Général'
            
            # Désactiver la province pour les Directeurs Provinciaux
            self.fields['province_admin'].disabled = True
            self.fields['province_admin'].help_text = 'Province auto-remplie'
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Générer le code_homologation si absent et c'est une création
        if not self.instance.pk and not cleaned_data.get('code_homologation'):
            # On va le générer dans la vue, donc on ne fait rien ici
            pass
        
        return cleaned_data


class PhotoInfrastructureForm(forms.ModelForm):
    """
    Formulaire pour ajouter une photo à une infrastructure.
    """
    
    class Meta:
        model = PhotoInfrastructure
        fields = ['photo', 'description']
        widgets = {
            'photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'capture': 'environment',
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Vue générale, Entrée, Vestiaires, etc.',
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].required = False
        self.fields['description'].label = 'Description (optionnel)'
        self.fields['photo'].label = 'Photo'
