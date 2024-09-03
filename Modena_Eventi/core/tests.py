from django.test import TestCase
import json
from django.core.exceptions import ValidationError
from .models import *
from utenti.models import *
from django.utils.timezone import now
from datetime import timedelta
from django.db.utils import IntegrityError
from django.urls import reverse
from django.core.exceptions import PermissionDenied

#----------------MODEL TEST---------------- 

class PrenotazioneModelTest(TestCase):      

    def setUp(self):
        '''
        SetUp Phase
        '''
        #---CREAZIONE DUE USER---
        self.user_utente = User.objects.create_user(
            username='testutente',
            first_name='Federico',
            last_name='Utente',
            password='testpass',
            is_utente=True
        )
        self.user_pubblicatore = User.objects.create_user(
            username='testpubblicatore',
            first_name='Massimo',
            password='testpass',
            is_pubblicatore=True
        )
        #---CREAZIONI UTENTI---
        self.utente = Utente.objects.create(
            user=self.user_utente
        )
        self.pubblicatore = Pubblicatore.objects.create(
            user=self.user_pubblicatore,
            latitudine = 44.72958901676243,
            longitudine = 11.040441132528958,
            descrizione='Descrizione del pubblicatore'
        )

        #----CREAZIONE EVENTO ASSOCIATO AL PUBBLICATORE----


        self.evento = Evento.objects.create(
            nome="Qualche evento",
            descrizione = "Un qualche evento da qualche parte",
            data = now().date() + timedelta(days=1),
            max = 100,
            gratis=False,
            costo=20.00,
            pubblicatore=self.pubblicatore
        )
        
        #-----CREAZIONE PRENOTAZIONE----
        self.prenotazione = Prenotazione.objects.create(
            utente=self.utente,
            evento=self.evento
        )
        
    
    def test_only_utente(self):
        '''
        Ogni prenotazione può essere fatta solo da utenti comuni e non da pubblicatori
        '''
        with self.assertRaises(ValueError):
            Prenotazione.objects.create(
                utente=self.pubblicatore,
                evento=self.evento
            )

class RecensioneModelTest(TestCase):

    def setUp(self):
        '''
        SetUp Phase
        '''
        #---CREAZIONE DUE USER---
        self.user_utente = User.objects.create_user(
            username='testutente',
            first_name='Federico',
            last_name='Utente',
            password='testpass',
            is_utente=True
        )
        self.user_pubblicatore = User.objects.create_user(
            username='testpubblicatore',
            first_name='Massimo',
            password='testpass',
            is_pubblicatore=True
        )
        #---CREAZIONI UTENTI---
        self.utente = Utente.objects.create(
            user=self.user_utente
        )
        self.pubblicatore = Pubblicatore.objects.create(
            user=self.user_pubblicatore,
            latitudine = 44.72958901676243,
            longitudine = 11.040441132528958,
            descrizione='Descrizione del pubblicatore'
        )

        #----CREAZIONE EVENTO FUTURO ASSOCIATO AL PUBBLICATORE----
        self.evento_futuro = Evento.objects.create(
            nome="Qualche evento futuro",
            descrizione = "Un qualche evento futuro da qualche parte",
            data = now().date() + timedelta(days=1),
            max = 100,
            gratis=False,
            costo=20.00,
            pubblicatore=self.pubblicatore
        )

        #----CREAZIONE EVENTO PASSATO ASSOCIATO AL PUBBLICATORE----
        self.evento_passato = Evento.objects.create(
            nome="Qualche evento passato",
            descrizione = "Un qualche evento passato da qualche parte",
            data = now().date() + timedelta(days=-1),
            max = 100,
            gratis=False,
            costo=20.00,
            pubblicatore=self.pubblicatore
        )
        
        #-----CREAZIONE PRENOTAZIONI----
        self.prenotazione_futura = Prenotazione.objects.create(
            utente=self.utente,
            evento=self.evento_futuro
        )
        self.prenotazione_passata = Prenotazione.objects.create(
            utente=self.utente,
            evento=self.evento_passato
        )
        

    def test_invalid_recensione_data(self):
        '''
        Si possono recensire solo prenotazioni con date passate
        '''
        with self.assertRaises(ValidationError):
            Recensione.objects.create(
                data_recensione=now().date(),
                utente=self.utente,
                evento=self.evento_futuro,
                testo='Buono',
                voto=4,
                prenotazione=self.prenotazione_futura
            )

    def test_invalid_voto(self):
        '''
        Il voto delle recensioni non può essere un valore non compreso tra 1 e 5
        '''
        # Lista di voti non validi
        invalid_votes = [0, 6, -1, 10, 100]

        for voto in invalid_votes:
            with self.assertRaises(ValidationError):
                recensione = Recensione.objects.create(
                    data_recensione=now().date(),
                    utente=self.utente,
                    evento=self.evento_passato,
                    testo='Eccellente',
                    voto=voto,
                    prenotazione=self.prenotazione_passata
                )
                recensione.full_clean()  # forzerà la validazione
                recensione.save()
    
    def test_unique_recensione_evento(self):
        '''
        Un utente può recensire un evento (la prenotazione associata) solo una volta
        '''
        
        Recensione.objects.create(
            data_recensione=now().date(),
            utente=self.utente,
            evento=self.evento_passato,
            testo='Buono',
            voto=4,
            prenotazione=self.prenotazione_passata
        )
        
        with self.assertRaises(ValidationError):
            Recensione.objects.create(
                data_recensione=now().date(),
                utente=self.utente,
                evento=self.evento_passato,
                testo='Cattivo',
                voto=1,
                prenotazione=self.prenotazione_passata
            )
    
    def test_recensione_for_other_user(self):
        '''
        Un utente può recensire solo per sè stesso
        '''
        self.client.login(username='testutente', password='testpass')
        self.user_utente2 = User.objects.create_user(
            username='testutente2',
            first_name='Franco',
            last_name='Utente',
            password='testpass',
            is_utente=True
        )
        self.utente2 = Utente.objects.create(
            user=self.user_utente2
        )
        with self.assertRaises(ValueError):
            Recensione.objects.create(
                data_recensione=now().date(),
                utente=self.utente2,
                evento=self.evento_passato,
                testo='Buono',
                voto=4,
                prenotazione=self.prenotazione_passata
            )

