// Variables globales
let currentTab = 'provinces';
let deleteCallback = null;

// allProvinces sera initialisé depuis le template Django

// Initialisation
document.addEventListener('DOMContentLoaded', function() {
    loadProvinces();
    
    // Recherche en temps réel
    document.getElementById('search-input').addEventListener('input', function(e) {
        const term = e.target.value.toLowerCase();
        document.querySelectorAll('#table-body tr').forEach(row => {
            row.style.display = row.textContent.toLowerCase().includes(term) ? '' : 'none';
        });
    });
    
    // Gestionnaire de soumission du formulaire
    document.getElementById('form-province').addEventListener('submit', handleFormSubmit);
});

// Navigation entre onglets
function switchTab(tab) {
    currentTab = tab;
    document.querySelectorAll('[id^="tab-"]').forEach(t => {
        t.classList.remove('tab-active');
        t.classList.add('text-slate-600', 'border-transparent');
    });
    const activeTab = document.getElementById('tab-' + tab);
    activeTab.classList.add('tab-active');
    activeTab.classList.remove('text-slate-600', 'border-transparent');
    
    updateCreateButton();
    
    if (tab === 'provinces') loadProvinces();
    else if (tab === 'territoires') loadTerritoires();
    else if (tab === 'secteurs') loadSecteurs();
    else if (tab === 'groupements') loadGroupements();
}

// Mettre à jour le bouton de création
function updateCreateButton() {
    const labels = {
        provinces: 'Nouvelle province',
        territoires: 'Nouveau territoire',
        secteurs: 'Nouveau secteur',
        groupements: 'Nouveau groupement'
    };
    document.getElementById('btn-create-text').textContent = labels[currentTab];
    document.getElementById('modal-title').textContent = labels[currentTab];
}

