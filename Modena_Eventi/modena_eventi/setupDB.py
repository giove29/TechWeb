from core.models import *
from utenti.models import *
import random
import json, os
from django.db import transaction, IntegrityError
import random
from datetime import timedelta
from django.utils import timezone

BO = 8

def erase_db():
    print("Cancello il DB")
    try:
        Evento.objects.all().delete()
        Tag.objects.all().delete()
        Pubblicatore.objects.all().delete()
        Prenotazione.objects.all().delete()
        Recensione.objects.all().delete()
        User.objects.all().delete()
        Utente.objects.all().delete()
        print("Database cancellato")
    except Exception as e:
        print("Database già vuoto")

def init_db():
    #------CREAZIONE SUPER USER------
    admin = User.objects.create_superuser(username="admin", password="passwordadmin")
    admin.save()

    #------POPOLAZIONE TABELLA PUBBLICATORI------
    json_pubblicatori_path = os.path.join(os.path.dirname(__file__), 'initDBJsons', 'pubblicatori.json')
    
    with open(json_pubblicatori_path, 'r') as file:
        data = json.load(file) 
    with transaction.atomic():
        for item in data:
            #----creazione dell'utente a cui associare la pubblicatore-----
            user, created = User.objects.get_or_create(
                username=item['username'],
                defaults={
                    'first_name': item['nome'],
                    'is_pubblicatore': True,
                    'is_utente': False,
                    'img': 'static/img/default_img/user2.png'
                }
            )
            
            if created:
                user.set_password(item['password'])
                user.save()

            #----creazione della pubblicatore-----
            pubblicatore, created = Pubblicatore.objects.get_or_create(
                user=user,
                defaults={
                    'descrizione': item['descrizione'],
                    'latitudine': item['latitudine'],
                    'longitudine': item['longitudine']
                }
            )
            
            if not created:
                # Se il pubblicatore esiste già, aggiornalo
                pubblicatore.descrizione = item['descrizione']
                pubblicatore.latitudine = item['latitudine']
                pubblicatore.longitudine = item['longitudine']
                pubblicatore.save()


    #------POPOLAZIONE TABELLA EVENTI------
    json_eventi_path = os.path.join(os.path.dirname(__file__), 'initDBJsons', 'eventi.json')
    
    with open(json_eventi_path, 'r') as file:
        data = json.load(file)    

    with transaction.atomic(): # assicura che tutte le operazioni del db siano eseguite singolarmente
        for item in data:
            tags = item.pop('tags')
            tags = [nome.strip() for nome in tags.split(',')]

            evento, _ = Evento.objects.update_or_create(
                gratis=item['gratis'],
                descrizione=item['descrizione'],
                nome=item['nome'],
                costo=item['costo'],
                data=item['data'],
                max=item['max'],
                pubblicatore=random.choice(list(Pubblicatore.objects.all()))
            )
            

            for nome_tag in tags:
                tag, _ = Tag.objects.get_or_create(
                    nome=nome_tag.lower()
                )
                evento.tags.add(tag)

    #----POPOLAZIONE UTENTI NORMALI ----
    json_utenti_path = os.path.join(os.path.dirname(__file__), 'initDBJsons', 'utenti.json')
    with open(json_utenti_path, 'r') as file:
        data = json.load(file)
    
    with transaction.atomic():
        for item in data:
            # Creazione dell'utente
            user, created = User.objects.get_or_create(
                username=item['username'],
                defaults={
                    'first_name': item['nome'],
                    'last_name': item['cognome'],
                    'is_pubblicatore': False,
                    'is_utente': True,
                    'img': 'static/img/default_img/user1.png'
                }
            )

            # Impostazione della password
            user.set_password(item['password'])
            user.save()

            # Creazione dell'oggetto Utente associato
            utente, created = Utente.objects.get_or_create(
                user=user
            )

    #-----POPOLAZIONE TABELLA PRENOTAZIONI-----

    utenti = Utente.objects.all()
    eventi = Evento.objects.all()

    for evento in eventi:
        for _ in range(BO):
            utente = random.choice(utenti)

            created = False
            while not created:
                
                Prenotazione.objects.create(
                    utente=utente,
                    evento=evento
                )
                created = True

        #-----POPOLAZIONE TABELLA RECENSIONI-----
    json_recensioni_path = os.path.join(os.path.dirname(__file__), 'initDBJsons', 'recensioni.json')
    with open(json_recensioni_path, 'r', encoding='UTF-8') as file:
        data = json.load(file)

    prenotazioni = Prenotazione.objects.all()
    oggi = timezone.localdate()

    #prendo solo un 50% così da sperimentare
    prenotazioni_totali = Prenotazione.objects.count()
    prenotazioni_campione = Prenotazione.objects.all()[:prenotazioni_totali // 2]
    for prenotazione in prenotazioni_campione:
        recensione_random = random.choice(data)
        recensione = Recensione(
            data_recensione=oggi,
            utente=prenotazione.utente,
            evento=prenotazione.evento,
            testo=recensione_random['Testo'],
            voto=recensione_random['Voto'],
            prenotazione=prenotazione
        )
        try:
            recensione.save()
        except Exception as e:
            pass
            # print(f'Errore creando recensione per la prenotazione {prenotazione}: {e}')


    print("DUMP DB")
    for evento in Evento.objects.all():
        print(evento, evento.tags.all())
    

    for user in Pubblicatore.objects.all():
        print(f'{user}')
    
    for user in Utente.objects.all():
        print(user)
        
    for prenotazione in Prenotazione.objects.all():
        print(prenotazione)
    
    for recensione in Recensione.objects.all():
        print(recensione)


    dbInfo = (
        f"{Evento.objects.count()} - Eventi\n"
        f"{Pubblicatore.objects.count()} - Pubblicatori\n"
        f"{Utente.objects.count()} - Utenti\n"
        f"{Prenotazione.objects.count()} - Prenotazioni\n"
        f"{Recensione.objects.count()} - Recensioni\n"
        f"{User.objects.filter(is_staff=True).count()} - Admin"
    )
    print("INFO DATABASE")
    print(dbInfo)