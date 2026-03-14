// Éditer une province
function editProvince(id) {
    const province = allProvinces.find(p => p.id === id || p.uid === id);
    if (!province) return;
    
    document.getElementById('modal-title').textContent = 'Modifier la province';
    
    // Masquer tous les selects
    document.getElementById('province-select-container').classList.add('hidden');
    document.getElementById('territoire-select-container').classList.add('hidden');
    document.getElementById('secteur-select-container').classList.add('hidden');
    document.getElementById('province-select').required = false;
    document.getElementById('territoire-select').required = false;
    document.getElementById('secteur-select').required = false;
    
    document.getElementById('modal-province').classList.remove('hidden');
    
    // Pré-remplir le formulaire
    document.querySelector('[name="designation"]').value = province.designation || '';
    document.querySelector('[name="code"]').value = province.code || '';
    document.querySelector('[name="description"]').value = province.description || '';
    
    // Modifier l'action du formulaire
    const form = document.getElementById('form-province');
    form.removeEventListener('submit', handleFormSubmit);
    
    const updateHandler = function(e) {
        e.preventDefault();
        const formData = new FormData(form);
        
        fetch(`/parametres-geographiques/province/${id}/update/`, {
            method: 'POST',
            headers: {'X-CSRFToken': getCookie('csrftoken')},
            body: formData
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                closeModal('modal-province');
                showMessage(data.message, 'success');
                setTimeout(() => window.location.reload(), 500);
            } else {
                showMessage('Erreur: ' + JSON.stringify(data.errors), 'error');
            }
        });
    };
    
    form._customSubmitHandler = updateHandler;
    form.addEventListener('submit', updateHandler);
}

// Éditer un territoire
function editTerritoire(id) {
    fetch(`/parametres-geographiques/territoire/${id}/detail/`)
        .then(r => r.json())
        .then(territoire => {
            document.getElementById('modal-title').textContent = 'Modifier le territoire';
            
            // Masquer tous les selects
            document.getElementById('province-select-container').classList.add('hidden');
            document.getElementById('territoire-select-container').classList.add('hidden');
            document.getElementById('secteur-select-container').classList.add('hidden');
            document.getElementById('province-select').required = false;
            document.getElementById('territoire-select').required = false;
            document.getElementById('secteur-select').required = false;
            
            // Afficher uniquement le select province
            const provinceSelect = document.getElementById('province-select-container');
            provinceSelect.classList.remove('hidden');
            document.getElementById('province-select').required = true;
            
            const select = document.getElementById('province-select');
            select.innerHTML = '<option value="">Sélectionner une province</option>' + 
                allProvinces.map(p => `<option value="${p.id}" ${p.id === territoire.province_id ? 'selected' : ''}>${p.designation}</option>`).join('');
            
            // Pré-remplir le formulaire
            document.querySelector('[name="designation"]').value = territoire.designation || '';
            document.querySelector('[name="code"]').value = territoire.code || '';
            document.querySelector('[name="description"]').value = territoire.description || '';
            
            document.getElementById('modal-province').classList.remove('hidden');
            
            // Modifier l'action du formulaire
            const form = document.getElementById('form-province');
            form.removeEventListener('submit', handleFormSubmit);
            
            const updateHandler = function(e) {
                e.preventDefault();
                const formData = new FormData(form);
                
                fetch(`/parametres-geographiques/territoire/${id}/update/`, {
                    method: 'POST',
                    headers: {'X-CSRFToken': getCookie('csrftoken')},
                    body: formData
                })
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        closeModal('modal-province');
                        showMessage(data.message, 'success');
                        setTimeout(() => window.location.reload(), 500);
                    } else {
                        showMessage('Erreur: ' + JSON.stringify(data.errors), 'error');
                    }
                });
            };
            
            form._customSubmitHandler = updateHandler;
            form.addEventListener('submit', updateHandler);
        });
}