#----------------VIEW TEST----------------  
class EliminaPrenotazioneViewTest(TestCase):# 

    def setUp(self):
        # CREAZIONE DUE UTENTI
        self.user_utente = User.objects.create_user(username='testutente',
                                                    first_name='first_name',
                                                    last_name='last_name',
                                                    password='testpass', 
                                                    is_utente=True
                                                    )
        
        self.utente = Utente.objects.create(user=self.user_utente)

        self.user_pubblicatore = User.objects.create_user(username='testpubblicatore', 
                                                        password='testpass', 
                                                        first_name='first_name',
                                                        is_pubblicatore=True
                                                        )
        self.pubblicatore = Pubblicatore.objects.create(
            user=self.user_pubblicatore,
            descrizione='Descrizione del Pubblicatore',
            latitudine = 44.72958901676243,
            longitudine = 11.040441132528958,
        )


        #----CREAZIONE EVENTO ASSOCIATO AL PUBBLICATORE----
        self.evento = Evento.objects.create(
            nome="Qualche evento",
            descrizione = "Un qualche evento da qualche parte",
            data = now().date() + timedelta(days=1),
            max = 100,
            gratis=False,
            costo=20.00,
            pubblicatore=self.pubblicatore
        )
        
        #-----CREAZIONE PRENOTAZIONE----
        self.prenotazione = Prenotazione.objects.create(
            utente=self.utente,
            evento=self.evento
        )
        
    def test_delete_just_own_prenotazioni(self):
        """
        Un utente può eliminare solo le proprie prenotazioni.
        """
        self.user_utente2 = User.objects.create_user(
            username='testutente2',
            password='testpass',
            first_name='first_name',
            last_name='last_name',
            is_utente=True
        )
        
        self.utente2 = Utente.objects.create(
            user=self.user_utente2
        )
        
        
        self.client.login(username='testutente2', password='testpass')
    

        response = self.client.post(reverse('core:elimina_prenotazione', args=[self.prenotazione.pk]))
        self.assertEqual(response.status_code, 403)

