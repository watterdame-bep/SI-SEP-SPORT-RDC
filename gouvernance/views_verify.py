"""
Vues publiques pour la vérification des documents (Arrêtés et Certificats).
"""
from django.shortcuts import render
from django.http import JsonResponse
from gouvernance.models import Institution


def verify_home(request):
    """Page d'accueil pour la vérification des documents."""
    return render(request, 'sisep_verify.html')


def verify_arrete_by_numero(request, numero_arrete):
    """
    Vérifier un arrêté par son numéro.
    Redirige vers la page de vérification avec l'UUID.
    """
    try:
        institution = Institution.objects.get(
            numero_arrete=numero_arrete,
            statut_signature='SIGNE',
            niveau_territorial='FEDERATION'
        )
        return render(request, 'gouvernance/verifier_arrete.html', {
            'institution': institution,
        })
    except Institution.DoesNotExist:
        return render(request, 'gouvernance/verifier_arrete.html', {
            'institution': None,
        }, status=404)


def verify_certificat_by_numero(request, numero_homologation):
    """
    Vérifier un certificat par son numéro.
    """
    try:
        institution = Institution.objects.get(
            numero_homologation=numero_homologation,
            statut_signature='SIGNE',
            niveau_territorial='FEDERATION'
        )
        return render(request, 'gouvernance/verifier_certificat.html', {
            'institution': institution,
            'valide': True,
        })
    except Institution.DoesNotExist:
        return render(request, 'gouvernance/verifier_certificat.html', {
            'valide': False,
            'message': 'Certificat non trouvé ou invalide'
        }, status=404)


def verify_certificat_by_uuid(request, uid):
    """
    Vérifier un certificat par son UUID (depuis QR code).
    """
    institution = Institution.objects.filter(
        uid=uid,
        statut_signature='SIGNE',
        niveau_territorial='FEDERATION'
    ).prefetch_related('disciplines', 'provinces_implantation').first()
    
    return render(request, 'gouvernance/verifier_certificat.html', {
        'institution': institution,
        'valide': institution is not None,
    })


def verifier_certificat_aptitude(request, uid):
    """
    Vérification publique du certificat d'aptitude (F72) — depuis QR code.
    Affiche uniquement : validité, athlète (nom, ID sportif), date examen, médecin.
    Aucun détail médical.
    """
    from gouvernance.models import VisiteMedicale

    visite = VisiteMedicale.objects.filter(uid=uid).select_related(
        'athlete', 'athlete__personne', 'athlete__club', 'athlete__discipline'
    ).first()

    return render(request, 'gouvernance/verifier_certificat_aptitude.html', {
        'visite': visite,
        'valide': visite is not None,
    })


def verifier_athlete(request, uid):
    """
    Vérification publique d'un athlète (depuis QR code sur la licence F22).
    Affiche : nom, n° national sportif, statut (Apte / Certifié national), validité licence.
    """
    from gouvernance.models import Athlete

    athlete = Athlete.objects.filter(uid=uid, actif=True).select_related(
        'personne', 'club', 'discipline'
    ).first()

    return render(request, 'gouvernance/verifier_athlete.html', {
        'athlete': athlete,
        'valide': athlete is not None and athlete.statut_certification == 'CERTIFIE_NATIONAL',
    })


def verify_ligue_by_uuid(request, uid):
    """
    Vérifier une ligue provinciale par son UUID (depuis QR code d'attestation).
    """
    from gouvernance.models import AttestationReconnaissance

    ligue = Institution.objects.filter(
        uid=uid,
        niveau_territorial='LIGUE',
        statut_signature='SIGNE'
    ).prefetch_related('disciplines', 'province_admin', 'institution_tutelle').first()
    
    attestation = None
    if ligue:
        attestation = AttestationReconnaissance.objects.filter(ligue=ligue).first()
    
    return render(request, 'gouvernance/verifier_ligue.html', {
        'ligue': ligue,
        'attestation': attestation,
        'valide': ligue is not None,
    })
