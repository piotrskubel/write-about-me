'''Django views'''
import os
from datetime import datetime
from django_ratelimit.decorators import ratelimit
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.management import call_command
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from .models import Game, BlacklistedGame
from .forms import PlatformForm
from .data import store_data

# pylint: disable=invalid-name
# pylint: disable=no-member
# pylint: disable=unused-argument
def superuser_check(user):
    'Method checking if superuser is logged in'
    return user.is_superuser

@ratelimit(key=lambda g, r: r.META.get('HTTP_X_FORWARDED_FOR', r.META.get(
    'REMOTE_ADDR', '')).split(',')[0].strip(), method=ratelimit.UNSAFE, rate='3/h', block=False)
def index(request):
    'Representation of index view'
    was_limited = getattr(request, 'limited')
    if was_limited is True:
        messages.error(request, 'Votes limit reached. Please come back later!')
        return redirect('index')
    store_data()
    form = PlatformForm(request.GET or None, initial={'platform': ""})
    if form.is_valid():
        platform = form.cleaned_data['platform']
    else:
        platform = ''
    if request.method == 'POST':
        game_id = request.POST.get('game_id')
        if game_id is not None:
            try:
                game_id = int(game_id)
            except ValueError:
                pass
            else:
                try:
                    game = Game.objects.get(id=game_id)
                except Game.DoesNotExist:
                    pass
                else:
                    game.votes += 1
                    game.save()
                    url = reverse('index') + f'?platform={platform}'
                    return redirect(url)
    games = Game.objects.all().order_by('date').filter(platforms__contains=platform)
    top_games = Game.objects.order_by('-votes').filter(platforms__contains=platform)[:3]
    Game.objects.filter(date__lt=datetime.now().date()).delete()
    context = {'games': games, 'top_games': top_games, 'form':form}
    return render(request, 'index.html', context)


@user_passes_test(superuser_check)
def game_delete(request, pk):
    'Game delete view'
    game = get_object_or_404(Game, pk=pk)
    BlacklistedGame.objects.get_or_create(title=game.title)
    game.delete()
    return redirect('index')

@user_passes_test(superuser_check)
def game_update(request, pk):
    'Game update view'
    if request.method == 'POST':
        game = get_object_or_404(Game, pk=pk)
        BlacklistedGame.objects.get_or_create(title=game.title)
        date = request.POST.get('date')
        title = request.POST.get('title')
        platforms = request.POST.get('platforms')
        game.date = date
        game.title = title
        game.platforms = platforms
        game.save()
    return redirect('index')

@user_passes_test(superuser_check)
def delete(request):
    'Reset view'
    Game.objects.all().delete()
    BlacklistedGame.objects.all().delete()
    return redirect('index')

@user_passes_test(superuser_check)
def create_backup(request):
    'Backup view'
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = f'backup_{timestamp}.json'
    call_command('dumpdata', 'releases', output=filename)
    messages.info(request, 'Restore point created!')
    return redirect('index')

@user_passes_test(superuser_check)
def restore(request):
    'Restore points creation'
    backups = [f for f in os.listdir() if f.startswith('backup_') and f.endswith('.json')]
    backups.sort(reverse=True)
    data = []
    for backup in backups:
        url = request.build_absolute_uri(reverse('restore_backup', args=[backup]))
        data.append({'filename': backup, 'url': url})
    return JsonResponse(data, safe=False)

@user_passes_test(superuser_check)
def restore_backup(request, filename):
    'Restore view'
    Game.objects.all().delete()
    BlacklistedGame.objects.all().delete()
    call_command('loaddata', filename)
    return redirect('index')

@csrf_exempt
@user_passes_test(superuser_check)
def delete_restore_point(request, filename):
    'Delete restore points view'
    os.remove(filename)
    return redirect('index')
