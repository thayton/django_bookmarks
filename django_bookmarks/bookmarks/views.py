from django.db.models import Q
from django.shortcuts import render, get_object_or_404, render_to_response
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import RequestContext
from django.template.loader import get_template
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, InvalidPage

from datetime import datetime, timedelta

from bookmarks.forms import *
from bookmarks.models import *

ITEMS_PER_PAGE = 2

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

    query_set = user.bookmarks.order_by('-id')
    paginator = Paginator(query_set, ITEMS_PER_PAGE)
    
    if request.user.is_authenticated():
        # Is the logged in user already following the 
        # owner of this page?
        is_following = Follow.objects.filter(
            follower=request.user, 
            followed=user
        )
    else:
        is_following = False

    try:
        page_number = int(request.GET['page'])
    except (KeyError, ValueError):
        page_number = 1

    try:
        page = paginator.page(page_number)
    except InvalidPage:
        raise Http404

    vars = {
        'username': username, 
        'bookmarks': page.object_list, 
        'show_tags': True,
        'show_edit': username == request.user.username,
        'show_if_shared': username == request.user.username, # Show if user decide to share this link
        'show_paginator': paginator.num_pages > 1,
        'has_prev': page.has_previous(),
        'has_next': page.has_next(),
        'page': page_number,
        'pages': paginator.num_pages,
        'next_page': page_number + 1,
        'prev_page': page_number - 1,
        'is_following': is_following

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
                password=form.cleaned_data['password1'],
                email=form.cleaned_data['email']
            )
            if 'invitation' in request.session:
                # Retrieve the invitation object
                invitation = Invitation.objects.get(
                    id=request.session['invitation']
                )
                # Delete the invitation from the database and the session.
                invitation.delete()
                del request.session['invitation']

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
    import pdb; pdb.set_trace()
    if form.cleaned_data['share']:
        shared, created = SharedBookmark.objects.get_or_create(
            bookmark=bookmark
        )
        if created:
            shared.users_voted.add(request.user)
            shared.save()

    else:
        # Check if user is un-sharing a bookmark
        shared_bookmark = SharedBookmark.objects.filter(bookmark=bookmark)
        if shared_bookmark:
            shared_bookmark.delete()

    # Save bookmark to database.
    bookmark.save()
    return bookmark

@login_required
def bookmark_save_page(request):
    if request.method == 'POST':
        form = BookmarkSaveForm(request.POST)
        if form.is_valid():
            bookmark = _bookmark_save(request, form)
            if request.is_ajax():
                vars = {
                    'bookmarks': [bookmark],
                    'show_edit': True,
                    'show_tags': True,
                    'show_if_shared': True
                }
                reqc = RequestContext(request, vars)
                return render_to_response('bookmark_list.html', reqc)
            else:
                return HttpResponseRedirect(reverse('user_page', args=(request.user.username,)))
        else:
            if request.is_ajax():
                return HttpResponse(u'failure') # form invalid for ajax 
    elif 'url' in request.GET:
        url = request.GET['url']
        title = ''
        tags = ''
        shared_bookmark = False

        try:
            link = Link.objects.get(url=url)
            bookmark = Bookmark.objects.get(
                link=link,
                user=request.user
            )

            shared_bookmark = SharedBookmark.objects.get(bookmark=bookmark)
            shared_bookmark = True

        except (Link.DoesNotExist, Bookmark.DoesNotExist, SharedBookmark.DoesNotExist):
            pass

        form = BookmarkSaveForm({
                'url': url,
                'title': bookmark.title,
                'tags': ' '.join(tag.name for tag in bookmark.tags.all()),
                'share': shared_bookmark
               })
    else:
        form = BookmarkSaveForm()

    reqc = RequestContext(request, {'form': form})

    if request.is_ajax():
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
            keywords = query.split()
            q = Q()
            for keyword in keywords:
                q = q & Q(title__icontains=keyword)

            form = SearchForm({'query': query})
            bookmarks = Bookmark.objects.filter(q)[:10]

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
    if 'term' in request.GET:
        tags = Tag.objects.filter(
            name__istartswith=request.GET['term']
        )[:10]

        resp = '[%s]' % ', '.join('"%s"' % tag.name for tag in tags)
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
    '''
    Return a list of bookmarks with the most votes.

    TODO: Enable filtering by a date range. Eg, most popular
    during the last week, last 30 days, all time.
    '''
    today = datetime.today()
    yesterday = today - timedelta(1)
    
    shared_bookmarks = SharedBookmark.objects.filter(
        date__gt=yesterday
    )

