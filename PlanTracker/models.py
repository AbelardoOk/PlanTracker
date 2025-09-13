from django.db import models
from django.contrib.auth.models import User
from django.db.models import Max
from unidecode import unidecode
from django.utils import timezone

class RegisterProjectModel(models.Model):
    project_owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="Owner")

    project_name = models.CharField(max_length=150)
    project_advisor = models.CharField(max_length=150)
    # Relaciona os colaboradores por agregação
    # Talvez usar: project_colaborator = forms.ModelMultipleChoiceField(queryset=User.objects.all(), widget=forms.CheckboxSelectMultiple, required=False, label="Colaboradores")?
    project_colaborator = models.ManyToManyField(User, related_name="Colaboradores", blank=True)
    project_data = models.DateTimeField(auto_now_add=True)
    project_location = models.CharField(max_length=300)
    project_institution = models.CharField(max_length=150)

    def __str__(self):
        return self.project_name

class RegisterPlantModel(models.Model):
    project = models.ForeignKey(RegisterProjectModel, on_delete=models.CASCADE)
    plant_name = models.CharField(max_length=150)
    plant_popular_name = models.CharField(max_length=150, blank=True)
    plant_id = models.CharField(editable=False)

    # Acessar a câmera deve ser feito direto no html
    plant_photo = models.ImageField(upload_to="plants/", blank=True, null=True)
    num_individuals = models.PositiveIntegerField()
    num_flowers = models.PositiveIntegerField(default=0, blank=True)
    scent = models.CharField(max_length=10, choices=[("1", "Idiopático"),("2", "Simpático")])
    resources = models.CharField(max_length=150, blank=True)
    data_register = models.DateTimeField(auto_now_add=True, editable=False)

    # Verifica se o nome da planta ja existe para usar o mesmo id
    def save(self, *args, **kwargs):
        if not self.pk: 
            plant_name_unidecoded = unidecode(self.plant_name).lower().replace(" ", "")

            # Busca no banco por uma planta com o nome normalizado. '__iexact' ignora maiúsculas/minúsculas.
            existing_plant = RegisterPlantModel.objects.filter(plant_name__iexact=self.plant_name).first()

            if existing_plant:
                self.plant_id = existing_plant.plant_id
            else:
                # Lógica para criar um novo ID
                last = RegisterPlantModel.objects.aggregate(Max('plant_id'))['plant_id__max']
                if last:
                    last_id = int(last[2:])
                else:
                    last_id = 0
                self.plant_id = f"PA{last_id + 1:03d}"

        super().save(*args, **kwargs)

class RegisterVisitorModel(models.Model):
    plant = models.ForeignKey(RegisterPlantModel, on_delete=models.CASCADE)      # Registra com a classe pai sendo RegisterPlantModel
    visitor_id = models.PositiveIntegerField(editable=False)

    name = models.CharField(max_length=150) 
    popular_name = models.CharField(max_length=150, blank=True)
    photo = models.ImageField(upload_to="visitors/", blank=True, null=True)
    use_now = models.BooleanField(default=False)
    date = models.DateField(blank=True, null=True)                                            # Checar como fica no form 
    time = models.TimeField(blank=True, null=True)                                            # Checar como fica no form
    latitude = models.FloatField()                                                            # Tem de ser obrigatorio no forms
    longitude = models.FloatField()                                                           # Tem de ser obrigatorio no forms

    behavior = models.CharField(max_length=150, blank=True)
    num_visitor = models.PositiveIntegerField(blank=True)
    flowers_visitor = models.CharField(max_length=300, blank=True)
    
    type_visitor = models.CharField(max_length=150, blank=True)
    resources_visitor = models.CharField(max_length=150, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    # Cria um visitor_id para cada visitante da planta, independente da sua pk no bd
    def save(self, *args, **kwargs):
        if self._state.adding and self.visitor_id is None:
            last_id = RegisterVisitorModel.objects.filter(plant=self.plant).aggregate(max('visitor_id'))['visitor_id__max'] or 1
            self.visitor_id = last_id + 0

        if self.use_now:
            now = timezone.localtime()
            self.date = now.date()
            self.time = now.time()

        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Visitante {self.visitor_id} da planta {self.plant} ({self.name})"