// Charger les provinces
function loadProvinces() {
    document.getElementById('table-head').innerHTML = `
        <tr>
            <th class="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Province</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Territoires</th>
            <th class="px-4 py-3 text-center text-xs font-semibold text-slate-500 uppercase tracking-wider">Actions</th>
        </tr>
    `;
    
    if (allProvinces.length === 0) {
        document.getElementById('table-body').innerHTML = `
            <tr><td colspan="3" class="px-6 py-16 text-center">
                <i class="fa-solid fa-map text-4xl text-slate-300 mb-4"></i>
                <p class="text-base font-bold text-slate-900">Aucune province</p>
            </td></tr>
        `;
        return;
    }
    
    document.getElementById('table-body').innerHTML = allProvinces.map(p => `
        <tr class="hover:bg-slate-50/70 transition-colors">
            <td class="px-6 py-4">
                <div class="flex items-center gap-3">
                    <div class="h-10 w-10 rounded-xl bg-rdc-blue text-white flex items-center justify-center font-bold text-sm">
                        ${p.designation.substring(0, 2).toUpperCase()}
                    </div>
                    <div>
                        <div class="text-sm font-semibold text-slate-900">${p.designation}</div>
                        <div class="text-xs text-slate-500">Code: ${p.code || 'N/A'}</div>
                    </div>
                </div>
            </td>
            <td class="px-4 py-2.5 text-xs text-slate-500">${p.nb_territoires} territoire(s)</td>
            <td class="px-4 py-2.5 text-center">
                <button onclick="editProvince('${p.id}')" style="display:inline-flex;align-items:center;justify-content:center;width:32px;height:32px;color:#fff;background:#0036ca;border:none;border-radius:6px;cursor:pointer;" onmouseover="this.style.background='#002aaa'" onmouseout="this.style.background='#0036ca'" title="Modifier"><i class="fa-solid fa-pen text-xs"></i>
                </button>
                <button onclick="deleteProvince('${p.id}')" style="display:inline-flex;align-items:center;justify-content:center;width:32px;height:32px;color:#fff;background:#ED1C24;border:none;border-radius:6px;cursor:pointer;" onmouseover="this.style.background='#c0151b'" onmouseout="this.style.background='#ED1C24'" title="Supprimer"><i class="fa-solid fa-trash text-xs"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

// Charger les territoires
function loadTerritoires() {
    document.getElementById('table-head').innerHTML = `
        <tr>
            <th class="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Territoire/Ville</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Province</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Secteurs</th>
            <th class="px-4 py-3 text-center text-xs font-semibold text-slate-500 uppercase tracking-wider">Actions</th>
        </tr>
    `;
    
    document.getElementById('table-body').innerHTML = `
        <tr><td colspan="4" class="px-6 py-16 text-center">
            <i class="fa-solid fa-spinner fa-spin text-4xl text-slate-300 mb-4"></i>
            <p class="text-base font-bold text-slate-900">Chargement...</p>
        </td></tr>
    `;
    
    const promises = allProvinces.map(p => 
        fetch(`/parametres-geographiques/api/territoires/${p.id}/`)
            .then(r => r.json())
            .then(data => ({province: p, territoires: data.territoires}))
    );
    
    Promise.all(promises).then(results => {
        const allTerritoires = [];
        results.forEach(result => {
            result.territoires.forEach(t => {
                t.province = result.province;
                allTerritoires.push(t);
            });
        });
        
        if (allTerritoires.length === 0) {
            document.getElementById('table-body').innerHTML = `
                <tr><td colspan="4" class="px-6 py-16 text-center">
                    <i class="fa-solid fa-city text-4xl text-slate-300 mb-4"></i>
                    <p class="text-base font-bold text-slate-900">Aucun territoire</p>
                </td></tr>
            `;
            return;
        }
        
        document.getElementById('table-body').innerHTML = allTerritoires.map(t => `
            <tr class="hover:bg-slate-50/70 transition-colors">
                <td class="px-6 py-4">
                    <div class="flex items-center gap-3">
                        <div class="h-10 w-10 rounded-xl bg-blue-600 text-white flex items-center justify-center font-bold text-sm">
                            ${t.designation.substring(0, 2).toUpperCase()}
                        </div>
                        <div>
                            <div class="text-sm font-semibold text-slate-900">${t.designation}</div>
                            <div class="text-xs text-slate-500">Code: ${t.code || 'N/A'}</div>
                        </div>
                    </div>
                </td>
                <td class="px-4 py-2.5 text-xs text-slate-500">${t.province.designation}</td>
                <td class="px-4 py-2.5 text-xs text-slate-500">${t.nb_secteurs || 0} secteur(s)</td>
                <td class="px-4 py-2.5 text-center">
                    <button onclick="editTerritoire('${t.id}')" style="display:inline-flex;align-items:center;justify-content:center;width:32px;height:32px;color:#fff;background:#0036ca;border:none;border-radius:6px;cursor:pointer;" onmouseover="this.style.background='#002aaa'" onmouseout="this.style.background='#0036ca'" title="Modifier"><i class="fa-solid fa-pen text-xs"></i>
                    </button>
                    <button onclick="deleteTerritoire('${t.id}')" style="display:inline-flex;align-items:center;justify-content:center;width:32px;height:32px;color:#fff;background:#ED1C24;border:none;border-radius:6px;cursor:pointer;" onmouseover="this.style.background='#c0151b'" onmouseout="this.style.background='#ED1C24'" title="Supprimer"><i class="fa-solid fa-trash text-xs"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }).catch(err => {
        console.error('Erreur:', err);
        document.getElementById('table-body').innerHTML = `
            <tr><td colspan="4" class="px-6 py-16 text-center">
                <i class="fa-solid fa-exclamation-triangle text-4xl text-red-300 mb-4"></i>
                <p class="text-base font-bold text-slate-900">Erreur de chargement</p>
            </td></tr>
        `;
    });
}

