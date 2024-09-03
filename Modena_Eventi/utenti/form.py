from django import forms
from .models import *
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.core.validators import RegexValidator
from django.db import transaction
from core.models import *

# crea qui i tuoi Forms

class UtenteSignUpForm(UserCreationForm):
    nome = forms.CharField(required=True)
    cognome = forms.CharField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ["username", "nome", "cognome", "password1", "password2"]

    @transaction.atomic
    def save(self):
        #-----
        user = super().save(commit=False) 
        user.is_utente = True
        user.first_name = self.cleaned_data.get('nome')
        user.last_name = self.cleaned_data.get('cognome')
        user.save()
        #-----
        utente = Utente.objects.create(
            user=user,
            #email=self.cleaned_data.get('email')
        )
        utente.save()
        return user
    
class PubblicatoreSignUpForm(UserCreationForm):
    nome = forms.CharField(label = "Nome del Pubblicatore", required=True)

    descrizione = forms.CharField(label="descrizione",
                                  widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Inserisci una descrizione...'}))
    latitudine = forms.FloatField(label = "latitudine")
    longitudine = forms.FloatField(label="longitudine")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ["username", "nome", "descrizione", "latitudine", "longitudine"]

    @transaction.atomic
    def save(self):
        user = super().save(commit=False) 
        user.is_pubblicatore = True
        user.first_name = self.cleaned_data.get("nome")
        user.save()

        pubblicatore = Pubblicatore.objects.create(
            user = user,
            descrizione = self.cleaned_data.get("descrizione"),
            latitudine = self.cleaned_data.get("latitudine"),
            longitudine = self.cleaned_data.get("longitudine")
        )
        pubblicatore.save()
        
        #----Probabilmente in questa zona dovrà andare la creazione del punto nella mappa collegato 1:1 con i pubblicatori
        return user
    
class UpdateUserForm(forms.ModelForm):
    first_name = forms.CharField(required=True,
                             widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['first_name']
    
class UpdatePubblicatoreForm(forms.ModelForm):
    descrizione = forms.CharField(required=True,
                                  widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Inserisci una descrizione...'}))
    latitudine = forms.FloatField(required=True,
                                  widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Inserisci la latitudine'}))
    longitudine = forms.FloatField(required=True,
                                  widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Inserisci la longitudine'}))

    class Meta:
        model = Pubblicatore
        fields = ["descrizione", "latitudine", "longitudine"]

class CambiaPasswordForm(PasswordChangeForm):
    old_password = forms.CharField(
        label="Password attuale",
        widget=forms.PasswordInput(),
        required=True,
    )
    new_password1 = forms.CharField(
        label="Nuova password",
        widget=forms.PasswordInput(),
    )
    new_password2 = forms.CharField(
        label="Conferma password",
        widget=forms.PasswordInput(),
    )  

    def clean_old_password(self):
        old_password = self.cleaned_data.get("old_password")
        if not self.user.check_password(old_password):
            raise forms.ValidationError("La password attuale non è corretta.")
        return old_password

    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get("new_password1")
        new_password2 = cleaned_data.get("new_password2")

        if new_password1 and new_password2:
            if new_password1 != new_password2:
                raise forms.ValidationError("Le nuove password non coincidono.")
        return cleaned_data

