import streamlit as st
import datetime

# --- CONFIGURATION ET STYLES ---
st.set_page_config(page_title="Réservation - Salon de Coiffure", page_icon="💇‍♀️", layout="centered")

# Initialisation de la base de données temporaire en mémoire
if "rdv_db" not in st.session_state:
    st.session_state.rdv_db = []  # Liste de dictionnaires contenant les RDV

# --- DONNÉES DU SALON ---
NB_EMPLOYES = 3

PRESTATIONS = {
    "Coupe & Brushing": {"duree": 60, "prix": "30€"},
    "Tresses Africaines": {"duree": 120, "prix": "70€"},
    "Manucure / Ongles": {"duree": 60, "prix": "25€"},
    "Coloration": {"duree": 120, "prix": "50€"},
    "Soin Capillaire": {"duree": 30, "prix": "20€"},
}

# --- FONCTIONS UTILES ---
def est_ouvert(date_choisie):
    """Vérifie si le salon est ouvert et retourne les heures de début et de fin."""
    jour = date_choisie.weekday()  # 0=Lundi, 1=Mardi... 5=Samedi, 6=Dimanche
    
    if jour == 0:  # Lundi fermé
        return False, None, None
    elif jour in [1, 2, 3, 4]:  # Mardi à Vendredi (10h - 18h)
        return True, 10, 18
    else:  # Week-end (8h - 18h)
        return True, 8, 18

def generer_creneaux(date_choisie, duree_minutes):
    """Génère les créneaux disponibles en fonction des employés libres."""
    ouvert, heure_debut, heure_fin = est_ouvert(date_choisie)
    if not ouvert:
        return []

    creneaux_dispo = []
    heure_actuelle = datetime.datetime.combine(date_choisie, datetime.time(heure_debut, 0))
    heure_cloture = datetime.datetime.combine(date_choisie, datetime.time(heure_fin, 0))

    while heure_actuelle + datetime.timedelta(minutes=duree_minutes) <= heure_cloture:
        # Compter combien de RDV chevauchent ce créneau
        simultane = 0
        debut_rdv_propose = heure_actuelle
        fin_rdv_propose = heure_actuelle + datetime.timedelta(minutes=duree_minutes)

        for rdv in st.session_state.rdv_db:
            if rdv["date"] == date_choisie:
                # Vérification du chevauchement des horaires
                if not (fin_rdv_propose <= rdv["debut"] or debut_rdv_propose >= rdv["fin"]):
                    simultane += 1

        # Si on a moins de RDV en cours que de coiffeurs dispos, le créneau est libre !
        if simultane < NB_EMPLOYES:
            creneaux_dispo.append(heure_actuelle.time())
        
        # Avancer de 30 minutes pour proposer le choix suivant
        heure_actuelle += datetime.timedelta(minutes=30)

    return creneaux_dispo

# --- INTERFACE UTILISATEUR ---
st.title("💇‍♀️ Prendre Rendez-vous")
st.write("Réservez votre prestation en quelques clics. Notre équipe de 3 expertes est à votre disposition !")

st.divider()

# 1. Informations client
col1, col2 = st.columns(2)
with col1:
    nom = st.text_input("Nom & Prénom")
with col2:
    telephone = st.text_input("Téléphone")

# 2. Choix de la prestation
prestation_choisie = st.selectbox(
    "Choisissez une prestation :", 
    options=list(PRESTATIONS.keys()),
    format_func=lambda x: f"{x} ({PRESTATIONS[x]['duree']} min - {PRESTATIONS[x]['prix']})"
)

duree_presta = PRESTATIONS[prestation_choisie]["duree"]

# 3. Choix de la date
date_rdv = st.date_input("Date du rendez-vous :", min_value=datetime.date.today())

# Vérification du jour d'ouverture
ouvert, _, _ = est_ouvert(date_rdv)

if not ouvert:
    st.error("Désolé, le salon est fermé le lundi. Veuillez choisir un autre jour.")
else:
    # 4. Choix de l'heure (dynamique selon les dispo)
    creneaux_libres = generer_creneaux(date_rdv, duree_presta)
    
    if not creneaux_libres:
        st.warning("Désolé, plus aucun créneau n'est disponible pour cette prestation à cette date.")
    else:
        heure_rdv = st.selectbox("Heures disponibles :", options=creneaux_libres, format_func=lambda x: x.strftime("%H:%h"))
        
        # Bouton de validation
        if st.button("Confirmer le rendez-vous", type="primary"):
            if not nom or not telephone:
                st.error("Veuillez remplir votre nom et votre numéro de téléphone.")
            else:
                # Calcul des heures exactes de début et de fin
                dt_debut = datetime.datetime.combine(date_rdv, heure_rdv)
                dt_fin = dt_debut + datetime.timedelta(minutes=duree_presta)
                
                # Enregistrement du RDV
                nouveau_rdv = {
                    "client": nom,
                    "tel": telephone,
                    "prestation": prestation_choisie,
                    "date": date_rdv,
                    "debut": dt_debut,
                    "fin": dt_fin
                }
                st.session_state.rdv_db.append(nouveau_rdv)
                
                st.success(f"🎉 Rendez-vous confirmé pour {nom} ! Prestation : {prestation_choisie} le {date_rdv.strftime('%d/%m/%Y')} à {heure_rdv.strftime('%H:%M')}.")

# --- SECTION ADMIN (POUR VOIR LES RDV PRIS) ---
st.divider()
with st.expander("Voir l'agenda du salon (Zone Admin)"):
    if not st.session_state.rdv_db:
        st.info("Aucun rendez-vous pour le moment.")
    else:
        for r in st.session_state.rdv_db:
            st.write(f"📅 **{r['date'].strftime('%d/%m/%Y')}** | ⏰ {r['debut'].strftime('%H:%M')} - {r['fin'].strftime('%H:%M')} : **{r['client']}** ({r['prestation']}) - 📞 {r['tel']}")