// Charger les secteurs
function loadSecteurs() {
    document.getElementById('table-head').innerHTML = `
        <tr>
            <th class="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Secteur/Commune</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Territoire</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Groupements</th>
            <th class="px-4 py-3 text-center text-xs font-semibold text-slate-500 uppercase tracking-wider">Actions</th>
        </tr>
    `;
    
    document.getElementById('table-body').innerHTML = `
        <tr><td colspan="4" class="px-6 py-16 text-center">
            <i class="fa-solid fa-spinner fa-spin text-4xl text-slate-300 mb-4"></i>
            <p class="text-base font-bold text-slate-900">Chargement...</p>
        </td></tr>
    `;
    
    const promises = allProvinces.map(p => 
        fetch(`/parametres-geographiques/api/territoires/${p.id}/`)
            .then(r => r.json())
            .then(data => ({province: p, territoires: data.territoires}))
    );
    
    Promise.all(promises).then(results => {
        const allTerritoires = [];
        results.forEach(result => {
            result.territoires.forEach(t => {
                t.province = result.province;
                allTerritoires.push(t);
            });
        });
        
        const secteurPromises = allTerritoires.map(t =>
            fetch(`/parametres-geographiques/api/secteurs/${t.id}/`)
                .then(r => r.json())
                .then(data => ({territoire: t, secteurs: data.secteurs}))
        );
        
        Promise.all(secteurPromises).then(secteurResults => {
            const allSecteurs = [];
            secteurResults.forEach(result => {
                result.secteurs.forEach(s => {
                    s.territoire = result.territoire;
                    allSecteurs.push(s);
                });
            });
            
            if (allSecteurs.length === 0) {
                document.getElementById('table-body').innerHTML = `
                    <tr><td colspan="4" class="px-6 py-16 text-center">
                        <i class="fa-solid fa-building text-4xl text-slate-300 mb-4"></i>
                        <p class="text-base font-bold text-slate-900">Aucun secteur</p>
                    </td></tr>
                `;
                return;
            }
            
            document.getElementById('table-body').innerHTML = allSecteurs.map(s => `
                <tr class="hover:bg-slate-50/70 transition-colors">
                    <td class="px-6 py-4">
                        <div class="flex items-center gap-3">
                            <div class="h-10 w-10 rounded-xl bg-green-600 text-white flex items-center justify-center font-bold text-sm">
                                ${s.designation.substring(0, 2).toUpperCase()}
                            </div>
                            <div>
                                <div class="text-sm font-semibold text-slate-900">${s.designation}</div>
                                <div class="text-xs text-slate-500">${s.territoire.designation}</div>
                            </div>
                        </div>
                    </td>
                    <td class="px-4 py-2.5 text-xs text-slate-500">${s.territoire.designation}</td>
                    <td class="px-4 py-2.5 text-xs text-slate-500">${s.nb_groupements || 0} groupement(s)</td>
                    <td class="px-4 py-2.5 text-center">
                        <button onclick="editSecteur('${s.id}')" style="display:inline-flex;align-items:center;justify-content:center;width:32px;height:32px;color:#fff;background:#0036ca;border:none;border-radius:6px;cursor:pointer;" onmouseover="this.style.background='#002aaa'" onmouseout="this.style.background='#0036ca'" title="Modifier"><i class="fa-solid fa-pen text-xs"></i>
                        </button>
                        <button onclick="deleteSecteur('${s.id}')" style="display:inline-flex;align-items:center;justify-content:center;width:32px;height:32px;color:#fff;background:#ED1C24;border:none;border-radius:6px;cursor:pointer;" onmouseover="this.style.background='#c0151b'" onmouseout="this.style.background='#ED1C24'" title="Supprimer"><i class="fa-solid fa-trash text-xs"></i>
                        </button>
                    </td>
                </tr>
            `).join('');
        });
    }).catch(err => {
        console.error('Erreur:', err);
        document.getElementById('table-body').innerHTML = `
            <tr><td colspan="4" class="px-6 py-16 text-center">
                <i class="fa-solid fa-exclamation-triangle text-4xl text-red-300 mb-4"></i>
                <p class="text-base font-bold text-slate-900">Erreur de chargement</p>
            </td></tr>
        `;
    });
}