#    shared_bookmarks = shared_bookmarks.order_by('-votes')[:10]
    shared_bookmarks = SharedBookmark.objects.order_by('-votes')[:10]

    reqc = RequestContext(request, {'shared_bookmarks': shared_bookmarks})
    return render_to_response('popular_page.html', reqc)
    
def following_page(request, username):
    '''
    Return list of users that username is following
    '''
    user = get_object_or_404(User, username=username)
    followed = [ follow.followed for follow in user.following.all() ]

    followed_bookmarks = Bookmark.objects.filter(
        user__in=followed
    ).order_by('-id')

    vars = {
        'username': username,
        'followed': followed,
        'bookmarks': followed_bookmarks[:10],
        'show_tags': True,
        'show_user': True
    }

    reqc = RequestContext(request, vars)
    return render_to_response('following_page.html', reqc)

def followers_page(request, username):
    '''
    Return list of users that follow username
    '''
    user = get_object_or_404(User, username=username)
    followers = [ follow.follower for follow in user.followers.all() ]

    followers_bookmarks = Bookmark.objects.filter(
        user__in=followers
    ).order_by('-id')

    vars = {
        'username': username,
        'followers': followers,
        'bookmarks': followers_bookmarks[:10],
        'show_tags': True,
        'show_user': True
    }

    reqc = RequestContext(request, vars)
    return render_to_response('followers_page.html', reqc)

@login_required
def follow_user(request, username):
    if request.method == 'POST':
        followed_user = get_object_or_404(
            User, username=username
        )

        follow = Follow(
            follower = request.user,
            followed = followed_user
        )
            
        try:
            follow.save()
            messages.info(request,
                          message='You are now following %s.' % followed_user.username
            )
        except:
            # Unique-together constraint violated
            messages.warning(request,
                             message='You are already following %s' % followed_user.username
            )


        if request.is_ajax() or 'X-Requested-With' in request.META:
            # Put messages in here
            return HttpResponse('success')
        else:
            return HttpResponseRedirect(
                reverse('user_page', args=(request.user.username,))
            )
    else:
        vars = {'username': username, 'action': 'follow'}
        reqc = RequestContext(request, vars)
        return render_to_response('follow_user_form.html', reqc)

def unfollow_user(request, username):
    if request.method == 'POST':
        followed_user = get_object_or_404(
            User, username=username
        )

        follow = get_object_or_404(
            Follow,
            follower = request.user,
            followed = followed_user
        )
            
        try:
            follow.delete()
            messages.info(request,
                          message='You are no longer following %s.' % followed_user.username
            )
        except:
            # Unique-together constraint violated
            messages.warning(request,
                             message='You are not following %s' % followed_user.username

            )

        if request.is_ajax() or 'X-Requested-With' in request.META:
            return HttpResponse('success')
        else:
            return HttpResponseRedirect(
                reverse('user_page', args=(request.user.username,))
            )
    else:
        vars = {'username': username, 'action': 'unfollow'}
        reqc = RequestContext(request, vars)
        return render_to_response('follow_user_form.html', reqc)

@login_required
def friend_invite(request):
    if request.method == 'POST':
        form = FriendInviteForm(request.POST)
        if form.is_valid():
            invitation = Invitation(
                name=form.cleaned_data['name'],
                email=form.cleaned_data['email'],
                code=User.objects.make_random_password(20),
                sender=request.user
            )
            invitation.save()

            try:
                invitation.send()
                messages.info(request,
                    message='An invitation was send to %s.' % 
                    invitation.email
                )
            except smtplib.SMTPException:
                messages.error(request,
                    message='An error happened when sending the invitation'
                )
            return HttpResponseRedirect(reverse('invite_friend'))
    else:
        form = FriendInviteForm()

    reqc = RequestContext(request, {
            'form': form
    })
    return render_to_response('friend_invite.html', reqc)

def accept_invite(request, code):
    invitation = get_object_or_404(Invitation, code__exact=code)
    request.session['invitation'] = invitation.id
    return HttpResponseRedirect(reverse('register'))