// Éditer un secteur
function editSecteur(id) {
    fetch(`/parametres-geographiques/secteur/${id}/detail/`)
        .then(r => r.json())
        .then(secteur => {
            document.getElementById('modal-title').textContent = 'Modifier le secteur';
            
            // Masquer tous les selects
            document.getElementById('province-select-container').classList.add('hidden');
            document.getElementById('territoire-select-container').classList.add('hidden');
            document.getElementById('secteur-select-container').classList.add('hidden');
            document.getElementById('province-select').required = false;
            document.getElementById('territoire-select').required = false;
            document.getElementById('secteur-select').required = false;
            
            // Afficher uniquement le select territoire
            const territoireSelect = document.getElementById('territoire-select-container');
            territoireSelect.classList.remove('hidden');
            document.getElementById('territoire-select').required = true;
            
            // Charger tous les territoires et pré-sélectionner
            loadTerritoiresForSelect(() => {
                document.getElementById('territoire-select').value = secteur.territoire_id;
            });
            
            // Pré-remplir le formulaire
            document.querySelector('[name="designation"]').value = secteur.designation || '';
            document.querySelector('[name="description"]').value = secteur.description || '';
            
            document.getElementById('modal-province').classList.remove('hidden');
            
            // Modifier l'action du formulaire
            const form = document.getElementById('form-province');
            form.removeEventListener('submit', handleFormSubmit);
            
            const updateHandler = function(e) {
                e.preventDefault();
                const formData = new FormData(form);
                
                fetch(`/parametres-geographiques/secteur/${id}/update/`, {
                    method: 'POST',
                    headers: {'X-CSRFToken': getCookie('csrftoken')},
                    body: formData
                })
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        closeModal('modal-province');
                        showMessage(data.message, 'success');
                        setTimeout(() => window.location.reload(), 500);
                    } else {
                        showMessage('Erreur: ' + JSON.stringify(data.errors), 'error');
                    }
                });
            };
            
            form._customSubmitHandler = updateHandler;
            form.addEventListener('submit', updateHandler);
        });
}

// Éditer un groupement
function editGroupement(id) {
    fetch(`/parametres-geographiques/groupement/${id}/detail/`)
        .then(r => r.json())
        .then(groupement => {
            document.getElementById('modal-title').textContent = 'Modifier le groupement';
            
            // Masquer tous les selects
            document.getElementById('province-select-container').classList.add('hidden');
            document.getElementById('territoire-select-container').classList.add('hidden');
            document.getElementById('secteur-select-container').classList.add('hidden');
            document.getElementById('province-select').required = false;
            document.getElementById('territoire-select').required = false;
            document.getElementById('secteur-select').required = false;
            
            // Afficher uniquement le select secteur
            const secteurSelect = document.getElementById('secteur-select-container');
            secteurSelect.classList.remove('hidden');
            document.getElementById('secteur-select').required = true;
            
            // Charger tous les secteurs et pré-sélectionner
            loadSecteursForSelect(() => {
                document.getElementById('secteur-select').value = groupement.secteur_id;
            });
            
            // Pré-remplir le formulaire
            document.querySelector('[name="designation"]').value = groupement.designation || '';
            document.querySelector('[name="description"]').value = groupement.description || '';
            
            document.getElementById('modal-province').classList.remove('hidden');
            
            // Modifier l'action du formulaire
            const form = document.getElementById('form-province');
            form.removeEventListener('submit', handleFormSubmit);
            
            const updateHandler = function(e) {
                e.preventDefault();
                const formData = new FormData(form);
                
                fetch(`/parametres-geographiques/groupement/${id}/update/`, {
                    method: 'POST',
                    headers: {'X-CSRFToken': getCookie('csrftoken')},
                    body: formData
                })
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        closeModal('modal-province');
                        showMessage(data.message, 'success');
                        setTimeout(() => window.location.reload(), 500);
                    } else {
                        showMessage('Erreur: ' + JSON.stringify(data.errors), 'error');
                    }
                });
            };
            
            form._customSubmitHandler = updateHandler;
            form.addEventListener('submit', updateHandler);
        });
}

// Supprimer un groupement
function deleteGroupement(id) {
    document.getElementById('confirm-message').textContent = 'Êtes-vous sûr de vouloir supprimer ce groupement ?';
    document.getElementById('modal-confirm').classList.remove('hidden');
    deleteCallback = function() {
        fetch(`/parametres-geographiques/groupement/${id}/delete/`, {
            method: 'POST',
            headers: {'X-CSRFToken': getCookie('csrftoken')}
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                showMessage(data.message, 'success');
                loadGroupements();
            } else {
                showMessage(data.message, 'error');
            }
        })
        .catch(err => {
            showMessage('Erreur lors de la suppression', 'error');
        });
    };
}