// Charger les groupements
function loadGroupements() {
    document.getElementById('table-head').innerHTML = `
        <tr>
            <th class="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Groupement/Quartier</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Secteur</th>
            <th class="px-4 py-3 text-center text-xs font-semibold text-slate-500 uppercase tracking-wider">Actions</th>
        </tr>
    `;
    
    document.getElementById('table-body').innerHTML = `
        <tr><td colspan="3" class="px-6 py-16 text-center">
            <i class="fa-solid fa-spinner fa-spin text-4xl text-slate-300 mb-4"></i>
            <p class="text-base font-bold text-slate-900">Chargement...</p>
        </td></tr>
    `;
    
    const promises = allProvinces.map(p => 
        fetch(`/parametres-geographiques/api/territoires/${p.id}/`)
            .then(r => r.json())
            .then(data => ({province: p, territoires: data.territoires}))
    );
    
    Promise.all(promises).then(results => {
        const allTerritoires = [];
        results.forEach(result => {
            result.territoires.forEach(t => {
                t.province = result.province;
                allTerritoires.push(t);
            });
        });
        
        const secteurPromises = allTerritoires.map(t =>
            fetch(`/parametres-geographiques/api/secteurs/${t.id}/`)
                .then(r => r.json())
                .then(data => ({territoire: t, secteurs: data.secteurs}))
        );
        
        Promise.all(secteurPromises).then(secteurResults => {
            const allSecteurs = [];
            secteurResults.forEach(result => {
                result.secteurs.forEach(s => {
                    s.territoire = result.territoire;
                    allSecteurs.push(s);
                });
            });
            
            const groupementPromises = allSecteurs.map(s =>
                fetch(`/parametres-geographiques/api/groupements/${s.id}/`)
                    .then(r => r.json())
                    .then(data => ({secteur: s, groupements: data.groupements}))
            );
            
            Promise.all(groupementPromises).then(groupementResults => {
                const allGroupements = [];
                groupementResults.forEach(result => {
                    result.groupements.forEach(g => {
                        g.secteur = result.secteur;
                        allGroupements.push(g);
                    });
                });
                
                if (allGroupements.length === 0) {
                    document.getElementById('table-body').innerHTML = `
                        <tr><td colspan="3" class="px-6 py-16 text-center">
                            <i class="fa-solid fa-location-dot text-4xl text-slate-300 mb-4"></i>
                            <p class="text-base font-bold text-slate-900">Aucun groupement</p>
                        </td></tr>
                    `;
                    return;
                }
                
                document.getElementById('table-body').innerHTML = allGroupements.map(g => `
                    <tr class="hover:bg-slate-50/70 transition-colors">
                        <td class="px-6 py-4">
                            <div class="flex items-center gap-3">
                                <div class="h-10 w-10 rounded-xl bg-amber-600 text-white flex items-center justify-center font-bold text-sm">
                                    ${g.designation.substring(0, 2).toUpperCase()}
                                </div>
                                <div>
                                    <div class="text-sm font-semibold text-slate-900">${g.designation}</div>
                                    <div class="text-xs text-slate-500">${g.secteur.designation}</div>
                                </div>
                            </div>
                        </td>
                        <td class="px-4 py-2.5 text-xs text-slate-500">${g.secteur.designation}</td>
                        <td class="px-4 py-2.5 text-center">
                            <button onclick="editGroupement('${g.id}')" style="display:inline-flex;align-items:center;justify-content:center;width:32px;height:32px;color:#fff;background:#0036ca;border:none;border-radius:6px;cursor:pointer;" onmouseover="this.style.background='#002aaa'" onmouseout="this.style.background='#0036ca'" title="Modifier"><i class="fa-solid fa-pen text-xs"></i>
                            </button>
                            <button onclick="deleteGroupement('${g.id}')" style="display:inline-flex;align-items:center;justify-content:center;width:32px;height:32px;color:#fff;background:#ED1C24;border:none;border-radius:6px;cursor:pointer;" onmouseover="this.style.background='#c0151b'" onmouseout="this.style.background='#ED1C24'" title="Supprimer"><i class="fa-solid fa-trash text-xs"></i>
                            </button>
                        </td>
                    </tr>
                `).join('');
            });
        });
    }).catch(err => {
        console.error('Erreur:', err);
        document.getElementById('table-body').innerHTML = `
            <tr><td colspan="3" class="px-6 py-16 text-center">
                <i class="fa-solid fa-exclamation-triangle text-4xl text-red-300 mb-4"></i>
                <p class="text-base font-bold text-slate-900">Erreur de chargement</p>
            </td></tr>
        `;
    });
}

// Ouvrir le modal de création
function openCreateModal() {
    const modal = document.getElementById('modal-province');
    const provinceSelect = document.getElementById('province-select-container');
    const territoireSelect = document.getElementById('territoire-select-container');
    const secteurSelect = document.getElementById('secteur-select-container');
    
    // Masquer tous les selects
    provinceSelect.classList.add('hidden');
    territoireSelect.classList.add('hidden');
    secteurSelect.classList.add('hidden');
    document.getElementById('province-select').required = false;
    document.getElementById('territoire-select').required = false;
    document.getElementById('secteur-select').required = false;
    
    // Afficher les selects selon l'onglet
    if (currentTab === 'territoires') {
        provinceSelect.classList.remove('hidden');
        document.getElementById('province-select').required = true;
        const select = document.getElementById('province-select');
        select.innerHTML = '<option value="">Sélectionner une province</option>' + 
            allProvinces.map(p => `<option value="${p.id}">${p.designation}</option>`).join('');
    } else if (currentTab === 'secteurs') {
        territoireSelect.classList.remove('hidden');
        document.getElementById('territoire-select').required = true;
        loadTerritoiresForSelect();
    } else if (currentTab === 'groupements') {
        secteurSelect.classList.remove('hidden');
        document.getElementById('secteur-select').required = true;
        loadSecteursForSelect();
    }
    
    modal.classList.remove('hidden');
}

