"""
Formulaires pour le référentiel géographique
"""
from django import forms
from gouvernance.models import (
    ProvAdmin,
    TerritoireVille,
    SecteurCommune,
    GroupementQuartier,
)


class ProvAdminForm(forms.ModelForm):
    """Formulaire pour Province Administrative"""
    class Meta:
        model = ProvAdmin
        fields = ['designation', 'description', 'code']
        widgets = {
            'designation': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue',
                'placeholder': 'Ex: Kinshasa'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue',
                'rows': 3,
                'placeholder': 'Description optionnelle'
            }),
            'code': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rdc-blue focus:border-rdc-blue',
                'placeholder': 'Ex: KIN'
            }),
        }


class TerritoireVilleForm(forms.ModelForm):
    """Formulaire pour Territoire/Ville"""
    
    class Meta:
        model = TerritoireVille
        fields = ['province_admin', 'designation', 'description', 'code']
        widgets = {
            'province_admin': forms.Select(attrs={
                'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'designation': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Ex: Gombe'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 3
            }),
            'code': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
        }


class SecteurCommuneForm(forms.ModelForm):
    """Formulaire pour Secteur/Commune"""
    
    class Meta:
        model = SecteurCommune
        fields = ['territoire', 'designation', 'description']
        widgets = {
            'territoire': forms.Select(attrs={
                'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500'
            }),
            'designation': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500',
                'rows': 3
            }),
        }


class GroupementQuartierForm(forms.ModelForm):
    """Formulaire pour Groupement/Quartier"""
    
    class Meta:
        model = GroupementQuartier
        fields = ['secteur', 'designation', 'description']
        widgets = {
            'secteur': forms.Select(attrs={
                'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500'
            }),
            'designation': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500',
                'rows': 3
            }),
        }

