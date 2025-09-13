from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponse
from django.db import models
import csv
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
        return redirect("home/")                      
    
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
            return redirect("project_details", project_id=project.id)                  # Leva pro detalhes do projeto, ainda não criado
    return render(request, "PlanTracker/register_plant.html", {"form" : form, "project" : project})

@login_required
def delete_plant(request, plant_id):
    plant = get_object_or_404(RegisterPlantModel, id=plant_id)
    project = plant.project # Pega o projeto ao qual a planta pertence

    # Permite a exclusão se o usuário for o dono ou um colaborador
    if request.user != project.project_owner and request.user not in project.project_colaborator.all():
        messages.error(request, "Você não tem permissão para excluir plantas neste projeto.")
        return redirect('project_details', project_id=project.id)

    if request.method == 'POST':
        plant_name = plant.plant_name
        plant.delete()
        messages.success(request, f"A planta '{plant_name}' foi excluída com sucesso.")
        # Redireciona de volta para a página de detalhes do projeto
        return redirect('project_details', project_id=project.id)

    # Se não for POST, apenas redireciona
    return redirect('project_details', project_id=project.id)

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

@login_required
def delete_project(request, project_id):
    project = get_object_or_404(RegisterProjectModel, id=project_id)

    # Apenas o dono do projeto pode deletá-lo
    if request.user != project.project_owner:
        messages.error(request, "Você não tem permissão para excluir este projeto.")
        return redirect('home')

    if request.method == 'POST':
        project_name = project.project_name
        project.delete()
        messages.success(request, f"O projeto '{project_name}' foi excluído com sucesso.")
        return redirect('home')

    # Se o método não for POST, redireciona para a home (medida de segurança)
    return redirect('home')

#@login_required
def home(request):
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

@login_required
def filter_and_export(request):
    form = FilterProjectForm(request.GET or None)
    results = RegisterVisitorModel.objects.select_related('plant__project').all() # Evita N+1 (ou era pra fazer isso)
    
    if form.is_valid():
        name = form.cleaned_data.get("project_name")
        start_date = form.cleaned_data.get("date_from")
        end_date = form.cleaned_data.get("date_to")
        visitor_type = form.cleaned_data.get("type_visitor")
        resource = form.cleaned_data.get("resources")

        if name:
            results = results.filter(plant__project__project_name__icontains=name)
        if start_date:
            results = results.filter(date__gte=start_date)
        if end_date:
            results = results.filter(date__lte=end_date)
        if visitor_type:
            results = results.filter(type_visitor__ic=visitor_type)  # __icontains
        if resource:
            results = results.filter(resources_visitor__ic=resource)  # Qualquer coisa mudar resources_visitor__icontains

    # Se o usuário clicou em "Exportar"
    if "export" in request.GET:
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="export.csv"'
        writer = csv.writer(response)
        writer.writerow(["Registro", "Visitante", "Tipo", "Planta", "Projeto", "Data/Hora", "Localização", "Recursos"])
        for v in results:
            writer.writerow([
                v.visitor_id,
                v.name,
                v.type_visitor,
                f"{v.plant.name} ({v.plant.plant_id})",
                v.plant.project.project_name,
                f"{v.date} {v.time}",
                f"{v.latitude}, {v.longitude}",
                v.resources_visitor,
            ])
        return response

    return render(request, "PlanTracker/filter_page.html", {"form": form, "results": results})