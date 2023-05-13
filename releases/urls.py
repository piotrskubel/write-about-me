'''Django URLs'''
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('game/<int:pk>/delete/', views.game_delete, name='game-delete'),
    path('game/<int:pk>/update/', views.game_update, name='game-update'),
    path('delete', views.delete, name='delete'),
    path('backup/', views.create_backup, name='backup'),
    path('restore/', views.restore, name='restore'),
    path('restore/<str:filename>/', views.restore_backup, name='restore_backup'),
    path('delete_restore_point/<str:filename>/',
        views.delete_restore_point, name='delete_restore_point'),
]
