'''Django models'''
from django.db import models

class Game(models.Model):
    '''Standard game model'''
    date = models.DateField()
    title = models.CharField(max_length=255, unique=True)
    platforms = models.CharField(max_length=255)
    votes = models.IntegerField(default=0)

class BlacklistedGame(models.Model):
    '''Blacklisted game model'''
    title = models.CharField(max_length=255, unique=True)
