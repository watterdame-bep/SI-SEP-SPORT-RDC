// Gestion du formulaire de création de fédération
document.addEventListener('DOMContentLoaded', function() {
    
    // Gestion des étapes
    let currentStep = 1;
    const totalSteps = 5;
    const STORAGE_KEY = 'federation_form_data';
    const STORAGE_STEP_KEY = 'federation_form_step';
    
    function showStep(step) {
        // Cacher toutes les étapes
        document.querySelectorAll('.form-step').forEach(el => {
            el.classList.remove('active');
        });
        
        // Afficher l'étape courante
        const currentStepEl = document.querySelector(`.form-step[data-step="${step}"]`);
        if (currentStepEl) {
            currentStepEl.classList.add('active');
        }
        
        // Mettre à jour les indicateurs
        document.querySelectorAll('.step-item').forEach((item, index) => {
            const stepNum = index + 1;
            item.classList.remove('active', 'completed', 'pending');
            
            if (stepNum < step) {
                item.classList.add('completed');
                item.querySelector('.step-circle').innerHTML = '<i class="fa-solid fa-check"></i>';
            } else if (stepNum === step) {
                item.classList.add('active');
                item.querySelector('.step-circle').textContent = stepNum;
            } else {
                item.classList.add('pending');
                item.querySelector('.step-circle').textContent = stepNum;
            }
        });
        
        // Sauvegarder l'étape courante
        localStorage.setItem(STORAGE_STEP_KEY, step.toString());
        
        // Scroll vers le haut
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
    
    // Sauvegarder les données du formulaire
    function saveFormData() {
        const formData = {};
        const form = document.getElementById('form-federation');
        if (!form) return;
        
        const formElements = form.querySelectorAll('input:not([type="file"]), select, textarea');
        
        formElements.forEach(field => {
            if (field.name) {
                if (field.type === 'checkbox' || field.type === 'radio') {
                    formData[field.name] = field.checked;
                } else {
                    formData[field.name] = field.value;
                }
            }
        });
        
        localStorage.setItem(STORAGE_KEY, JSON.stringify(formData));
        localStorage.setItem(STORAGE_STEP_KEY, currentStep.toString());
        console.log('Données sauvegardées:', Object.keys(formData).length, 'champs');
    }
    
    // Restaurer l'étape et les données sauvegardées
    function restoreFormData() {
        const savedStep = localStorage.getItem(STORAGE_STEP_KEY);
        const savedData = localStorage.getItem(STORAGE_KEY);
        
        console.log('Restauration - Étape sauvegardée:', savedStep);
        console.log('Restauration - Données sauvegardées:', savedData ? 'Oui' : 'Non');
        
        if (savedStep) {
            currentStep = parseInt(savedStep);
            showStep(currentStep);
        }
        
        if (savedData) {
            try {
                const formData = JSON.parse(savedData);
                console.log('Restauration de', Object.keys(formData).length, 'champs');
                
                Object.keys(formData).forEach(fieldName => {
                    const field = document.querySelector(`[name="${fieldName}"]`);
                    if (field) {
                        if (field.type === 'file') {
                            // On ne peut pas restaurer les fichiers
                        } else if (field.type === 'checkbox' || field.type === 'radio') {
                            field.checked = formData[fieldName];
                        } else {
                            field.value = formData[fieldName];
                        }
                        console.log('Restauré:', fieldName, '=', formData[fieldName]);
                    }
                });
                console.log('Données du formulaire restaurées avec succès');
            } catch (e) {
                console.error('Erreur lors de la restauration des données:', e);
            }
        }
    }
    
    // Sauvegarder automatiquement à chaque changement
    const form = document.getElementById('form-federation');
    if (form) {
        form.addEventListener('input', function(e) {
            console.log('Input event sur:', e.target.name);
            saveFormData();
        });
        form.addEventListener('change', function(e) {
            console.log('Change event sur:', e.target.name);
            saveFormData();
        });
    }
    
    // Restaurer les données au chargement (APRÈS avoir défini showStep)
    restoreFormData();
    
    // Boutons Suivant
    document.querySelectorAll('.btn-next').forEach(btn => {
        btn.addEventListener('click', function() {
            if (validateCurrentStep()) {
                if (currentStep < totalSteps) {
                    currentStep++;
                    showStep(currentStep);
                }
            }
        });
    });
    
    // Définir les champs obligatoires par étape
    const stepRequiredFields = {
        1: ['code', 'numero_dossier', 'nom_officiel', 'sigle', 'disciplines', 'type_institution'],
        2: ['telephone_off', 'email_officiel'],
        3: ['type_agrement_sollicite', 'date_demande_agrement', 'provinces_implantation'],
        4: ['nom_president', 'telephone_president'],
        5: ['document_statuts', 'document_pv_ag', 'document_liste_membres']
    };
    
    // Validation de l'étape courante
    function validateCurrentStep() {
        console.log('Validation de l\'étape:', currentStep);
        
        // Récupérer les noms des champs obligatoires pour cette étape
        const requiredFieldNames = stepRequiredFields[currentStep] || [];
        console.log('Champs obligatoires pour l\'étape', currentStep, ':', requiredFieldNames);
        
        let isValid = true;
        let emptyFields = [];
        
        requiredFieldNames.forEach(fieldName => {
            // Traitement spécial pour provinces_implantation
            if (fieldName === 'provinces_implantation') {
                const checkboxes = document.querySelectorAll('input[name="provinces_implantation"]:checked');
                const provincesError = document.getElementById('provinces-error');
                
                if (checkboxes.length < 6) {
                    isValid = false;
                    if (provincesError) {
                        provincesError.classList.remove('hidden');
                    }
                    emptyFields.push('Provinces d\'implantation (minimum 6)');
                } else {
                    if (provincesError) {
                        provincesError.classList.add('hidden');
                    }
                }
                return;
            }
            
            // Trouver le champ par son nom
            const field = document.querySelector(`[name="${fieldName}"]`);
            if (!field) {
                console.log('Champ non trouvé:', fieldName);
                return;
            }
            
            // Retirer les styles d'erreur précédents
            field.classList.remove('border-rdc-red', 'border-2');
            
            // Vérifier si le champ est vide
            let isEmpty = false;
            const fieldValue = field.value ? field.value.trim() : '';
            
            if (field.type === 'hidden') {
                isEmpty = !fieldValue;
            } else if (field.tagName === 'SELECT') {
                isEmpty = !fieldValue || fieldValue === '';
            } else if (field.type === 'file') {
                isEmpty = !field.files || field.files.length === 0;
            } else {
                isEmpty = !fieldValue;
            }
            
            console.log('Champ:', fieldName, 'Vide:', isEmpty, 'Valeur:', fieldValue);
            
            if (isEmpty) {
                isValid = false;
                
                // Ne marquer en rouge que les champs visibles
                if (field.type !== 'hidden') {
                    field.classList.add('border-rdc-red', 'border-2');
                }
                
                // Récupérer le label du champ
                const parentDiv = field.closest('div');
                const label = parentDiv ? parentDiv.querySelector('label') : null;
                if (label) {
                    let labelText = label.textContent || label.innerText || '';
                    labelText = labelText.replace(/\*/g, '').trim();
                    labelText = labelText.replace(/\s+/g, ' ').trim();
                    if (labelText && !emptyFields.includes(labelText)) {
                        emptyFields.push(labelText);
                    }
                }
            }
        });
        
        console.log('Validation résultat:', isValid, 'Champs vides:', emptyFields);
        
        if (!isValid) {
            showMessage(
                `Veuillez remplir tous les champs obligatoires avant de continuer. Champs manquants : ${emptyFields.slice(0, 3).join(', ')}${emptyFields.length > 3 ? '...' : ''}`,
                'error'
            );
            
            // Scroll vers le premier champ vide
            const firstEmptyFieldName = requiredFieldNames.find(name => {
                if (name === 'provinces_implantation') {
                    return document.querySelectorAll('input[name="provinces_implantation"]:checked').length < 6;
                }
                const field = document.querySelector(`[name="${name}"]`);
                return field && field.classList.contains('border-rdc-red');
            });
            
            if (firstEmptyFieldName) {
                if (firstEmptyFieldName === 'provinces_implantation') {
                    const provincesSection = document.querySelector('label:has(input[name="provinces_implantation"])');
                    if (provincesSection) {
                        provincesSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                } else {
                    const firstEmptyField = document.querySelector(`[name="${firstEmptyFieldName}"]`);
                    if (firstEmptyField && firstEmptyField.type !== 'hidden') {
                        firstEmptyField.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        setTimeout(() => firstEmptyField.focus(), 300);
                    }
                }
            }
        }
        
        return isValid;
    }
    
    // Retirer les bordures rouges quand l'utilisateur commence à remplir
    document.querySelectorAll('[required]').forEach(field => {
        field.addEventListener('input', function() {
            if (this.value && this.value.trim() !== '') {
                this.classList.remove('border-rdc-red', 'border-2');
            }
        });
        
        field.addEventListener('change', function() {
            if (this.value && this.value.trim() !== '') {
                this.classList.remove('border-rdc-red', 'border-2');
            }
        });
    });
    
    // Gestion des provinces d'implantation
    const provincesCheckboxes = document.querySelectorAll('input[name="provinces_implantation"]');
    provincesCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const checkedCount = document.querySelectorAll('input[name="provinces_implantation"]:checked').length;
            const provincesError = document.getElementById('provinces-error');
            
            if (checkedCount >= 6) {
                if (provincesError) {
                    provincesError.classList.add('hidden');
                }
            }
        });
    });
    
    // Boutons Précédent
    document.querySelectorAll('.btn-prev').forEach(btn => {
        btn.addEventListener('click', function() {
            if (currentStep > 1) {
                currentStep--;
                showStep(currentStep);
            }
        });
    });
    
    // Clic sur les indicateurs d'étapes
    document.querySelectorAll('.step-item').forEach((item, index) => {
        item.addEventListener('click', function() {
            const targetStep = index + 1;
            // Permettre de revenir en arrière uniquement
            if (targetStep <= currentStep) {
                currentStep = targetStep;
                showStep(currentStep);
            }
        });
    });
    
    // État des documents obligatoires
    const requiredDocs = {
        'doc-statuts': false,
        'doc-pv': false,
        'doc-membres': false
    };
    
    // Gérer l'upload de fichiers
    const uploadInputs = document.querySelectorAll('.upload-input');
    
    uploadInputs.forEach(input => {
        const container = input.closest('.upload-box');
        const filesDiv = container.querySelector('.upload-files');
        const inputId = input.id;
        
        // Changement de fichier
        input.addEventListener('change', function(e) {
            displayFiles(inputId, this.files, filesDiv);
            checkRequiredDocuments();
        });
        
        // Drag & Drop
        container.addEventListener('dragover', function(e) {
            e.preventDefault();
            this.style.borderColor = '#0036ca';
            this.style.background = 'linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%)';
        });
        
        container.addEventListener('dragleave', function(e) {
            e.preventDefault();
            this.style.borderColor = '';
            this.style.background = '';
        });
        
        container.addEventListener('drop', function(e) {
            e.preventDefault();
            this.style.borderColor = '';
            this.style.background = '';
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                // Assigner les fichiers à l'input
                input.files = files;
                displayFiles(inputId, files, filesDiv);
                checkRequiredDocuments();
            }
        });
    });
    
    // Afficher les fichiers
    function displayFiles(inputId, files, container) {
        if (files.length === 0) {
            container.innerHTML = '';
            container.classList.remove('has-files');
            return;
        }
        
        container.classList.add('has-files');
        container.innerHTML = '';
        
        Array.from(files).forEach((file, index) => {
            const badge = document.createElement('div');
            badge.className = 'file-badge';
            badge.innerHTML = `
                <div class="file-info">
                    <i class="fa-solid fa-file-pdf text-rdc-red"></i>
                    <span class="file-name">${file.name}</span>
                    <span class="file-size">(${(file.size / 1024).toFixed(1)} KB)</span>
                </div>
                <button type="button" class="file-remove" onclick="removeFile('${inputId}', ${index})">
                    <i class="fa-solid fa-times"></i>
                </button>
            `;
            container.appendChild(badge);
        });
        
        // Marquer comme chargé si c'est un document obligatoire
        if (requiredDocs.hasOwnProperty(inputId)) {
            requiredDocs[inputId] = true;
        }
    }
    
    // Supprimer un fichier
    window.removeFile = function(inputId, index) {
        const input = document.getElementById(inputId);
        const container = input.closest('.upload-box').querySelector('.upload-files');
        
        // Créer un nouveau FileList sans le fichier supprimé
        const dt = new DataTransfer();
        const files = Array.from(input.files);
        files.splice(index, 1);
        files.forEach(file => dt.items.add(file));
        input.files = dt.files;
        
        // Réafficher
        displayFiles(inputId, input.files, container);
        
        // Mettre à jour l'état
        if (requiredDocs.hasOwnProperty(inputId)) {
            requiredDocs[inputId] = input.files.length > 0;
        }
        
        checkRequiredDocuments();
    };
    
    // Vérifier si tous les documents obligatoires sont chargés
    function checkRequiredDocuments() {
        const allUploaded = requiredDocs['doc-statuts'] && 
                            requiredDocs['doc-pv'] && 
                            requiredDocs['doc-membres'];
        
        const btnSubmit = document.getElementById('btn-submit');
        const validationMessage = document.getElementById('validation-message');
        
        if (allUploaded) {
            btnSubmit.disabled = false;
            btnSubmit.classList.remove('bg-slate-300', 'text-slate-500', 'cursor-not-allowed');
            btnSubmit.classList.add('bg-rdc-blue', 'hover:bg-rdc-blue-hover', 'text-white', 'cursor-pointer');
            if (validationMessage) validationMessage.classList.add('hidden');
        } else {
            btnSubmit.disabled = true;
            btnSubmit.classList.add('bg-slate-300', 'text-slate-500', 'cursor-not-allowed');
            btnSubmit.classList.remove('bg-rdc-blue', 'hover:bg-rdc-blue-hover', 'text-white', 'cursor-pointer');
            if (validationMessage) validationMessage.classList.remove('hidden');
        }
    }
    
    // Afficher un message
    window.showMessage = function(message, type = 'success') {
        const container = document.getElementById('message-container');
        const alertClass = type === 'success' ? 'bg-green-50 border-green-400 text-green-800' : 'bg-red-50 border-red-400 text-red-800';
        const iconClass = type === 'success' ? 'fa-check-circle text-green-400' : 'fa-exclamation-circle text-red-400';
        
        const alert = document.createElement('div');
        alert.className = `${alertClass} border-l-4 p-4 rounded-lg flex items-start gap-3`;
        alert.innerHTML = `
            <i class="fa-solid ${iconClass} text-xl mt-0.5"></i>
            <div class="flex-1">
                <p class="text-sm font-semibold">${message}</p>
            </div>
            <button onclick="this.parentElement.remove()" class="text-current opacity-50 hover:opacity-100">
                <i class="fa-solid fa-times"></i>
            </button>
        `;
        
        container.appendChild(alert);
        window.scrollTo({ top: 0, behavior: 'smooth' });
        setTimeout(() => alert.remove(), 8000);
    };
    
    // Cascade géographique
    const provinceSelect = document.getElementById('province-select');
    if (provinceSelect) {
        provinceSelect.addEventListener('change', async function() {
            const provinceId = this.value;
            const territoireSelect = document.getElementById('territoire-select');
            const secteurSelect = document.getElementById('secteur-select');
            const groupementSelect = document.getElementById('groupement-select');
            
            territoireSelect.innerHTML = '<option value="">Chargement...</option>';
            secteurSelect.innerHTML = '<option value="">Sélectionner d\'abord un territoire</option>';
            groupementSelect.innerHTML = '<option value="">Sélectionner d\'abord un secteur</option>';
            secteurSelect.disabled = true;
            groupementSelect.disabled = true;
            
            if (!provinceId) {
                territoireSelect.innerHTML = '<option value="">Sélectionner d\'abord une province</option>';
                territoireSelect.disabled = true;
                return;
            }
            
            try {
                const response = await fetch(`/parametres-geographiques/api/territoires/?province=${provinceId}`);
                const data = await response.json();
                
                territoireSelect.innerHTML = '<option value="">Sélectionner un territoire</option>';
                data.forEach(territoire => {
                    const option = document.createElement('option');
                    option.value = territoire.uid;
                    option.textContent = territoire.designation;
                    territoireSelect.appendChild(option);
                });
                
                territoireSelect.disabled = false;
            } catch (error) {
                console.error('Erreur:', error);
                territoireSelect.innerHTML = '<option value="">Erreur de chargement</option>';
            }
        });
    }
    
    const territoireSelect = document.getElementById('territoire-select');
    if (territoireSelect) {
        territoireSelect.addEventListener('change', async function() {
            const territoireId = this.value;
            const secteurSelect = document.getElementById('secteur-select');
            const groupementSelect = document.getElementById('groupement-select');
            
            secteurSelect.innerHTML = '<option value="">Chargement...</option>';
            groupementSelect.innerHTML = '<option value="">Sélectionner d\'abord un secteur</option>';
            groupementSelect.disabled = true;
            
            if (!territoireId) {
                secteurSelect.innerHTML = '<option value="">Sélectionner d\'abord un territoire</option>';
                secteurSelect.disabled = true;
                return;
            }
            
            try {
                const response = await fetch(`/parametres-geographiques/api/secteurs/?territoire=${territoireId}`);
                const data = await response.json();
                
                secteurSelect.innerHTML = '<option value="">Sélectionner un secteur</option>';
                data.forEach(secteur => {
                    const option = document.createElement('option');
                    option.value = secteur.uid;
                    option.textContent = secteur.designation;
                    secteurSelect.appendChild(option);
                });
                
                secteurSelect.disabled = false;
            } catch (error) {
                console.error('Erreur:', error);
                secteurSelect.innerHTML = '<option value="">Erreur de chargement</option>';
            }
        });
    }
    
    const secteurSelect = document.getElementById('secteur-select');
    if (secteurSelect) {
        secteurSelect.addEventListener('change', async function() {
            const secteurId = this.value;
            const groupementSelect = document.getElementById('groupement-select');
            
            groupementSelect.innerHTML = '<option value="">Chargement...</option>';
            
            if (!secteurId) {
                groupementSelect.innerHTML = '<option value="">Sélectionner d\'abord un secteur</option>';
                groupementSelect.disabled = true;
                return;
            }
            
            try {
                const response = await fetch(`/parametres-geographiques/api/groupements/?secteur=${secteurId}`);
                const data = await response.json();
                
                groupementSelect.innerHTML = '<option value="">Sélectionner un groupement</option>';
                data.forEach(groupement => {
                    const option = document.createElement('option');
                    option.value = groupement.uid;
                    option.textContent = groupement.designation;
                    groupementSelect.appendChild(option);
                });
                
                groupementSelect.disabled = false;
            } catch (error) {
                console.error('Erreur:', error);
                groupementSelect.innerHTML = '<option value="">Erreur de chargement</option>';
            }
        });
    }
    
    // Soumission du formulaire
    const formFederation = document.getElementById('form-federation');
    if (formFederation) {
        formFederation.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const btnSubmit = document.getElementById('btn-submit');
            const originalText = btnSubmit.innerHTML;
            
            btnSubmit.disabled = true;
            btnSubmit.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> <span>Enregistrement en cours...</span>';
            
            try {
                const formData = new FormData(this);
                
                const response = await fetch('/gouvernance/federations/store/', {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken')
                    }
                });
                
                const data = await response.json();
                
                if (data.success) {
                    // Effacer les données sauvegardées
                    localStorage.removeItem(STORAGE_KEY);
                    localStorage.removeItem(STORAGE_STEP_KEY);
                    
                    showMessage(data.message, 'success');
                    setTimeout(() => {
                        window.location.href = data.redirect_url;
                    }, 2000);
                } else {
                    showMessage(data.message, 'error');
                    btnSubmit.disabled = false;
                    btnSubmit.innerHTML = originalText;
                }
            } catch (error) {
                console.error('Erreur:', error);
                showMessage('Une erreur est survenue lors de l\'enregistrement', 'error');
                btnSubmit.disabled = false;
                btnSubmit.innerHTML = originalText;
            }
        });
    }
    
    // Fonction utilitaire pour récupérer le cookie CSRF
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    // Bouton pour effacer les données sauvegardées (optionnel)
    window.clearSavedFormData = function() {
        if (confirm('Êtes-vous sûr de vouloir effacer toutes les données du formulaire ?')) {
            localStorage.removeItem(STORAGE_KEY);
            localStorage.removeItem(STORAGE_STEP_KEY);
            window.location.reload();
        }
    };
    
    console.log('Federation form initialized');
});
