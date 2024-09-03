from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Evento, Prenotazione, Recensione, Tag
from utenti.models import Pubblicatore
from django.db import transaction


class CreaEventoForm(forms.ModelForm):
    nome = forms.CharField(max_length=50)
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label="Tags"
    )
    descrizione = forms.CharField(max_length=500)
    costo = forms.DecimalField(max_digits=10, decimal_places=2)

    data = forms.DateField(
        widget=forms.SelectDateWidget,
        label="Data dell'Evento",
        required=True
    )

    max = forms.IntegerField(
        label="Numero massimo di Partecipanti",
        min_value=1,
        max_value=200,
        initial=50,
        required=True
    )

    gratis = forms.BooleanField(
        label="Evento Gratuito",
        required=False,
        initial=False
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(CreaEventoForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Evento
        fields = ["nome", "tags", "descrizione", "data", "max", "gratis", "costo"]

    def clean(self):
        cleaned_data = super().clean()
        costo = cleaned_data.get('costo')
        gratis = cleaned_data.get('gratis')
        data_evento = cleaned_data.get('data')

        # Verifica costo
        if costo < 0:
            self.add_error('costo', 'Il costo deve essere maggiore o uguale a 0.')
        elif gratis and costo != 0:
            self.add_error('costo', 'Il costo deve essere 0 se l\'evento è gratuito.')

        # Verifica data non passata
        if data_evento and data_evento < timezone.now().date():
            self.add_error('data', 'La data dell\'evento non può essere passato')

        return cleaned_data

    @transaction.atomic
    def save(self):
        pubblicatore = list(Pubblicatore.objects.filter(user=self.user))[0]
        evento = Evento.objects.create(
            nome=self.cleaned_data["nome"],
            descrizione=self.cleaned_data["descrizione"],
            data=self.cleaned_data["data"],
            costo=self.cleaned_data['costo'],
            max=self.cleaned_data["max"],
            gratis=self.cleaned_data["gratis"],
            pubblicatore=pubblicatore
        )
        for tag in self.cleaned_data["tags"]:
            evento.tags.add(tag)
        evento.save()
        return evento
