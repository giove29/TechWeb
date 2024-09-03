import heapq
from django.db.models import Avg
from django.utils.timezone import now
from datetime import date
from collections import Counter
from .models import *
from utenti.models import Pubblicatore
from collections import defaultdict

def get_recommendations_for_evento(evento, num_rec=3, user_id=None):
    
    # Ottieni tutte le recensioni per l'evento specificato
    evento_recensioni = Recensione.objects.filter(evento_id=evento.id)
    # Crea un dizionario con utente_id come chiave e voto come valore
    recensioni_dict = {recensione.utente: recensione.voto for recensione in evento_recensioni}
    recommended_eventi = defaultdict(list)
    # scorro tutti gli utenti e i voti che hanno dato all'evento
    for utente, voto in recensioni_dict.items():
        # Scorro tutti gli eventi che ha recensito un utente
        # moltiplico il voto dato all'evento in questione X l'evento che ha recensito e lo salvo in un dizionario
        # evento: [voto, voto, voto] dove la lista dei voti sarà esclusivamente degli utenti che hanno recensito sia 
        # quell'evento che l'evento passato come parametro
        # Così facendo sarà più importante l'opinione di un utente a cui è piaciuto l'evento che sto visualizzando. 
        recensioni_utente = Recensione.objects.filter(utente=utente).exclude(evento_id=evento.id)
        for recensione in recensioni_utente:
            recommended_eventi[recensione.evento.id].append(recensione.voto*voto)   
    
    medie_dict = {evento_id: sum(voti) / len(voti) for evento_id, voti in recommended_eventi.items()}
    topEventi = heapq.nlargest(num_rec, medie_dict.items(), key=lambda x: x[1])
    return [Evento.objects.get(id=id) for id, _ in topEventi]


def get_recommended_pubblicatori_by_reviews():
    
    # Annotiamo i pubblicatori con la media dei voti delle recensioni degli eventi che pubblicano
    pubblicatori = Pubblicatore.objects.annotate(
        avg_voto=Avg('eventi__recensioni__voto')  # Media dei voti delle recensioni per ogni evento
    ).order_by('-avg_voto')[:5]  # Ordiniamo per la media dei voti e prendiamo i primi 5

    return pubblicatori


def get_recommended_eventi_by_tags(utente=None):
    eventi_per_tag = {}
    
    if utente is None:
        tags = Tag.objects.all()
    else:
        tags = get_top_3_tags_for_utente(utente)
        if tags == []:
            tags = Tag.objects.all()

    for tag in tags:
        eventi = Evento.objects.filter(tags=tag, data__gte=now().date()).annotate(
            avg_voto=Avg('recensioni__voto')
        ).order_by('-avg_voto').first()
        
        if eventi:
            eventi_per_tag[tag] = eventi

    return eventi_per_tag

def get_top_3_tags_for_utente(utente):
    # Filtra le prenotazioni dell'utente
    prenotazioni = Prenotazione.objects.filter(
        utente=utente
    )

    # Estrai i tag degli eventi passati
    tags = []
    for prenotazione in prenotazioni:
        eventi = prenotazione.evento.tags.all()
        tags.extend(eventi)

    if not tags:
        return []

    # Conta la frequenza di ciascun tags
    tag_ids = [tag.id for tag in tags]
    tag_counter = Counter(tag_ids)
    
    # Trova i 3 tag più comuni
    top_3_tag_ids = [tag_id for tag_id, _ in tag_counter.most_common(3)]

    # Restituisce istanze di Tag
    top_3_tags = Tag.objects.filter(id__in=top_3_tag_ids)

    return top_3_tags