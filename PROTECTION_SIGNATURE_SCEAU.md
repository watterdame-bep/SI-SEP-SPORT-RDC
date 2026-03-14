# Protection de la Signature et du Sceau par Mot de Passe

## Résumé

La signature et le sceau du Ministre sont maintenant protégés par une confirmation de mot de passe. Aucune modification ne peut être effectuée sans que le Ministre entre son mot de passe, garantissant que seul le Ministre autorisé peut modifier ces documents d'État.

## Sécurité implémentée

### 1. Confirmation par Mot de Passe Obligatoire
- **Avant**: N'importe qui ayant accès au profil du Ministre pouvait modifier la signature/sceau
- **Après**: Seul le Ministre (avec son mot de passe) peut modifier ces éléments

### 2. Formulaire de Confirmation
Un nouveau formulaire `ConfirmationMotDePasseForm` a été créé qui:
- Demande le mot de passe de l'utilisateur
- Valide le mot de passe contre la base de données
- Rejette la modification si le mot de passe est incorrect

### 3. Interface Utilisateur
- Bloc rouge "Confirmation de sécurité requise" avec icône cadenas
- Champ de mot de passe obligatoire pour chaque upload
- Message d'erreur clair si le mot de passe est incorrect

## Fichiers modifiés

### 1. `core/forms.py`
Ajout du formulaire `ConfirmationMotDePasseForm`:
```python
class ConfirmationMotDePasseForm(forms.Form):
    """Formulaire de confirmation par mot de passe pour modifier la signature/sceau."""
    password = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(attrs={...}),
        help_text='Votre mot de passe est requis pour modifier la signature ou le sceau.',
    )
    
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
    
    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not self.user.check_password(password):
            raise forms.ValidationError('Mot de passe incorrect.')
        return password
```

### 2. `core/views.py`
Modification de la vue `profil_ministre()`:
```python
@login_required(login_url='/login/')
@_user_passes_test(est_ministre, login_url='/login/')
def profil_ministre(request):
    """
    Page de gestion du profil du Ministre (signature et sceau).
    Modification protégée par mot de passe.
    """
    # ...
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        
        # Vérifier le mot de passe avant toute modification
        if form_type in ['signature', 'sceau']:
            password_form = ConfirmationMotDePasseForm(request.user, request.POST)
            if not password_form.is_valid():
                messages.error(request, "Mot de passe incorrect. Modification annulée.")
                return redirect('core:profil_ministre')
        
        # Procéder à la modification si le mot de passe est correct
        if form_type == 'signature':
            if 'signature_image' in request.FILES:
                profil.signature_image = request.FILES['signature_image']
                profil.save()
                messages.success(request, "✓ Signature téléchargée avec succès!")
```

### 3. `templates/core/profil_ministre.html`
Ajout de blocs de confirmation par mot de passe:
```html
<!-- Confirmation par mot de passe -->
<div class="bg-red-50 border border-red-200 rounded-lg p-4">
    <p class="text-sm font-semibold text-red-800 mb-3">
        <i class="fa-solid fa-lock mr-2"></i>
        Confirmation de sécurité requise
    </p>
    <div>
        <label for="password_signature" class="block text-sm font-semibold text-slate-700 mb-2">
            Mot de passe
        </label>
        <input type="password" id="password_signature" name="password" 
               placeholder="Entrez votre mot de passe pour confirmer"
               class="block w-full px-4 py-2 border border-slate-300 rounded-lg..."
               required>
        <p class="text-xs text-slate-500 mt-1">
            Votre mot de passe est requis pour modifier la signature (protection d'État)
        </p>
    </div>
</div>
```

## Flux de sécurité

1. **Accès au profil**: Ministre accède à `/minister/profil/`
2. **Sélection du fichier**: Choisit une nouvelle signature ou sceau
3. **Entrée du mot de passe**: Doit entrer son mot de passe pour confirmer
4. **Validation**: Le système vérifie le mot de passe
5. **Modification**: Si correct, la signature/sceau est mise à jour
6. **Rejet**: Si incorrect, la modification est annulée avec message d'erreur

## Messages de feedback

- ✓ **Succès**: "✓ Signature téléchargée avec succès!"
- ✗ **Erreur mot de passe**: "Mot de passe incorrect. Modification annulée."
- ✗ **Pas de fichier**: "Veuillez sélectionner un fichier."

## Avantages de sécurité

✅ **Protection contre les accès non autorisés**: Seul le Ministre peut modifier
✅ **Audit trail**: Chaque modification nécessite une authentification
✅ **Prévention des modifications accidentelles**: Confirmation explicite requise
✅ **Conformité d'État**: Signature et sceau sont des documents officiels protégés
✅ **Facilité d'utilisation**: Interface claire et intuitive

## Recommandations

1. **Mot de passe fort**: Assurez-vous que le Ministre utilise un mot de passe robuste
2. **Accès sécurisé**: Limitez l'accès au profil du Ministre à des connexions sécurisées
3. **Audit**: Envisager d'ajouter un log des modifications de signature/sceau
4. **Rotation**: Envisager une rotation périodique de la signature/sceau

