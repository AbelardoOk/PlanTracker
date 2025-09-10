from django.urls import path
from . import views

urlpatterns = [
    path("", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("home/", views.home, name="home"),
    path("new_project/", views.register_project, name="register_project"),
    path("<int:project_id>/new_plant/", views.register_plant, name="register_plant"), 
    path("<int:plant_id>/new_visitor/", views.register_visitor, name="register_visitor"),
    path("<int:project_id>/project_details/", views.project_details, name="project_details"),
    path("<int:plant_id>/plant_details/", views.plant_details, name="plant_details"),
    path('project/delete/<int:project_id>/', views.delete_project, name='delete_project'),
    path('plant/delete/<int:plant_id>/', views.delete_plant, name='delete_plant'),
]