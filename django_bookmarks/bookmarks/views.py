from django.shortcuts import render, get_object_or_404, render_to_response
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import RequestContext
from django.template.loader import get_template
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.core.urlresolvers import reverse
from bookmarks.forms import *

def main_page(request):
    return render_to_response('main_page.html', {'user': request.user})

def user_page(request, username):
    user = get_object_or_404(User, username=username)
    bookmarks = user.bookmarks.all()

    vars = {'username': username, 'bookmarks': bookmarks}
    reqc = RequestContext(request, vars)

    return render_to_response('user_page.html', reqc)

def logout_page(request):
    logout(request)
    return HttpResponseRedirect(reverse('home'))

def register_page(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
                email=form.cleaned_data['email']
            )
            return HttpResponseRedirect(reverse('home'))
    else:
        form = RegistrationForm()

    reqc = RequestContext(request, {'form': form})
    return render_to_response('registration/register.html', reqc)
