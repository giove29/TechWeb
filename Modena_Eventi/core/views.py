from typing import Any
from django.db.models.query import QuerySet
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Count, Avg
from django.db.models.functions import Round
from django.http import HttpResponseRedirect

from django.views.generic.list import ListView
from django.views.generic import TemplateView, DetailView
from django.urls import reverse

from .recommendations import *
from datetime import datetime
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

from .models import *
from .form import CreaEventoForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from utenti.models import Pubblicatore, Utente

from datetime import datetime
from django.utils.timezone import now
import folium
import logging
logger = logging.getLogger(__name__)


#-------Permessi-------

class UtenteNormale(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        
        if request.user.is_pubblicatore:
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)
    

class UtentePubblicatore(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        
        if request.user.is_utente:
            raise PermissionDenied
        
        return super().dispatch(request, *args, **kwargs)
    

#-------CBV-------

class ListaEventiView(ListView):
    model = Evento
    template_name = "core/listaeventi.html"
    context_object_name = "object_list"
    paginate_by = 9

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_pubblicatore:
            raise PermissionDenied

        # Verifica la logica di redirect qui
        gratis = self.request.GET.get("gratuito")
        ordinamento = self.request.GET.get("ordinamento", "voto_medio")
        if gratis == 'True' and ordinamento == 'costo':
            # Esegui il redirect se i parametri di filtro non sono compatibili
            return redirect(reverse('core:cerca_evento') + '?filtro=no')

        return super().dispatch(request, *args, **kwargs)

    def get_model_name(self):
        return self.model._meta.verbose_name_plural

    def get_queryset(self):
        queryset = Evento.objects.all()

        # Filtraggio per tags (logica OR)
        tags = self.request.GET.getlist("tags")
        print(tags)
        if tags:
            tag_filters = Q()
            for tag in tags:
                tag="pet friendly" if tag=="petfriendly" else tag
                tag="musica dal vivo" if tag=="musicadalvivo" else tag
                tag="arte e mostre" if tag=="arteemostre"else tag
                tag="cibo e bevande" if tag=="ciboebevande"else tag
                
                tag_filters |= Q(tags__nome=tag)
            queryset = queryset.filter(tag_filters).distinct()

        # Filtraggio per gratuità
        gratis = self.request.GET.get("gratuito")
        if gratis in ['True', 'False']:
            queryset = queryset.filter(gratis=(gratis == 'True'))

        # Ordinamento
        ordinamento = self.request.GET.get("ordinamento", "voto_medio")
        ordine = self.request.GET.get("ordine", "asc")

        queryset = queryset.annotate(voto_medio=Avg('recensioni__voto'))

        if ordinamento:
            queryset = queryset.order_by(f'-{ordinamento}' if ordine == "desc" else ordinamento)
        else:
            queryset = queryset.order_by('-voto_medio')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Conserva i parametri attuali del filtro per i link di paginazione
        get_params = self.request.GET.copy()
        page = get_params.pop('page', None)  # Rimuovi il parametro della pagina attuale
        context['get_params'] = get_params.urlencode()  # Codifica i parametri rimanenti

        # Aggiungi le informazioni sulla prenotazione
        if self.request.user.is_authenticated:
            try:
                utente = Utente.objects.get(user=self.request.user)
            except Utente.DoesNotExist:
                utente = None

            if utente:
                prenotazioni = Prenotazione.objects.filter(utente=utente)
                prenotati_ids = prenotazioni.values_list('evento_id', flat=True)
            else:
                prenotati_ids = []
        else:
            prenotati_ids = []

        # Data odierna
        today_date = now().date()

        context['prenotati_ids'] = prenotati_ids
        context['today_date'] = today_date
        context['object_list'] = [(evento, evento.voto_medio, today_date) for evento in context['object_list']]
        context["tipi_tags"] = Tag.TAG_CHOICES
        return context
    
class PrenotazioneConfermataView(UtenteNormale, TemplateView):
    template_name = "core/prenotazione_confermata.html"

    def post(self, request, *args, **kwargs):
        user = self.request.user
        utente = get_object_or_404(Utente, user=user)

        id_evento = request.POST.get('id')
        evento = get_object_or_404(Evento, pk=id_evento)

        if Prenotazione.objects.filter(
            utente = utente,
            evento = evento
        ).exists():
            return redirect(reverse('core:visualizza_pubblicatore', args=[evento.pubblicatore_id]) + '?prenotazione=esistente')
        
        Prenotazione.objects.create(
            utente = utente,
            evento = evento
        )

        context = self.get_context_data()
        context["evento"] = evento

        return self.render_to_response(context)
    
class PrenotazioniUtenteView(TemplateView):
    template_name = "core/prenotazioni_utente.html"
    paginate_by = 5

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        utente = Utente.objects.get(user=user)

        now = timezone.localtime(timezone.now())
        eventi_passati = Evento.objects.filter(data__lt=now.date())
        eventi_futuri = Evento.objects.filter(data__gt=now.date())

        prenotazioni_future = Prenotazione.objects.filter(
            evento__in=eventi_futuri,
            utente__user=user
        ).order_by("evento__data")
        prenotazioni_passate = Prenotazione.objects.filter(
            evento__in=eventi_passati,
            utente__user=user
        ).order_by("-evento__data")

        prenotazioni_dict = {}
        for prenotazione in prenotazioni_passate:
            try:
                recensione = Recensione.objects.get(utente=utente, evento=prenotazione.evento)
                voto = recensione.voto
            except Recensione.DoesNotExist:
                voto = None
            prenotazioni_dict[prenotazione] = voto

        # Paginator per prenotazioni passate
        paginator_passate = Paginator(list(prenotazioni_dict.items()), self.paginate_by)
        page_passate = self.request.GET.get('page_passate')
        try:
            prenotazioni_passate_paginati = paginator_passate.page(page_passate)
        except PageNotAnInteger:
            prenotazioni_passate_paginati = paginator_passate.page(1)
        except EmptyPage:
            prenotazioni_passate_paginati = paginator_passate.page(paginator_passate.num_pages)

        # Paginator per prenotazioni future
        paginator_future = Paginator(prenotazioni_future, self.paginate_by)
        page_future = self.request.GET.get('page_future')
        try:
            prenotazioni_future_paginati = paginator_future.page(page_future)
        except PageNotAnInteger:
            prenotazioni_future_paginati = paginator_future.page(1)
        except EmptyPage:
            prenotazioni_future_paginati = paginator_future.page(paginator_future.num_pages)

        context["prenotazioni_passate"] = prenotazioni_passate_paginati
        context["prenotazioni_passate_page_obj"] = prenotazioni_passate_paginati
        context["prenotazioni_future"] = prenotazioni_future_paginati
        context["prenotazioni_future_page_obj"] = prenotazioni_future_paginati
        context["range"] = range(1, 6)  # Lista di numeri per le stelle

        return context

class PrenotazioniPubblicatoreView(UtentePubblicatore, TemplateView):
    template_name = "core/prenotazioni_pubblicatore.html"
    paginate_by = 7

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        pubblicatore = get_object_or_404(Pubblicatore, user = user)
        prenotazioni = Prenotazione.objects.filter(evento__pubblicatore=pubblicatore).order_by("-evento__data")
        
        now = timezone.localtime(timezone.now())
        prenotazioni_dict = {
            prenotazione: prenotazione.evento.data > now.date() 
            for prenotazione in prenotazioni
        }

        paginator = Paginator(list(prenotazioni_dict.items()), self.paginate_by)
        page = self.request.GET.get('page')

        try:
            prenotazioni_paginati = paginator.page(page)
        except PageNotAnInteger:
            prenotazioni_paginati = paginator.page(1)
        except EmptyPage:
            prenotazioni_paginati = paginator.page(paginator.num_pages)

        
        context['prenotazioni'] = dict(prenotazioni_paginati)
        context['page_obj'] = prenotazioni_paginati

        return context


class DetailEventoView(LoginRequiredMixin, ListView):
    model = Recensione
    template_name = "core/visualizza_evento.html"
    context_object_name = "recensioni"
    paginate_by = 4

    def get_queryset(self):
        self.evento = get_object_or_404(Evento, pk=self.kwargs['pk'])
        return Recensione.objects.filter(evento=self.evento).order_by("-voto")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.evento

        # Verifica se l'utente ha già prenotato l'evento
        user = self.request.user
        evento_prenotato = Prenotazione.objects.filter(evento=self.evento, utente__user=user).exists()
        context["evento_prenotato"] = evento_prenotato

        # Calcola il numero di posti occupati
        posti_occupati = self.evento.prenotazioni.count()
        max_posti = self.evento.max
        context["posti_occupati"] = posti_occupati
        context["max_posti"] = max_posti

        # Controlla se i posti sono esauriti
        context["posti_esauriti"] = posti_occupati >= max_posti

        #---Recommendations System
        suggested_eventi = get_recommendations_for_evento(self.evento)
        suggested_eventi_dict = {}
        for evento in suggested_eventi:
            voto_medio = round(Recensione.objects.filter(evento_id=evento.id).aggregate(Avg('voto'))['voto__avg'],1)
            if voto_medio is None:
                voto_medio = "-"
            suggested_eventi_dict[evento] = voto_medio
        
        context['suggested_eventi'] =  list(suggested_eventi_dict.items())

        voto_medio = self.get_queryset().aggregate(media=Avg("voto"))["media"]
        if voto_medio is None:
            voto_medio = "-"
        else:
            voto_medio = round(voto_medio, 1)
        context["voto_medio"] = voto_medio

        # Aggiungi la data odierna al contesto
        context["today_date"] = now().date().strftime('%Y-%m-%d')

        # ---Mappa
        mappa = folium.Map(location=[self.evento.pubblicatore.latitudine, self.evento.pubblicatore.longitudine], zoom_start=13)
        folium.Marker(
            location=[self.evento.pubblicatore.latitudine, self.evento.pubblicatore.longitudine],
            popup=f"{self.evento.pubblicatore.user.first_name}: {self.evento.pubblicatore.descrizione}",
            icon=folium.Icon(color="blue", icon="exclamation-sign")
        ).add_to(mappa)
        mappa_html = mappa._repr_html_()

        context["mappa_html"] = mappa_html
        # --------

        return context


class DetailPubblicatoreView(UtenteNormale, DetailView):
    template_name = "core/visualizza_pubblicatore.html"

    def get(self, request, pk):
        pubblicatore = get_object_or_404(Pubblicatore, pk=pk)

        # Ottieni gli eventi prenotati dall'utente
        eventi_prenotati = Prenotazione.objects.filter(utente__user=request.user).values_list('evento_id', flat=True)
        eventi_prenotati_ids = set(eventi_prenotati)

        # Ottieni la data corrente
        now = timezone.now()

        # Filtra gli eventi passati e futuri
        eventi_passati = pubblicatore.eventi.filter(data__lt=now)
        eventi_futuri = pubblicatore.eventi.filter(data__gte=now)

        # ---Mappa
        mappa = folium.Map(location=[pubblicatore.latitudine, pubblicatore.longitudine], zoom_start=13)
        folium.Marker(
            location=[pubblicatore.latitudine, pubblicatore.longitudine],
            popup=f"{pubblicatore.user.first_name}: {pubblicatore.descrizione}",
            icon=folium.Icon(color="blue", icon="exclamation-sign")
        ).add_to(mappa)
        mappa_html = mappa._repr_html_()
        # --------

        return render(request, self.template_name, {
            'object': pubblicatore,
            'mappa_html': mappa_html,
            'eventi_prenotati_ids': eventi_prenotati_ids,
            'eventi_passati': eventi_passati,
            'eventi_futuri': eventi_futuri,
        })


    
class CercaEvento(ListView):
    model = Evento
    template_name = "core/cerca_evento.html"
    context_object_name = 'eventi'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_pubblicatore:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        tags = self.request.GET.getlist("tag", [])

        if tags:
            queryset = Evento.objects.filter(tags__name__in=tags).distinct()
        else:
            queryset = Evento.objects.all()

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tags_query"] = self.request.GET.getlist("tag", [])
        context["tipi_tags"] = Tag.TAG_CHOICES

        #----Folium Map

        pubblicatori = Pubblicatore.objects.all()

        if pubblicatori:
            avg_lat = sum([p.latitudine for p in pubblicatori]) / len(pubblicatori)
            avg_lon = sum([p.longitudine for p in pubblicatori]) / len(pubblicatori)
        else:
            avg_lat, avg_lon = 0, 0
        
        mappa = folium.Map(location=[avg_lat, avg_lon], zoom_start=13)

        for pub in pubblicatori:
            pubblicatore_url = reverse('core:visualizza_pubblicatore', args=[pub.pk])
            popup_content = folium.Popup(f'<a href="{pubblicatore_url}" target="_blank">{pub.user.first_name}: {pub.descrizione}</a>')
            folium.Marker(
                location=[pub.latitudine, pub.longitudine],
                popup=popup_content,
                icon=folium.Icon(color="blue", icon="exclamation-sign")
            ).add_to(mappa)
        
        mappa_html = mappa._repr_html_()

        context['mappa_html'] = mappa_html
        #--------------

        # Aggiungi i migliori pubblicatori in base alla media delle loro recensioni
        context['migliori_pubblicatori'] = get_recommended_pubblicatori_by_reviews()

        # Migliori Eventi per Tag (futuri)
        #se l'utente è autenticato allora passo alla funzione "get_recommended_eventi_by_tags" l'istanza di Utente, altrimenti None
        if self.request.user.is_authenticated:
            try:
                utente_instance = Utente.objects.get(user=self.request.user)
            except Utente.DoesNotExist:
                utente_instance = None
        else:
            utente_instance = None

        context['eventi_per_tag'] = get_recommended_eventi_by_tags(utente_instance)

        # Eventi Futuri più Vicini
        eventi_futuri = Evento.objects.filter(data__gte=now().date()).order_by('data')[:5].annotate(avg_voto=Avg('recensioni__voto'))
        context['eventi_futuri'] = eventi_futuri


        return context

class ListaEventiPerPubblicatoreView(UtentePubblicatore, ListView):
    model = Evento
    template_name = "core/lista_eventi_per_pubblicatore.html"
    context_object_name = 'object_list'

    def get_model_name(self):
        return self.model._meta.verbose_name_plural
    
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Evento.objects.none()
        
        self.pubblicatore = get_object_or_404(Pubblicatore, user=user)
        queryset = Evento.objects.filter(pubblicatore=self.pubblicatore).annotate(voto_medio=Round(Avg("recensioni__voto"), 1))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pubblicatore"] = self.pubblicatore
        context["title"] = "Gestisci Eventi"

        context["object_list"] = [
            {
                "evento": evento,
                "voto_medio": evento.voto_medio
            } for evento in context["object_list"]
        ]
        return context

class RecensioniEventoView(UtentePubblicatore, ListView):
    model = Recensione
    template_name = "core/recensioni_evento.html"
    context_object_name = 'recensioni'
    paginate_by = 5

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_pubblicatore:
            raise PermissionDenied
        
        evento_id = self.kwargs["evento_id"]
        evento = get_object_or_404(Evento, id = evento_id)

        pubblicatore = get_object_or_404(Pubblicatore, user=request.user)
        if evento.pubblicatore != pubblicatore:
            raise PermissionDenied
        
        self.evento = evento
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Recensione.objects.filter(evento=self.evento).order_by("-data_recensione")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["evento"] = self.evento
        voto_medio = self.get_queryset().aggregate(media=Avg("voto"))["media"]
        if voto_medio is None:
            voto_medio = "-"
        else:
            voto_medio = round(voto_medio, 1)
        context["voto_medio"] = voto_medio
        return context


#-------FBV-------

def create_evento(request):
    if not request.user.is_authenticated or not request.user.is_pubblicatore:
        raise PermissionDenied
    
    if request.method == "POST":
        form = CreaEventoForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            form.save()
            return redirect(reverse("core:gestisci_eventi") + "?created=ok")
        else:
            return render(request, "core/crea_evento.html", {"form": form})
    else:
        form = CreaEventoForm(user=request.user)
    return render(request, "core/crea_evento.html", {"form": form})

def elimina_evento(request, pk):
    print(request.method)
    if request.method == "POST":
        evento = get_object_or_404(Evento, pk=pk)
        #forse c'è bisogno di un try-except
        pubblicatore = evento.pubblicatore

        if pubblicatore.user != request.user:
            raise PermissionDenied
        
        evento.delete()
        return redirect(reverse("core:gestisci_eventi") + "?deleted=ok")
    raise PermissionDenied

def elimina_prenotazione(request, pk):
    prenotazione = get_object_or_404(Prenotazione, pk=pk)

    if not request.user.is_authenticated:
        raise PermissionDenied
    
    if request.user.is_pubblicatore:
        pubblicatore = prenotazione.evento.pubblicatore
        if pubblicatore.user != request.user:
            raise PermissionDenied
        
        prenotazione.delete()
        return redirect(reverse('core:prenotazioni_pubblicatore') + '?prenotazionedeleted=ok')

    if request.user.is_utente:
        utente = prenotazione.utente
        if utente.user != request.user:
            raise PermissionDenied
    
        prenotazione.delete()
        return redirect(reverse('core:prenotazioni_utente') + '?prenotazionedeleted=ok')

    return redirect('/') 

def home_page(request):
    user = request.user

    if user.is_pubblicatore:
        return redirect("core:gestisci_eventi")
    else:
        return redirect("core:cerca_evento")
    
def salva_recensione(request, prenotazione_id):

    if not request.user.is_authenticated:
        raise PermissionDenied
    
    if request.user.is_pubblicatore:
        raise PermissionDenied 
    
    prenotazione = get_object_or_404(Prenotazione, id=prenotazione_id)
    utente = get_object_or_404(Utente, user=request.user)


    if prenotazione.utente != utente:
        raise PermissionDenied
    
    if request.method == "POST":
        voto = request.POST.get("voto")
        testo = request.POST.get('testo')
        oggi = timezone.localdate()
        recensione = Recensione(
            prenotazione = prenotazione,
            voto = voto,
            testo = testo,
            data_recensione = oggi,
            utente = utente,
            evento = prenotazione.evento
        )
        try:
            recensione.save()
            return redirect(reverse("core:prenotazioni_utente") + "?review=ok")
        except Exception as e:
            print(str(e))
            return redirect(reverse("core:prenotazioni_utente") + "?review=no")
        
    return redirect('core:prenotazioni_utente')

