from django.shortcuts import render, get_object_or_404, render_to_response
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import RequestContext
from django.template.loader import get_template
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse

from datetime import datetime, timedelta

from bookmarks.forms import *
from bookmarks.models import *

def main_page(request):
    shared_bookmarks = SharedBookmark.objects.order_by('-date')[:10]
    vars = {
        'user': request.user,
        'shared_bookmarks': shared_bookmarks
    }
    reqc = RequestContext(request, vars)

    return render_to_response('main_page.html', reqc)

def user_page(request, username):
    user = get_object_or_404(User, username=username)
    bookmarks = user.bookmarks.order_by('-id')

    vars = {
        'username': username, 
        'bookmarks': bookmarks, 
        'show_tags': True,
        'show_edit': username == request.user.username
    }
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

def _bookmark_save(request, form):
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

    # Share on the main page if requested
    if form.cleaned_data['share']:
        shared, created = SharedBookmark.objects.get_or_create(
            bookmark=bookmark
        )
        if created:
            shared.users_voted.add(request.user)
            shared.save()

    # Save bookmark to database.
    bookmark.save()
    return bookmark

@login_required
def bookmark_save_page(request):
    ajax = 'ajax' in request.GET

    if request.method == 'POST':
        form = BookmarkSaveForm(request.POST)
        if form.is_valid():
            bookmark = _bookmark_save(request, form)
            if ajax:
                vars = {
                    'bookmarks': [bookmark],
                    'show_edit': True,
                    'show_tags': True
                }
                reqc = RequestContext(request, vars)
                return render_to_response('bookmark_list.html', reqc)
            else:
                return HttpResponseRedirect(reverse('user_page', args=(request.user.username,)))
        else:
            if ajax:
                return HttpResponse(u'failure') # form invalid for ajax 
    elif 'url' in request.GET:
        url = request.GET['url']
        title = ''
        tags = ''
        try:
            link = Link.objects.get(url=url)
            bookmark = Bookmark.objects.get(
                link=link,
                user=request.user
            )
        except (Link.DoesNotExist, Bookmark.DoesNotExist):
            pass

        form = BookmarkSaveForm({
                'url': url,
                'title': bookmark.title,
                'tags': ' '.join(tag.name for tag in bookmark.tags.all())
               })
    else:
        form = BookmarkSaveForm()

    reqc = RequestContext(request, {'form': form})

    if ajax:
        return render_to_response('bookmark_save_form.html', reqc)
    else:
        return render_to_response('bookmark_save.html', reqc)
        
def search_page(request):
    form = SearchForm()
    bookmarks = []
    show_results = False
    if 'query' in request.GET:
        show_results = True
        query = request.GET['query'].strip()
        if query:
            form = SearchForm({'query': query})
            bookmarks = Bookmark.objects.filter(
                title__icontains=query
            )[:10]
    vars = {
        'form': form,
        'bookmarks': bookmarks,
        'show_results': show_results,
        'show_tags': True,
        'show_user': True
    }
    reqc = RequestContext(request, vars)

    if request.GET.has_key('ajax'):
        return render_to_response('bookmark_list.html', reqc)
    else:
        return render_to_response('search.html', reqc)

def ajax_tag_autocomplete(request):
    print 'ajax_tag_autocomplete called'
    if 'term' in request.GET:
        tags = Tag.objects.filter(
            name__istartswith=request.GET['term']
        )[:10]
        resp = '[%s]' % ', '.join('"%s"' % tag.name for tag in tags)
        print resp
        return HttpResponse(resp)
    return HttpResponse()

@login_required
def bookmark_vote_page(request):
    if 'id' in request.GET:
        try:
            id = request.GET['id']
            shared_bookmark = SharedBookmark.objects.get(id=id)
            user_voted = shared_bookmark.users_voted.filter(
                username=request.user.username
            )
            if not user_voted:
                shared_bookmark.votes += 1
                shared_bookmark.users_voted.add(request.user)
                shared_bookmark.save()
        except SharedBookmark.DoesNotExist:
            raise Http404('Bookmark not found.')

        if 'HTTP_REFERER' in request.META:
            return HttpResponseRedirect(request.META['HTTP_REFERER'])
        return HttpResponseRedirect('/')

def popular_page(request):
    today = datetime.today()
    yesterday = today - timedelta(1)
    
    shared_bookmarks = SharedBookmark.objects.filter(
        date__gt=yesterday
    )
    shared_bookmarks = shared_bookmarks.order_by('-votes')[:10]

    reqc = RequestContext(request, {'shared_bookmarks': shared_bookmarks})
    return render_to_response('popular_page.html', reqc)
    
