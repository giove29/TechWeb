# Modena Eventi
Progetto Web che offre la possibilità di pubblicare, cercare e prenotare eventi.

---
## Struttura del Progetto
```
/Modena_Eventi/
    ├── /core
    ├── /modena_eventi
    ├── /static
    ├── /templates
    └── /utenti
```


---
## Passi di Installazione

Spostati dentro il progetto
```
cd Modena_Eventi/
```
Installa pipenv per la creazione di un'ambiente virtuale
```
pip install pipenv
```
Crea il virtual enviroment 
```
pipenv shell
```
Se non già in possesso, installa le dipendenze (deprecato con pipenv 2024.0.1):
```
pipenv install -r requirements.txt
```
#### Installazione Mauale dei requisiti
```
pipenv shell
pipenv install django
pipenv install django-widget-tweaks
pipenv install folium
```
Blocca le dipendenze:
```
pipenv lock
```

---
## Creazione del Mock DB

Lanciare i seguenti comandi rimanendo nella cartella `Modena_Eventi/`:
```
python manage.py makemigrations
python manage.py migrate
```
Spostati all'interno dell'app "modena_eventi":
```
cd modena_eventi/
```
Trovandoti nel percorso `Modena_Eventi/modena_eventi`, esegui:
```
python setup.py
```
Una volta completato il DB sarà stato creato e correttamente popolato. 

## Esecuzione del Software
Da `Modena_Eventi/`, lanciare il server:
```
python manage.py runserver
```
Il sito sarà accessibile da un browser al seguente indirizzo:
```
http://localhost:8000/
```
---
### Lista Utenti
| Username                  | Password        | Tipo di Utente |
|---------------------------|-----------------|----------------|
| admin                     | passwordadmin   | Admin          |
| Ivan                      | SecurePass123!  | Utente         |
| Giulia                    | SecurePass123!  | Utente         |
| Marco                     | SecurePass123!  | Utente         |
| Luca                      | SecurePass123!  | Utente         |
| Francesca                 | SecurePass123!  | Utente         |
| Davide                    | SecurePass123!  | Utente         |
| Martina                   | SecurePass123!  | Utente         |
| Giuseppe                  | SecurePass123!  | Utente         |
| Valentina                 | SecurePass123!  | Utente         |
| Antonio                   | SecurePass123!  | Utente         |
| Elena                     | SecurePass123!  | Utente         |
| Riccardo                  | SecurePass123!  | Utente         |
| Alessandra                | SecurePass123!  | Utente         |
| Paolo                     | SecurePass123!  | Utente         |
| Ilaria                    | SecurePass123!  | Utente         |
| Emanuele                  | SecurePass123!  | Utente         |
| Silvia                    | SecurePass123!  | Utente         |
| Gabriele                  | SecurePass123!  | Utente         |
| Laura                     | SecurePass123!  | Utente         |
| Stefano                   | SecurePass123!  | Utente         |
| Alice                     | SecurePass123!  | Utente         |
| Pub di Romeo              | password123     | Pubblicatore   |
| Ristorante La Dolce Vita  | password123     | Pubblicatore   |
| Caffè Centrale            | password123     | Pubblicatore   |
| Teatro Comunale           | password123     | Pubblicatore   |
| Museo Ferrari             | password123     | Pubblicatore   |
| Pizzeria Bella Napoli     | password123     | Pubblicatore   |
| Palazzo Ducale            | password123     | Pubblicatore   |
| CinemAstra                | password123     | Pubblicatore   |
| Bar Sport                 | password123     | Pubblicatore   |
| Galleria d'Arte Moderna   | password123     | Pubblicatore   |
| Ristorante Il Gusto       | password123     | Pubblicatore   |
| Mercato Albinelli         | password123     | Pubblicatore   |
| Bistrot Delizia           | password123     | Pubblicatore   |
| Biblioteca Estense        | password123     | Pubblicatore   |
| Brewery Modena            | password123     | Pubblicatore   |
| Pasticceria Dolce Sogno   | password123     | Pubblicatore   |
| Parco Ducale              | password123     | Pubblicatore   |
| Caffè della Storia        | password123     | Pubblicatore   |
| Ristorante L'Oasi         | password123     | Pubblicatore   |
| Centro Commerciale Modena | password123     | Pubblicatore   |
| Osteria del Borgo         | password123     | Pubblicatore   |
| Pizzeria La Bella Napoli  | password123     | Pubblicatore   |
| Gastronomia Modena        | password123     | Pubblicatore   |
| Piazza Grande             | password123     | Pubblicatore   |

