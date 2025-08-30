from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponse
from django.db import models
from .forms import LoginForm, RegisterForm, RegisterProjectForm, FilterProjectForm, RegisterPlantForm, RegisterVisitorForm
from .models import RegisterProjectModel, RegisterPlantModel, RegisterVisitorModel

# login_view <- LoginForm
# A página que aparece ao abrir o site, com opção de preencher dados e fazer o login ou registrar.
def login_view(request):
    if request.user.is_authenticated:
        return redirect("home/")                        
    
    form = LoginForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            # Tenta autenticar usuário e senha
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, f"Bem-vindo(a), {user.username}!")
                return redirect('home/')                
            else:
                messages.error(request, "Usuário ou senha inválidos.")

    return render(request, "PlanTracker/login.html", {"form" : form})

# register_view <- RegisterForm
def register_view(request):
    if request.user.is_authenticated:
        return redirect("home")                      
    
    form = RegisterForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            User.objects.create_user(username=username, email=email, password=password)
            messages.success(request, "Usuário criado com sucesso")
            return redirect("login")
        
    return render(request, "PlanTracker/register.html", {"form" : form})   

# register_project <- RegisterProjectForm <- RegisterProjectModel
@login_required
def register_project(request):

    form = RegisterProjectForm(request.POST)
    if request.method == "POST":
        
        if form.is_valid():
            project = form.save(commit=False)
            project.project_owner = request.user    
            project.save()
            form.save_m2m()                       # Salva os colaboradores
            return redirect("home")                   
    return render(request, "PlanTracker/registerproject.html", {"form" : form})

@login_required
def register_plant(request, project_id):
    project = get_object_or_404(RegisterProjectModel, id=project_id)

    if request.user != project.project_owner and request.user not in project.project_colaborator.all():
        return HttpResponse("Acesso negado", status=403)
    
    form = RegisterPlantForm(request.POST or None, request.FILES or None)
    if request.method == "POST":
        if form.is_valid():
            plant = form.save(commit=False)
            plant.project = project
            plant.save()
            messages.success(request, "Planta adicionada com sucesso")
            return redirect("", project_id=project.id)                   # Leva pro detalhes do projeto, ainda não criado
    return render(request, "PlanTracker/register_plant.html", {"form" : form, "project" : project})

@login_required
def register_visitor(request, plant_id):
    plant = get_object_or_404(RegisterPlantModel, id=plant_id)
    project = plant.project

    if request.user != project.project_owner and request.user not in project.project_colaborator.all():
        return HttpResponse("Acesso negado", status=403)
    
    form = RegisterVisitorForm(request.POST or None, request.FILES or None)
    if request.method == "POST":
        if form.is_valid():
            visitor = form.save(commit=False)
            visitor.plant = plant
            visitor.save()
            messages.success(request, "Visitante adicionado com sucesso")
            return redirect("", project_id=project.id)                   # Leva pro detalhes do projeto, ainda não criado
    return render(request, "PlanTracker/register_visitor.html", {"form" : form, "plant" : plant, "project" : project})

@login_required
def project_details(request, project_id):
    project = get_object_or_404(RegisterProjectModel, id=project_id)

    if request.user != project.project_owner and request.user not in project.project_colaborator.all():
        return HttpResponse("Acesso negado", status=403)
    
    plants = RegisterPlantModel.objects.filter(project=project)

    return render(request, "PlanTracker/project_details.html", {"project":project, "plants":plants})

@login_required
def plant_details(request, plant_id):
    plant = get_object_or_404(RegisterPlantModel, id=plant_id)
    project = plant.project

    if request.user != project.project_owner and request.user not in project.project_colaborator.all():
        return HttpResponse("Acesso negado", status=403)

    visitors = RegisterVisitorModel.objects.filter(plant=plant)

    return render(render, "PlanTracker/plant_details.html", {"plant":plant, "project":project, "visitors":visitors})

#Incompleto
#@login_required
def home(request):
    print("K"*1000)
    print(request.user)
    my_projects = RegisterProjectModel.objects.filter(project_owner=request.user)
    shared_projects = RegisterProjectModel.objects.filter(project_colaborator=request.user)

    form = FilterProjectForm(request.GET or None)
    if form.is_valid():
        if form.cleaned_data['nome']:
            my_projects = my_projects.filter(project_name__icontains=form.cleaned_data['nome'])
        if form.cleaned_data['instituicao']:
            my_projects = my_projects.filter(project_institution__icontains=form.cleaned_data['instituicao'])
    
    context = {"my_projects": my_projects, "shared_projects": shared_projects, "form": form}

    return render(request, "PlanTracker/home.html", context)

# Incompleto
#@login_required
def export_projects(request):
    # Se quiser mudar para exportar qualquer projeto:
    # projects = RegisterProjectModel.objects.filter(models.Q(owner=request.user) | models.Q(colaboradores=request.user)).distinct()
    projects =  RegisterProjectModel.objects.filter(project_owner=request.user)

