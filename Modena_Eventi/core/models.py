from django.utils.timezone import now
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

from utenti.models import *

# Create your models here.

class Tag(models.Model):
    TAG_CHOICES = [
        ("sport", "Sport"),
        ("musicadalvivo", "Musica dal Vivo"),
        ("arteemostre", "Arte e Mostre"),
        ("ciboebevande", "Cibo e Bevande"),
        ("cultura", "Cultura"),
        ("fiere", "Fiere"),
        ("cinema", "Cinema"),
        ("beneficenza", "Beneficenza"),
        ("tecnologia", "Tecnologia"),
        ("discoteca", "Discoteca"),
        ("pub", "Pub"),
        ("naturale", "Naturale"),
        ("petfriendly", "Pet Friendly"),
        ("moda", "Moda"),
    ]

    nome = models.CharField(max_length=50, choices=TAG_CHOICES, unique=True)

    def __str__(self):
        return self.get_nome_display()
    class Meta:
        verbose_name_plural = "Tags"

class Evento(models.Model):
    nome = models.CharField(max_length=50)
    descrizione = models.CharField(max_length=500)

    gratis = models.BooleanField(default=False)
    costo = models.DecimalField(max_digits=10, decimal_places=2)


    tags = models.ManyToManyField(Tag)

    data = models.DateField()

    max = models.IntegerField(default=100)
    n_prenotazioni = models.IntegerField(default=0)

    pubblicatore = models.ForeignKey(Pubblicatore, on_delete=models.CASCADE, related_name="eventi")


    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name_plural = "Eventi"


class Prenotazione(models.Model):
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name="prenotazioni")
    utente = models.ForeignKey(Utente, on_delete=models.PROTECT, blank=True, null=True, default=None, related_name="prenotazioni")

    
    def __str__(self):
        return "Prenotazione di " + self.utente.user.username +  " dell'evento: " + self.evento.nome 
    
    class Meta:
        verbose_name_plural = "Prenotazioni"

    def save(self, *args, **kwargs):
        
        if not self.utente.user.is_utente:
            raise ValueError("Gli eventi sono prenotabili sono dagli utenti registrati!")
        
        super().save(*args, **kwargs)
        
class Recensione(models.Model):
    data_recensione = models.DateField()
    utente = models.ForeignKey("utenti.Utente", on_delete=models.CASCADE, related_name="recensioni")
    evento = models.ForeignKey("Evento", on_delete=models.CASCADE, related_name="recensioni")
    testo = models.TextField()
    voto = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    prenotazione = models.OneToOneField("Prenotazione", on_delete=models.CASCADE, related_name='recensione')
    
    class Meta:
        verbose_name_plural = "Recensioni"

    def clean(self):
        if self.prenotazione.utente != self.utente:
            raise ValueError("Non puoi recensire per altri utenti")
        if not (1 <= int(self.voto) <= 5):
            raise ValidationError('Il voto deve essere compreso tra 1 e 5.')
        if self.evento.data >= now().date():
            raise ValidationError('Non è possibile recensire un evento futuro.')
        if not self.utente.user.is_utente:
            raise ValueError("Solo gli utenti registrati possono lasciare recensioni")
        # Controlla che l'utente non abbia già recensito l'evento
        if Recensione.objects.filter(utente=self.utente, evento=self.evento).exists():
            raise ValidationError('Hai già lasciato una recensione per questo evento.')
        
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        
    
    def __str__(self):
        return f"Recensione di {self.utente}\nVoto: {self.voto}"
    



