from django.urls import path
from .views import *

app_name = "core"

urlpatterns = [
    path("listaeventi/", ListaEventiView.as_view(), name="listaeventi"), #Accessibile da: Utenti, Anonymous
    path("prenotazioni/utente/", PrenotazioniUtenteView.as_view(), name="prenotazioni_utente"), #Accessibile da: Utenti
    path("prenotazioni/pubblicatore/", PrenotazioniPubblicatoreView.as_view(), name="prenotazioni_pubblicatore"), #Accessibile da: Pubblicatori
    path("evento/<int:pk>/", DetailEventoView.as_view(), name="visualizza_evento"), #Accessibile da: Utenti
    path("pubblicatore/<int:pk>/", DetailPubblicatoreView.as_view(), name="visualizza_pubblicatore"), #Accessibile da: Utenti
    path("cercaevento/", CercaEvento.as_view(), name="cerca_evento"), #Accessibile da: Utenti, Anonymous
    path("prenotazioneconfermata/", PrenotazioneConfermataView.as_view(), name="prenotazione_confermata"), #Accessibile da: Utenti
    path("gestiscieventi/", ListaEventiPerPubblicatoreView.as_view(), name="gestisci_eventi"), #Accessibile da: Pubblicatore
    path("recensioni/<int:evento_id>/", RecensioniEventoView.as_view(), name="recensioni_evento"), #Accessibile da: Utenti

    path('recensione/<int:prenotazione_id>/', salva_recensione, name="salva_recensione"), #Accessibile da: Utenti
    path('creaevento/', create_evento, name="crea_evento"), #Accessibile da: Pubblicatore
    path('eliminaevento/<int:pk>/', elimina_evento, name="elimina_evento"), #Accessibile da: Pubblicatore
    path('home/', home_page, name="homepage"),
    path("eliminaprenotazione/<int:pk>/", elimina_prenotazione, name="elimina_prenotazione") #Accessibile da: Utenti, Pubblicatore
]
