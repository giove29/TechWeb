from django.views.generic import CreateView
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.crypto import get_random_string
from django.core.exceptions import PermissionDenied
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordChangeView
from django.contrib import messages
from django.contrib.auth import login, logout,authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import render, redirect
from .models import *
from utenti.form import *
from django.urls import reverse
from django.contrib.auth.decorators import login_required

# Create your views here.


def register(request):
    if request.user.is_authenticated:
        raise PermissionDenied
    return render(request, 'utenti/register.html')

def PubblicatoreUpdateView(request):       
    if not request.user.is_authenticated:
        raise PermissionDenied
    
    if not request.user.is_pubblicatore:
        raise PermissionDenied
    
    pubblicatore = get_object_or_404(Pubblicatore, user = request.user)

    initial_data = {
        "init_nome": request.user.first_name,
        "init_descrizione": pubblicatore.descrizione,
        "init_latitudine": pubblicatore.latitudine,
        "init_longitudine": pubblicatore.longitudine,
        "init_numTelefono": pubblicatore.numTelefono
    }
    print(initial_data)
    
    if request.method == "POST":
        pubblicatore_form = UpdatePubblicatoreForm(request.POST, instance=pubblicatore)
        user_form = UpdateUserForm(request.POST, request.FILES, instance=request.user)

        if user_form.is_valid() and pubblicatore_form.is_valid():
            pubblicatore_form.save()
            user_form.save()
            return redirect("/users/profile/?modified=ok")
        else:
            error_fields = [
                field
                for form in [pubblicatore_form, user_form]
                for field, error_list in form.errors.as_data().items()
                if error_list
            ]
            error_params = '&'.join(f'{field}=no' for field in error_fields)
            return redirect(f'/users/profile/?modified=no&{error_params}')
    else:
        #Utente non ha campi da modificare se non il nome di user
        initial_data["init_cognome"] = request.user.last_name
        initial_data["img"] = request.user.img
        user_form = UpdateUserForm(instance=request.user)

    return render(request, "utenti/edit_profile_pubblicatore.html",
                  {
                      "user_form": user_form,
                      "initial_data": initial_data
                  }
                  )

def UtenteUpdateView(request):
    if not request.user.is_authenticated:
        raise PermissionDenied
    
    if not request.user.is_utente:
        raise PermissionDenied
    
    utente = get_object_or_404(Utente, user=request.user)
    initial_data = {
        'init_nome': request.user.first_name,
        'init_cognome': request.user.last_name
    }

    if request.method == 'POST':
        user_form = UpdateUserForm(request.POST, request.FILES, instance=request.user)
        if user_form.is_valid():
            print(user_form)
            user_form.save()
            return redirect('/users/profile/?modified=ok')
        else:
            error_fields = [
                field
                for field, error_list in user_form.errors.as_data().items()
                if error_list
            ]
            error_params = '&'.join(f'{field}=no' for field in error_fields)
            return redirect(f'/users/profile/?modified=no&{error_params}')
    else:
        user_form = UpdateUserForm(instance=request.user)

    return render(request, "utenti/edit_profile_utente.html",
                  {
                      "user_form": user_form,
                      "initial_data": initial_data
                  }
                  )

class UtenteRegistrationView(CreateView):
    model = User
    form_class = UtenteSignUpForm
    template_name = 'utenti/utente_register.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('/core/cercaevento/?registration=ok')
    
class PubblicatoreRegistrationView(CreateView):
    model = User
    form_class = PubblicatoreSignUpForm
    template_name = "utenti/pubblicatore_register.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('/core/gestiscieventi/?registration=ok')
    
#----LOGIN----
    
def login_request(request):
    if request.user.is_authenticated:
        raise PermissionDenied
    next_url = request.GET.get('next') or request.POST.get('next') or '/?login=ok'

    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                if next_url:
                    return redirect(next_url)

            else:
                messages.error(request, "Username o password sbagliati.")
        else:
            messages.error(request, "Username o password sbagliati.")
    
    return render(request, 'utenti/login.html', context={'form': AuthenticationForm(), 'next': next_url}) 

@login_required
def logout_request(request):
    logout(request)
    return redirect('/?logout=ok')

@login_required
def view_profile(request):
    user = get_object_or_404(User, pk=request.user.pk)
    
    if user.is_utente:
        profile_data = {
            'user': user,
            'utente': get_object_or_404(Utente, user=user)
        }
    elif user.is_pubblicatore:
        admin_email = User.objects.filter(is_staff=True).values_list('email', flat=True).first()

        profile_data = {
            'user': user,
            'pubblicatore': get_object_or_404(Pubblicatore, user=user),
            'admin_email' : admin_email
        }

    return render(request, 'utenti/profile_detail.html', profile_data)

@login_required
def update_profile(request):
    user = request.user
    if user.is_utente:
        utente_view = UtenteUpdateView
        return utente_view(request)
    elif user.is_pubblicatore:
        pubblicatore_view = PubblicatoreUpdateView
        return pubblicatore_view(request)
    else:
        raise Exception("Errore")

@login_required
def cambia_password(request):
    
    if request.method == 'POST':
        form = CambiaPasswordForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  
            return redirect(reverse('utenti:view_profile') + '?changed=ok')
    else:
        form = CambiaPasswordForm(request.user)

    return render(request, 'utenti/cambia_password.html', {'form': form})