// Charger les territoires pour le select
function loadTerritoiresForSelect(callback) {
    const select = document.getElementById('territoire-select');
    select.innerHTML = '<option value="">Chargement...</option>';
    
    const promises = allProvinces.map(p => 
        fetch(`/parametres-geographiques/api/territoires/${p.id}/`)
            .then(r => r.json())
            .then(data => ({province: p, territoires: data.territoires}))
    );
    
    Promise.all(promises).then(results => {
        const allTerritoires = [];
        results.forEach(result => {
            result.territoires.forEach(t => {
                t.province = result.province;
                allTerritoires.push(t);
            });
        });
        
        select.innerHTML = '<option value="">Sélectionner un territoire</option>' + 
            allTerritoires.map(t => `<option value="${t.id}">${t.designation} (${t.province.designation})</option>`).join('');
        
        if (callback) callback();
    });
}

// Charger les secteurs pour le select
function loadSecteursForSelect(callback) {
    const select = document.getElementById('secteur-select');
    select.innerHTML = '<option value="">Chargement...</option>';
    
    const promises = allProvinces.map(p => 
        fetch(`/parametres-geographiques/api/territoires/${p.id}/`)
            .then(r => r.json())
            .then(data => ({province: p, territoires: data.territoires}))
    );
    
    Promise.all(promises).then(results => {
        const allTerritoires = [];
        results.forEach(result => {
            result.territoires.forEach(t => {
                t.province = result.province;
                allTerritoires.push(t);
            });
        });
        
        const secteurPromises = allTerritoires.map(t =>
            fetch(`/parametres-geographiques/api/secteurs/${t.id}/`)
                .then(r => r.json())
                .then(data => ({territoire: t, secteurs: data.secteurs}))
        );
        
        Promise.all(secteurPromises).then(secteurResults => {
            const allSecteurs = [];
            secteurResults.forEach(result => {
                result.secteurs.forEach(s => {
                    s.territoire = result.territoire;
                    allSecteurs.push(s);
                });
            });
            
            select.innerHTML = '<option value="">Sélectionner un secteur</option>' + 
                allSecteurs.map(s => `<option value="${s.id}">${s.designation} (${s.territoire.designation})</option>`).join('');
            
            if (callback) callback();
        });
    });
}

// Fermer le modal
function closeModal(id) {
    document.getElementById(id).classList.add('hidden');
    document.getElementById('form-province').reset();
    document.getElementById('province-select').required = false;
    document.getElementById('territoire-select').required = false;
    document.getElementById('secteur-select').required = false;
    
    const form = document.getElementById('form-province');
    if (form._customSubmitHandler) {
        form.removeEventListener('submit', form._customSubmitHandler);
        form._customSubmitHandler = null;
    }
    form.addEventListener('submit', handleFormSubmit);
}

// Gestionnaire de soumission par défaut (création)
function handleFormSubmit(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    
    let url = '';
    if (currentTab === 'provinces') {
        url = '/parametres-geographiques/province/create/';
    } else if (currentTab === 'territoires') {
        url = '/parametres-geographiques/territoire/create/';
    } else if (currentTab === 'secteurs') {
        url = '/parametres-geographiques/secteur/create/';
    } else if (currentTab === 'groupements') {
        url = '/parametres-geographiques/groupement/create/';
    }
    
    fetch(url, {
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
    })
    .catch(err => {
        showMessage('Erreur lors de la création', 'error');
    });
}

// Afficher un message
function showMessage(msg, type) {
    const colors = {
        success: 'bg-green-50 text-green-800 border-green-200',
        error: 'bg-red-50 text-red-800 border-red-200'
    };
    const div = document.createElement('div');
    div.className = `p-4 rounded-lg border ${colors[type]}`;
    div.textContent = msg;
    document.getElementById('message-container').appendChild(div);
    setTimeout(() => div.remove(), 3000);
}

// Obtenir le cookie CSRF
function getCookie(name) {
    let value = null;
    if (document.cookie) {
        document.cookie.split(';').forEach(c => {
            const cookie = c.trim();
            if (cookie.startsWith(name + '=')) {
                value = decodeURIComponent(cookie.substring(name.length + 1));
            }
        });
    }
    return value;
}

// Confirmer la suppression
function confirmDelete() {
    closeModal('modal-confirm');
    if (deleteCallback) {
        deleteCallback();
        deleteCallback = null;
    }
}




