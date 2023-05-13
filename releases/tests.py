'''Django tests'''
from unittest.mock import patch
import tempfile
import os
from datetime import datetime, timedelta
import pytest
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory, override_settings, Client
from django.db import IntegrityError, transaction
from django.contrib.auth.models import User
from django.urls import reverse
from releases.views import index
from releases.data import scrape_wiki, create_dataframe, clean_and_filter
from releases.models import Game, BlacklistedGame

@pytest.mark.django_db
def test_ratelimit():
    '''Testing POST method limit'''
    factory = RequestFactory()
    request = factory.post('/')
    request.limited = True
    setattr(request, 'session', 'session')
    messages = FallbackStorage(request)
    setattr(request, '_messages', messages)
    response = index(request)
    assert response.status_code == 302
    assert response.url == '/'
    messages = list(get_messages(request))
    assert len(messages) == 1
    assert str(messages[0]) == 'Votes limit reached. Please come back later!'

def test_scrape_wiki():
    '''Testing wikipedia tables search'''
    tables = scrape_wiki()
    assert len(tables) > 0

def test_create_dataframe():
    '''Testing wikitables to pandas df transfer'''
    df = create_dataframe()
    assert not df.empty
    assert len(df.columns) == 8

def test_clean_and_filter():
    '''Testing cleaning and filtering data'''
    df = clean_and_filter()
    assert not df.empty
    assert len(df.columns) == 3

possible_date = (datetime.now()+timedelta(days=15)).strftime('%Y-%m-%d')

@pytest.mark.django_db
def test_store_data_duplicated():
    '''Testing data transfer into the database, if there are possible duplicates present'''
    Game.objects.create(date=possible_date, title='Possible duplicate', platforms='NS')
    data = [
        {'Title': 'Possible duplicate', 'Date': f'{possible_date}', 'Platform(s)': 'NS'},
        {'Title': 'Possibly blacklisted', 'Date': f'{possible_date}', 'Platform(s)': 'NS'},
    ]
    for row in data:
        if not BlacklistedGame.objects.filter(title=row['Title']).exists():
            game = Game(date=row['Date'], title=row['Title'], platforms=row['Platform(s)'])
            try:
                with transaction.atomic():
                    game.save()
            except IntegrityError:
                pass
    assert Game.objects.filter(title='Possible duplicate').count() == 1
    assert Game.objects.filter(title='Possibly blacklisted').count() == 1

@pytest.mark.django_db
def test_store_data_blacklisted():
    '''Testing data transfer into the database, if there are possible blacklisted entries present'''
    BlacklistedGame.objects.create(title='Possibly blacklisted')
    Game.objects.create(date=possible_date, title='Possible duplicate', platforms='NS')
    data = [
        {'Title': 'Possible duplicate', 'Date': f'{possible_date}', 'Platform(s)': 'NS'},
        {'Title': 'Possibly blacklisted', 'Date': f'{possible_date}', 'Platform(s)': 'NS'},
    ]
    for row in data:
        if not BlacklistedGame.objects.filter(title=row['Title']).exists():
            game = Game(date=row['Date'], title=row['Title'], platforms=row['Platform(s)'])
            try:
                with transaction.atomic():
                    game.save()
            except IntegrityError:
                pass
    assert Game.objects.filter(title='Possible duplicate').count() == 1
    assert Game.objects.filter(title='Possibly blacklisted').count() == 0

@override_settings(RATELIMIT_RATE='0/s')
@pytest.mark.django_db
def test_voting_system(transactional_db):
    '''Testing voting system'''
    factory = RequestFactory()
    game = Game.objects.create(
        date=possible_date, title='Title example', platforms='NS', votes=0)
    request = factory.post('/', {'game_id': game.id})
    response = index(request)
    game.refresh_from_db()
    assert game.votes == 1

@pytest.mark.django_db
def test_games_ranking(transactional_db):
    '''Testing rating system'''
    game1 = Game.objects.create(
        votes=7, date=possible_date, title='Title example 1', platforms='NS')
    game2 = Game.objects.create(
        votes=1, date=possible_date, title='Title example 2', platforms='NS')
    game3 = Game.objects.create(
        votes=8, date=possible_date, title='Title example 3', platforms='NS')
    game4 = Game.objects.create(
        votes=2, date=possible_date, title='Title example 4', platforms='NS')
    top_games = Game.objects.order_by('-votes')[:3]
    assert list(top_games) == [game3, game1, game4]

@pytest.fixture
def client():
    return Client()

@pytest.fixture
def superuser():
    return User.objects.create_superuser(
        username='test_superuser', password='test_password'
    )

@pytest.mark.django_db
def test_game_delete(client, superuser):
    '''Testing ability to delete entries'''
    client.force_login(superuser)
    game = Game.objects.create(date=possible_date, title='Title example', platforms='NS')
    response = client.get(f'/game/{game.pk}/delete/')
    assert not Game.objects.filter(pk=game.pk).exists()
    assert BlacklistedGame.objects.filter(title=game.title).exists()

@pytest.mark.django_db
def test_game_update(client, superuser):
    '''Testing ability to update entries'''
    client.force_login(superuser)
    game = Game.objects.create(date=possible_date, title='Title example', platforms='NS')
    response = client.post(f'/game/{game.pk}/update/', {
        'date' : possible_date,
        'title': 'Updated title',
        'platforms' : 'NS'
    })
    #we are checking old title (scraped from wikipedia)
    assert BlacklistedGame.objects.filter(title=game.title).exists()
    game.refresh_from_db()
    assert game.title == 'Updated title'

@pytest.mark.django_db
def test_create_backup(client, superuser):
    '''Testing ability to create backup files'''
    client.force_login(superuser)
    url = reverse('backup')
    with tempfile.NamedTemporaryFile() as temp_file:
        with patch('releases.views.call_command') as mock_call_command:
            mock_call_command.side_effect = lambda *args, **kwargs: temp_file.write(b'test')
            response = client.get(url)
            assert response.status_code == 302
            messages = list(get_messages(response.wsgi_request))
            assert len(messages) == 1
            assert str(messages[0]) == 'Restore point created!'

@pytest.mark.django_db
def test_restore(client, superuser):
    '''Testing ability to create restore points list'''
    client.force_login(superuser)
    url = reverse('restore')
    with tempfile.NamedTemporaryFile() as temp_file:
        with patch('releases.views.open') as mock_open:
            mock_open.return_value = temp_file
            response = client.get(url)
            assert response.status_code == 200
            assert 'application/json' in response['Content-Type']

@pytest.mark.django_db
def test_restore_backup(client, superuser):
    '''Testing ability to restore backup points'''
    Game.objects.create(date=possible_date, title='Possible title', platforms='NS')
    BlacklistedGame.objects.create(title='Possibly blacklisted')
    client.force_login(superuser)
    with tempfile.NamedTemporaryFile() as temp_file:
        with patch('releases.views.call_command') as mock_call_command:
            mock_call_command.side_effect = lambda *args, **kwargs: None
            url = reverse('restore_backup', args=[temp_file.name])
            response = client.get(url)
            assert response.status_code == 302
            assert Game.objects.count() == 0
            assert BlacklistedGame.objects.count() == 0

@pytest.mark.django_db
def test_delete_restore_point(client, superuser):
    '''Testing ability to delete restore points'''
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(b'test data')
        temp_file_name = temp_file.name
    assert os.path.exists(temp_file_name)
    client.force_login(superuser)
    url = reverse('delete_restore_point', args=[temp_file_name])
    response = client.get(url)
    assert response.status_code == 302
    assert not os.path.exists(temp_file_name)