// Supprimer un secteur
function deleteSecteur(id) {
    document.getElementById('confirm-message').textContent = 'Êtes-vous sûr de vouloir supprimer ce secteur ?';
    document.getElementById('modal-confirm').classList.remove('hidden');
    deleteCallback = function() {
        fetch(`/parametres-geographiques/secteur/${id}/delete/`, {
            method: 'POST',
            headers: {'X-CSRFToken': getCookie('csrftoken')},
            body: new URLSearchParams({force_delete: 'false'})
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                showMessage(data.message, 'success');
                loadSecteurs();
            } else if (data.has_children) {
                document.getElementById('confirm-message').textContent = data.message;
                document.getElementById('modal-confirm').classList.remove('hidden');
                deleteCallback = function() {
                    fetch(`/parametres-geographiques/secteur/${id}/delete/`, {
                        method: 'POST',
                        headers: {'X-CSRFToken': getCookie('csrftoken')},
                        body: new URLSearchParams({force_delete: 'true'})
                    })
                    .then(r => r.json())
                    .then(data => {
                        if (data.success) {
                            showMessage(data.message, 'success');
                            loadSecteurs();
                        } else {
                            showMessage(data.message, 'error');
                        }
                    });
                };
            } else {
                showMessage(data.message, 'error');
            }
        })
        .catch(err => {
            showMessage('Erreur lors de la suppression', 'error');
        });
    };
}

// Supprimer un territoire
function deleteTerritoire(id) {
    document.getElementById('confirm-message').textContent = 'Êtes-vous sûr de vouloir supprimer ce territoire ?';
    document.getElementById('modal-confirm').classList.remove('hidden');
    deleteCallback = function() {
        fetch(`/parametres-geographiques/territoire/${id}/delete/`, {
            method: 'POST',
            headers: {'X-CSRFToken': getCookie('csrftoken')},
            body: new URLSearchParams({force_delete: 'false'})
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                showMessage(data.message, 'success');
                loadTerritoires();
            } else if (data.has_children) {
                document.getElementById('confirm-message').textContent = data.message;
                document.getElementById('modal-confirm').classList.remove('hidden');
                deleteCallback = function() {
                    fetch(`/parametres-geographiques/territoire/${id}/delete/`, {
                        method: 'POST',
                        headers: {'X-CSRFToken': getCookie('csrftoken')},
                        body: new URLSearchParams({force_delete: 'true'})
                    })
                    .then(r => r.json())
                    .then(data => {
                        if (data.success) {
                            showMessage(data.message, 'success');
                            loadTerritoires();
                        } else {
                            showMessage(data.message, 'error');
                        }
                    });
                };
            } else {
                showMessage(data.message, 'error');
            }
        })
        .catch(err => {
            showMessage('Erreur lors de la suppression', 'error');
        });
    };
}

// Supprimer une province
function deleteProvince(id) {
    document.getElementById('confirm-message').textContent = 'Êtes-vous sûr de vouloir supprimer cette province ?';
    document.getElementById('modal-confirm').classList.remove('hidden');
    deleteCallback = function() {
        fetch(`/parametres-geographiques/province/${id}/delete/`, {
            method: 'POST',
            headers: {'X-CSRFToken': getCookie('csrftoken')},
            body: new URLSearchParams({force_delete: 'false'})
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                showMessage(data.message, 'success');
                allProvinces = allProvinces.filter(p => p.id !== id);
                loadProvinces();
            } else if (data.has_children) {
                document.getElementById('confirm-message').textContent = data.message;
                document.getElementById('modal-confirm').classList.remove('hidden');
                deleteCallback = function() {
                    fetch(`/parametres-geographiques/province/${id}/delete/`, {
                        method: 'POST',
                        headers: {'X-CSRFToken': getCookie('csrftoken')},
                        body: new URLSearchParams({force_delete: 'true'})
                    })
                    .then(r => r.json())
                    .then(data => {
                        if (data.success) {
                            showMessage(data.message, 'success');
                            allProvinces = allProvinces.filter(p => p.id !== id);
                            loadProvinces();
                        } else {
                            showMessage(data.message, 'error');
                        }
                    });
                };
            } else {
                showMessage(data.message, 'error');
            }
        })
        .catch(err => {
            showMessage('Erreur lors de la suppression', 'error');
        });
    };
}