class PrenotazioniUtenteViewTest(TestCase): 

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass', is_utente=True)
        self.utente = Utente.objects.create(user=self.user)

        self.user_pubblicatore = User.objects.create_user(username='testpubblicatore', 
                                                        password='testpass', 
                                                        first_name='first_name',
                                                        is_pubblicatore=True
                                                        )
        self.pubblicatore = Pubblicatore.objects.create(
            user = self.user_pubblicatore,
            descrizione='Descrizione del pubblicatore',
            latitudine = 44.72958901676243,
            longitudine = 11.040441132528958,
        )
        self.user_pubblicatore_2 = User.objects.create_user(username='testpubblicatore2', 
                                                        password='testpass', 
                                                        first_name='first_name',
                                                        is_pubblicatore=True
                                                        )
        self.pubblicatore_2 = Pubblicatore.objects.create(
            user = self.user_pubblicatore_2,
            descrizione='Descrizione del pubblicatore',
            latitudine = 44.735,
            longitudine = 11.042,
        )


        #----CREAZIONE EVENTI ASSOCIATI AI PUBBLICATORI----
        self.evento = Evento.objects.create(
            nome="Qualche evento",
            descrizione = "Un qualche evento da qualche parte",
            data = now().date() + timedelta(days=-1),
            max = 100,
            gratis=False,
            costo=20.00,
            pubblicatore=self.pubblicatore
        )

        self.evento_2 = Evento.objects.create(
            nome="Evento votatissimo",
            descrizione = "Evento Votatissimooo",
            data = now().date() + timedelta(days=-3),
            max = 100,
            gratis=False,
            costo=20.00,
            pubblicatore=self.pubblicatore_2
        )
        self.evento_futuro = Evento.objects.create(
            nome="Qualche evento futuro",
            descrizione = "Un qualche evento da qualche parte",
            data = now().date() + timedelta(days=1),
            max = 100,
            gratis=False,
            costo=20.00,
            pubblicatore=self.pubblicatore
        )

        self.evento_futuro_2 = Evento.objects.create(
            nome="Evento votatissimo futuro",
            descrizione = "Evento Votatissimooo",
            data = now().date() + timedelta(days=3),
            max = 100,
            gratis=False,
            costo=20.00,
            pubblicatore=self.pubblicatore_2
        )

        
        #-----CREAZIONE PRENOTAZIONE----
        self.prenotazione = Prenotazione.objects.create(
            utente=self.utente,
            evento=self.evento
        )

        #-----CREAZIONE RECENSIONI----
        diz_utenti = {}

        for i in range(5):
            user = User.objects.create_user(username='testuser'+str(i), password='testpass', is_utente=True)
            utente = Utente.objects.create(user=user)
            diz_utenti[user] = utente
            prenotazione = Prenotazione.objects.create(
                utente=utente,
                evento=self.evento
            )
            Recensione.objects.create(
                data_recensione=now().date(),
                utente = utente,
                evento = self.evento,
                testo = "Ciao" + str(i),
                voto = 1,
                prenotazione = prenotazione
            )
        prenotazione = Prenotazione.objects.create(
                utente=utente,
                evento=self.evento
            )
        Recensione.objects.create(
                data_recensione=now().date(),
                utente = utente,
                evento = self.evento_2,
                testo = "TOP",
                voto = 5,
                prenotazione = prenotazione
            )



    def test_first_prenotazione_before_today(self):
        '''
        Verifico che la prima recensione(la più recente) delle prenotazioni passate sia minore di quella attuale
        '''
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('core:prenotazioni_utente') + '?page_passate=1')
        
        prenotazioni_passate_page = response.context.get('prenotazioni_passate_page_obj')
        
        self.assertIsNotNone(prenotazioni_passate_page)
        
        # Verifica che ci siano prenotazioni nella pagina
        self.assertTrue(len(prenotazioni_passate_page.object_list) > 0)
        
        first_old_booking = list(prenotazioni_passate_page)[0][0]
        
        self.assertTrue(first_old_booking.evento.data < now().date())
    
    def test_no_prenotazione_nuovo_utente(self):
        '''
        Controllo che un nuovo utente non abbia nessuna prenotazione
        '''
        new_user = User.objects.create_user(username='newuser', password='newpass', is_utente=True)
        Utente.objects.create(user=new_user)

        self.client.login(username='newuser', password='newpass')
        response = self.client.get(reverse('core:prenotazioni_utente'))

        self.assertContains(response, 'Nessuna prenotazione passata')
        self.assertContains(response, 'Nessuna prenotazione futura')
    
    def test_review_button_disabled_for_reviewed_booking(self):
        '''
        Verifica che il tasto per recensire una prenotazione già recensita sia disabilitato
        '''
        self.client.login(username='testuser', password='testpass')
        
        self.data_passata = now().date() + timedelta(days=-1)
        prenotazione = Prenotazione.objects.create(
            utente=self.utente,
            evento=self.evento
        )
        
        Recensione.objects.create(
            data_recensione=now().date(),
            utente=self.utente,
            evento=self.evento,
            testo='Buono',
            voto=4,
            prenotazione=prenotazione
        )
        
        response = self.client.get(reverse('core:prenotazioni_utente'))
        self.assertContains(response, 'disabled-btn')

class CercaEventoViewTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass', is_utente=True)
        self.utente = Utente.objects.create(user=self.user)

        self.user_pubblicatore = User.objects.create_user(username='testpubblicatore', 
                                                        password='testpass', 
                                                        first_name='first_name',
                                                        is_pubblicatore=True
                                                        )
        self.pubblicatore = Pubblicatore.objects.create(
            user = self.user_pubblicatore,
            descrizione='Descrizione del pubblicatore',
            latitudine = 44.72958901676243,
            longitudine = 11.040441132528958,
        )
        self.user_pubblicatore_2 = User.objects.create_user(username='testpubblicatore2', 
                                                        password='testpass', 
                                                        first_name='first_name',
                                                        is_pubblicatore=True
                                                        )
        self.pubblicatore_2 = Pubblicatore.objects.create(
            user = self.user_pubblicatore_2,
            descrizione='Descrizione del pubblicatore',
            latitudine = 44.735,
            longitudine = 11.042,
        )


        #----CREAZIONE EVENTI ASSOCIATI AI PUBBLICATORI----
        self.evento = Evento.objects.create(
            nome="Qualche evento",
            descrizione = "Un qualche evento da qualche parte",
            data = now().date() + timedelta(days=-1),
            max = 100,
            gratis=False,
            costo=20.00,
            pubblicatore=self.pubblicatore
        )

        self.evento_2 = Evento.objects.create(
            nome="Evento votatissimo",
            descrizione = "Evento Votatissimooo",
            data = now().date() + timedelta(days=-3),
            max = 100,
            gratis=False,
            costo=20.00,
            pubblicatore=self.pubblicatore_2
        )
        self.evento_futuro = Evento.objects.create(
            nome="Qualche evento futuro",
            descrizione = "Un qualche evento da qualche parte",
            data = now().date() + timedelta(days=1),
            max = 100,
            gratis=False,
            costo=20.00,
            pubblicatore=self.pubblicatore
        )

        self.evento_futuro_2 = Evento.objects.create(
            nome="Evento votatissimo futuro",
            descrizione = "Evento Votatissimooo",
            data = now().date() + timedelta(days=3),
            max = 100,
            gratis=False,
            costo=20.00,
            pubblicatore=self.pubblicatore_2
        )

        
        #-----CREAZIONE PRENOTAZIONE----
        self.prenotazione = Prenotazione.objects.create(
            utente=self.utente,
            evento=self.evento
        )

        #-----CREAZIONE RECENSIONI----
        diz_utenti = {}

        for i in range(5):
            user = User.objects.create_user(username='testuser'+str(i), password='testpass', is_utente=True)
            utente = Utente.objects.create(user=user)
            diz_utenti[user] = utente
            prenotazione = Prenotazione.objects.create(
                utente=utente,
                evento=self.evento
            )
            Recensione.objects.create(
                data_recensione=now().date(),
                utente = utente,
                evento = self.evento,
                testo = "Ciao" + str(i),
                voto = 1,
                prenotazione = prenotazione
            )
        prenotazione = Prenotazione.objects.create(
                utente=utente,
                evento=self.evento
            )
        Recensione.objects.create(
                data_recensione=now().date(),
                utente = utente,
                evento = self.evento_2,
                testo = "TOP",
                voto = 5,
                prenotazione = prenotazione
            )
        
    def test_eventi_più_vicini(self):
        '''
        Verifico che gli eventi futuri più vicini siano disposti in modo ordinato
        '''
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('core:cerca_evento'))

        # Ottieni i dati dal contesto della risposta
        eventi_futuri = response.context['eventi_futuri']

        # Assicurati che gli eventi siano ordinati per data
        self.assertTrue(all(
            eventi_futuri[i].data <= eventi_futuri[i + 1].data
            for i in range(len(eventi_futuri) - 1)
        ), "Gli eventi non sono ordinati correttamente")

    def test_migliori_pubblicatori(self):
        '''
        Verifico che i pubblicatori migliori siano ordinati
        '''
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('core:cerca_evento'))

        # Ottieni i dati dal contesto della risposta
        migliori_pubblicatori = response.context['migliori_pubblicatori']

        # Assicurati che i pubblicatori siano ordinati per avg_voto
        self.assertTrue(all(
            migliori_pubblicatori[i].avg_voto >= migliori_pubblicatori[i + 1].avg_voto
            for i in range(len(migliori_pubblicatori) - 1)
        ), "I migliori pubblicatori non sono ordinati correttamente")


    def test_migliori_pubblicatori(self):
        '''
        Verifico che i pubblicatori migliori siano ordinati
        '''
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('core:cerca_evento'))

        # Ottieni i dati dal contesto della risposta
        migliori_pubblicatori = response.context['migliori_pubblicatori']

        # Assicurati che i pubblicatori siano ordinati per avg_voto
        self.assertTrue(all(
            migliori_pubblicatori[i].avg_voto >= migliori_pubblicatori[i + 1].avg_voto
            for i in range(len(migliori_pubblicatori) - 1)
        ), "I migliori pubblicatori non sono ordinati correttamente")

class ListaEventiViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass', is_utente=True)
        self.utente = Utente.objects.create(user=self.user)

        self.user_pubblicatore = User.objects.create_user(username='testpubblicatore', 
                                                        password='testpass', 
                                                        first_name='first_name',
                                                        is_pubblicatore=True
                                                        )
        self.pubblicatore = Pubblicatore.objects.create(
            user = self.user_pubblicatore,
            descrizione='Descrizione del pubblicatore',
            latitudine = 44.72958901676243,
            longitudine = 11.040441132528958,
        )
        self.user_pubblicatore_2 = User.objects.create_user(username='testpubblicatore2', 
                                                        password='testpass', 
                                                        first_name='first_name',
                                                        is_pubblicatore=True
                                                        )
        self.pubblicatore_2 = Pubblicatore.objects.create(
            user = self.user_pubblicatore_2,
            descrizione='Descrizione del pubblicatore',
            latitudine = 44.735,
            longitudine = 11.042,
        )


        #----CREAZIONE EVENTI ASSOCIATI AI PUBBLICATORI----
        self.evento = Evento.objects.create(
            nome="Qualche evento",
            descrizione = "Un qualche evento da qualche parte",
            data = now().date() + timedelta(days=-1),
            max = 100,
            gratis=False,
            costo=20.00,
            pubblicatore=self.pubblicatore
        )

        self.evento_2 = Evento.objects.create(
            nome="Evento votatissimo",
            descrizione = "Evento Votatissimooo",
            data = now().date() + timedelta(days=-3),
            max = 100,
            gratis=False,
            costo=20.00,
            pubblicatore=self.pubblicatore_2
        )
        self.evento_futuro = Evento.objects.create(
            nome="Qualche evento futuro",
            descrizione = "Un qualche evento da qualche parte",
            data = now().date() + timedelta(days=1),
            max = 100,
            gratis=False,
            costo=20.00,
            pubblicatore=self.pubblicatore
        )

        self.evento_futuro_2 = Evento.objects.create(
            nome="Evento votatissimo futuro",
            descrizione = "Evento Votatissimooo",
            data = now().date() + timedelta(days=3),
            max = 100,
            gratis=False,
            costo=20.00,
            pubblicatore=self.pubblicatore_2
        )

        
        #-----CREAZIONE PRENOTAZIONE----
        self.prenotazione = Prenotazione.objects.create(
            utente=self.utente,
            evento=self.evento
        )

        #-----CREAZIONE RECENSIONI----
        diz_utenti = {}

        for i in range(5):
            user = User.objects.create_user(username='testuser'+str(i), password='testpass', is_utente=True)
            utente = Utente.objects.create(user=user)
            diz_utenti[user] = utente
            prenotazione = Prenotazione.objects.create(
                utente=utente,
                evento=self.evento
            )
            Recensione.objects.create(
                data_recensione=now().date(),
                utente = utente,
                evento = self.evento,
                testo = "Ciao" + str(i),
                voto = 1,
                prenotazione = prenotazione
            )
        prenotazione = Prenotazione.objects.create(
                utente=utente,
                evento=self.evento
            )
        Recensione.objects.create(
                data_recensione=now().date(),
                utente = utente,
                evento = self.evento_2,
                testo = "TOP",
                voto = 5,
                prenotazione = prenotazione
            )
        
    def test_ordine_votodesc(self):
        '''
        Verifico che quando l'ordinamento è impostato per i voti decrescenti funzioni correttamente
        '''
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('core:listaeventi') + '?gratuito=&ordinamento=voto_medio&ordine=desc')

        object_list = response.context['object_list']

        eventi = [evento for evento, voto_medio, _ in object_list]
        voti_medi = [voto_medio if voto_medio is not None else 0 for _, voto_medio, _ in object_list]

        self.assertTrue(all(
            voti_medi[i] >= voti_medi[i + 1]
            for i in range(len(voti_medi) - 1)
        ), "Gli eventi trovati non sono ordinati correttamente per i voti decrescenti")

    def test_ordine_votoasc(self):
        '''
        Verifico che quando l'ordinamento è impostato per i voti crescenti funzioni correttamente
        '''
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('core:listaeventi') + '?gratuito=&ordinamento=voto_medio&ordine=asc')

        object_list = response.context['object_list']

        eventi = [evento for evento, voto_medio, _ in object_list]
        voti_medi = [voto_medio if voto_medio is not None else 0 for _, voto_medio, _ in object_list]

        self.assertTrue(all(
            voti_medi[i] <= voti_medi[i + 1]
            for i in range(len(voti_medi) - 1)
        ), "Gli eventi trovati non sono ordinati correttamente per i voti crescenti")

    def test_ordine_costoasc(self):
        '''
        Verifico che quando l'ordinamento è impostato per il costo crescente funzioni correttamente
        '''
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('core:listaeventi') + '?gratuito=&ordinamento=costo&ordine=asc')

        object_list = response.context['object_list']
        eventi = [evento for evento, _, _ in object_list]

        self.assertTrue(all(
            eventi[i].costo <= eventi[i + 1].costo
            for i in range(len(eventi) - 1)
        ), "Gli eventi trovati non sono ordinati correttamente per il costo crescente")

    def test_ordine_costodesc(self):
        '''
        Verifico che quando l'ordinamento è impostato per il costo decrescente funzioni correttamente
        '''
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('core:listaeventi') + '?gratuito=&ordinamento=costo&ordine=desc')

        object_list = response.context['object_list']
        eventi = [evento for evento, _, _ in object_list]

        self.assertTrue(all(
            eventi[i].costo >= eventi[i + 1].costo
            for i in range(len(eventi) - 1)
        ), "Gli eventi trovati non sono ordinati correttamente per il costo decrescente")

    def test_eventi_gratuiti(self):
        '''
        Verifico che quando è selezionato il tipo gratuito, tutti gli eventi siano a costo 0
        '''
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('core:listaeventi') + '?gratuito=True&ordinamento=voto_medio&ordine=asc')

        object_list = response.context['object_list']
        eventi = [evento for evento, _, _ in object_list]

        self.assertTrue(all(
            evento.costo == 0
            for evento in eventi
        ), "Gli eventi trovati non rispettano il filtro 'gratuito'")

    def test_eventi_a_pagamento(self):
        '''
        Verifico che quando è selezionato il tipo a pagamento, tutti gli eventi non siano a costo 0
        '''
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('core:listaeventi') + '?gratuito=False&ordinamento=voto_medio&ordine=asc')

        object_list = response.context['object_list']
        eventi = [evento for evento, _, _ in object_list]

        self.assertTrue(all(
            evento.costo > 0
            for evento in eventi
        ), "Gli eventi trovati non rispettano il filtro 'a pagamento'")

