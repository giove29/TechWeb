from django.db import models
from django.contrib.auth.models import AbstractUser
#from django.contrib.auth.models import User

# Create your models here.


class User(AbstractUser):
    
    # campi che aiutano a capire se un utente è una struttura o un utente
    is_pubblicatore = models.BooleanField(default=False)
    is_utente = models.BooleanField(default=False)
    img = models.ImageField(upload_to='static/img/users_img/profile_pic', default='static/img/default_img/no_img_profile.jpg')
    
    class Meta:
        verbose_name_plural = "Users"



class Pubblicatore(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    descrizione = models.CharField(max_length=500)
    latitudine = models.FloatField()
    longitudine = models.FloatField()
    numTelefono = models.CharField(max_length=20, default="+393806437638")

    def __str__(self):
        return self.user.first_name + ": " + self.descrizione + " (" + str(self.latitudine) + ", " + str(self.longitudine) + ")"


    class Meta:
        verbose_name_plural = "Pubblicatori"




class Utente(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)

    def __str__(self):
        return self.user.first_name + " " + self.user.last_name


    class Meta:
        verbose_name_plural = "Utenti"