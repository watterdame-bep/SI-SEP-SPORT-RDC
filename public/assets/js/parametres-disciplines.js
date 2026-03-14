// Gestion des Paramètres Disciplines
let disciplineToDelete = null;

// Afficher un message
function showMessage(message, type = 'success') {
    const container = document.getElementById('message-container');
    const alertClass = type === 'success' ? 'bg-green-50 border-green-400 text-green-800' : 'bg-red-50 border-red-400 text-red-800';
    const iconClass = type === 'success' ? 'fa-check-circle text-green-400' : 'fa-exclamation-circle text-red-400';
    
    const alert = document.createElement('div');
    alert.className = `${alertClass} border-l-4 p-4 rounded-lg flex items-start gap-3 animate-fade-in`;
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
    setTimeout(() => alert.remove(), 5000);
}

// Ouvrir le modal de création
function openCreateModal() {
    document.getElementById('modal-title').textContent = 'Nouvelle Discipline';
    document.getElementById('discipline-uid').value = '';
    document.getElementById('discipline-code').value = '';
    document.getElementById('discipline-designation').value = '';
    document.getElementById('modal-discipline').classList.remove('hidden');
}

// Ouvrir le modal d'édition
function editDiscipline(uid) {
    const row = document.querySelector(`tr[data-uid="${uid}"]`);
    if (!row) return;
    
    const code = row.querySelector('td:nth-child(1) span').textContent.trim();
    const designation = row.querySelector('td:nth-child(2) span').textContent.trim();
    
    document.getElementById('modal-title').textContent = 'Modifier la Discipline';
    document.getElementById('discipline-uid').value = uid;
    document.getElementById('discipline-code').value = code;
    document.getElementById('discipline-designation').value = designation;
    document.getElementById('modal-discipline').classList.remove('hidden');
}

// Fermer le modal
function closeModal() {
    document.getElementById('modal-discipline').classList.add('hidden');
}

// Soumettre le formulaire
document.getElementById('form-discipline').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const uid = document.getElementById('discipline-uid').value;
    const code = document.getElementById('discipline-code').value.trim().toUpperCase();
    const designation = document.getElementById('discipline-designation').value.trim();
    
    if (!code || !designation) {
        showMessage('Le code et la désignation sont obligatoires', 'error');
        return;
    }
    
    const url = uid 
        ? `/gouvernance/parametres/disciplines/${uid}/update/`
        : '/gouvernance/parametres/disciplines/create/';
    
    const method = uid ? 'PUT' : 'POST';
    
    try {
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ code, designation })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage(data.message, 'success');
            closeModal();
            setTimeout(() => location.reload(), 1000);
        } else {
            showMessage(data.message, 'error');
        }
    } catch (error) {
        showMessage('Erreur lors de l\'enregistrement', 'error');
        console.error(error);
    }
});

// Activer/Désactiver une discipline
async function toggleActif(uid) {
    try {
        const response = await fetch(`/gouvernance/parametres/disciplines/${uid}/toggle/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage(data.message, 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showMessage(data.message, 'error');
        }
    } catch (error) {
        showMessage('Erreur lors de la modification', 'error');
        console.error(error);
    }
}

// Supprimer une discipline
function deleteDiscipline(uid) {
    disciplineToDelete = uid;
    document.getElementById('modal-confirm-delete').classList.remove('hidden');
}

function closeConfirmDelete() {
    disciplineToDelete = null;
    document.getElementById('modal-confirm-delete').classList.add('hidden');
}

async function confirmDelete() {
    if (!disciplineToDelete) return;
    
    try {
        const response = await fetch(`/gouvernance/parametres/disciplines/${disciplineToDelete}/delete/`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage(data.message, 'success');
            closeConfirmDelete();
            setTimeout(() => location.reload(), 1000);
        } else {
            showMessage(data.message, 'error');
            closeConfirmDelete();
        }
    } catch (error) {
        showMessage('Erreur lors de la suppression', 'error');
        console.error(error);
        closeConfirmDelete();
    }
}

// Recherche
document.getElementById('search-input').addEventListener('input', function(e) {
    const searchTerm = e.target.value.toLowerCase();
    const rows = document.querySelectorAll('#disciplines-list tr');
    
    rows.forEach(row => {
        const code = row.querySelector('td:nth-child(1)')?.textContent.toLowerCase() || '';
        const designation = row.querySelector('td:nth-child(2)')?.textContent.toLowerCase() || '';
        
        if (code.includes(searchTerm) || designation.includes(searchTerm)) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
});

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
