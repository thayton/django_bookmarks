from django.shortcuts import render, get_object_or_404, render_to_response
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import RequestContext
from django.template.loader import get_template
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse

from bookmarks.forms import *
from bookmarks.models import *

def main_page(request):
    return render_to_response('main_page.html', {'user': request.user})

def user_page(request, username):
    user = get_object_or_404(User, username=username)
    bookmarks = user.bookmarks.order_by('-id')

    vars = {'username': username, 'bookmarks': bookmarks, 'show_tags': True}
    reqc = RequestContext(request, vars)

    return render_to_response('user_page.html', reqc)

def tag_page(request, tag_name):
    tag = get_object_or_404(Tag, name=tag_name)
    bookmarks = tag.bookmarks.order_by('-id')

    vars = {
        'bookmarks': bookmarks,
        'tag_name': tag_name,
        'show_tags': True,
        'show_user': True
    }
    reqc = RequestContext(request, vars)

    return render_to_response('tag_page.html', reqc)

def tag_cloud_page(request):
    MAX_WEIGHT = 5
    tags = Tag.objects.order_by('name')

    # Calculate min and max counts for tags
    min_count = max_count = tags[0].bookmarks.count()
    for tag in tags:
        tag.count = tag.bookmarks.count()
        if tag.count < min_count:
            min_count = tag.count
        if tag.count > max_count:
            max_count = tag.count

    # Calculate count rage. Avoid dividing by zero
    range = float(max_count - min_count)
    if range == 0.0:
        range = 1.0

    # Calculate tag weights
    for tag in tags:
        tag.weight = int(
            MAX_WEIGHT * (tag.count - min_count) / range
        )

    vars = {'tags': tags}
    reqc = RequestContext(request, vars)

    return render_to_response('tag_cloud_page.html', reqc)

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
            return HttpResponseRedirect(reverse('register_success'))
    else:
        form = RegistrationForm()

    reqc = RequestContext(request, {'form': form})
    return render_to_response('registration/register.html', reqc)

@login_required
def bookmark_save_page(request):
    if request.method == 'POST':
        form = BookmarkSaveForm(request.POST)
        if form.is_valid():
            # Create or get link
            link, dummy = Link.objects.get_or_create(
                url=form.cleaned_data['url']
            )

            # Create or get bookmark
            bookmark, created = Bookmark.objects.get_or_create(
                user=request.user,
                link=link
            )

            # Update bookmark title
            bookmark.title = form.cleaned_data['title']

            # If the bookmark is being updated, clear old tag list.
            if not created:
                bookmark.tags.clear()

            # Create new tag list.
            tag_names = form.cleaned_data['tags'].split()
            for tag_name in tag_names:
                tag, dummy = Tag.objects.get_or_create(name=tag_name)
                bookmark.tags.add(tag)

            # Save bookmarks to database.
            bookmark.save()
            return HttpResponseRedirect(reverse('user_page', args=(request.user.username,)))
    else:
        form = BookmarkSaveForm()

    reqc = RequestContext(request, {'form': form})
    return render_to_response('bookmark_save.html', reqc)
        
            