#----------------AUTH TEST----------------
class Permessi(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass', is_utente=True)
        self.utente = Utente.objects.create(user=self.user)

        self.user_pubblicatore = User.objects.create_user(username='testpubblicatore', 
                                                        password='testpass', 
                                                        is_pubblicatore=True
                                                        )
        self.pubblicatore = Pubblicatore.objects.create(
            user = self.user_pubblicatore,
            descrizione='Descrizione del pubblicatore',
            latitudine = 44.72958901676243,
            longitudine = 11.040441132528958,
        )
        
    def test_redirect_to_403_per_utente_normale(self):
        '''
        Verifica che un utente normale venga reindirizzato alla pagina 403 nel caso voglia raggiungere pagine dedicate ai pubblicatori
        '''
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('core:gestisci_eventi'))

        # Verifica che la risposta sia un errore 403 Forbidden
        self.assertEqual(response.status_code, 403)

    def test_redirect_to_403_per_pubblicatore(self):
        '''
        Verifica che un pubblicatore venga reindirizzato alla pagina 403 nel caso voglia raggiungere pagine a lui non accessibili
        '''
        self.client.login(username='testpubblicatore', password='testpass')
        response = self.client.get(reverse('core:cerca_evento'))

        # Verifica che la risposta sia un errore 403 Forbidden
        self.assertEqual(response.status_code, 403)