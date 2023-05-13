'''Methods importing and storing data'''
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import pandas as pd
from django.db import IntegrityError
from .models import Game, BlacklistedGame

# pylint: disable=invalid-name
current_year = str(datetime.now().year)

def scrape_wiki():
    '''Method looking for wikipedia tables'''
    url = f'https://en.wikipedia.org/wiki/{current_year}_in_video_games'
    html = requests.get(url, timeout=30).content
    soup = BeautifulSoup(html, 'html.parser')
    tables = soup.find_all('table', {'class': 'wikitable'})
    return tables

def create_dataframe():
    '''Method converting wikitables to pandas df'''
    result = pd.DataFrame()
    tables = scrape_wiki()
    for table in tables:
        headers = [header.text.strip() for header in table.find_all('th')]
        if all(key in headers for key in ['Title', 'Month', 'Day', 'Platform(s)']):
            read_df = pd.read_html(str(table))[0]
            result = pd.concat([result, read_df], ignore_index=True)
    return result

def clean_and_filter():
    '''Method cleaning and filtering data'''
    result = create_dataframe()
    result['Month'] = result['Month'].str.replace(' ', '')
    platforms = '|'.join(['NS', 'XSX', 'PS5', 'XBO', 'PS4', 'Win'])
    result = result[result['Platform(s)'].str.contains(platforms) & (result['Day'] != 'TBA')]
    result['Date'] = (current_year + '-' + result['Month'].astype(str).apply(
        lambda x: datetime.strptime(x, '%B').strftime('%m'))
        + '-' + result['Day'].astype(int).astype(str))
    result['Date'] = pd.to_datetime(result['Date'], format='%Y-%m-%d')
    result['Title'] = result['Title'].str.replace(r'\[[a-z]\]', '', regex=True)
    result = result[['Date', 'Title', 'Platform(s)']]
    today = datetime.now()
    end_date = today + timedelta(weeks=8)
    result = result[(result['Date'] >= today) & (result['Date'] <= end_date)]
    return result

def store_data():
    '''Method transfering entries into the database'''
    data = clean_and_filter()
    for _, row in data.iterrows():
        # pylint: disable=no-member
        if not BlacklistedGame.objects.filter(title=row['Title']).exists():
            game = Game(date=row['Date'], title=row['Title'], platforms=row['Platform(s)'])
            try:
                game.save()
            except IntegrityError:
                pass
