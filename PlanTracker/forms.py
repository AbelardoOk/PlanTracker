from django import forms
from django.contrib.auth.models import User
from .models import RegisterProjectModel, RegisterPlantModel, RegisterVisitorModel

# Formulário para usar na views.py dentro do login.html
class LoginForm(forms.Form):
    username = forms.CharField(label="Usuário", max_length=150)
    password = forms.CharField(label="Senha", widget=forms.PasswordInput)

# Formulário para usar na views.py dentro do register.html
class RegisterForm(forms.Form):
    username = forms.CharField(label="Usuário", max_length=150)
    email = forms.CharField(label="Email")
    password = forms.CharField(label="Senha", widget=forms.PasswordInput)
    confirm_password = forms.CharField(label="Confirme a senha", widget=forms.PasswordInput)

    # Verifica se nome de usuário já existe
    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Esse nome de usuário já existe.")
        return username

    # Verifica se email é valido (somente se termina com @gmail.com)
    def clean_email(self):
        email = self.cleaned_data['email']
        if not email.endswith("@gmail.com"):
            raise forms.ValidationError("O email deve terminar com @gmail.com")
        return email
    
    # Faz confirmação de senha
    def clean(self):
        cleaned_data = super(RegisterForm, self).clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            self.add_error('confirm_password', "As senhas não coincidem")
        return cleaned_data

# Formulário para usar na views.py dentro do registerproject.html
class RegisterProjectForm(forms.ModelForm):
    class Meta:
        model = RegisterProjectModel
        fields = ["project_name", "project_advisor", "project_colaborator", "project_location", "project_institution"]

class FilterProjectForm(forms.Form):
    nome = forms.CharField(label="Nome do Projeto", required=False)
    instituicao = forms.CharField(label="Instituição", required=False)


class RegisterPlantForm(forms.ModelForm):
    class Meta:
        model = RegisterPlantModel
        fields = [
            'plant_name', 'plant_popular_name', 'plant_photo', 'num_individuals', 
            'num_flowers', 'scent', 'resources'
        ]
        widgets = {
            'plant_name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ex: Handroanthus impetiginosus'
            }),
            'plant_popular_name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ex: Ipê Roxo'
            }),
            'plant_photo': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',      # Garante que só imagens serão aceitas
                # 'capture': 'environment'  // Adicionar 'capture' no HTML é mais confiável
            }),
            'num_individuals': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '1'
            }),
            'num_flowers': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '0'
            }),
            'scent': forms.Select(attrs={
                'class': 'form-select'
            }),
            'resources': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ex: Néctar, Pólen'
            }),
        }


class RegisterVisitorForm(forms.ModelForm):
    list_type = [("abelha", "Abelha"), ("borboleta", "Borboleta"), ("besouro", "Besouro"), ("beija flor", "Beija flor"), ("mariposa", "Mariposa"), ("vespa", "Vespa"), ("mosca", "Mosca"), ("tripes", "Tripes"), ("percevejo", "Percevejo"), ("outros", "Outros")]
    list_resources = [("pólen", "Pólen"), ("néctar", "Néctar"), ("tecido", "Tecido"), ("óleo", "Óleo"), ("fragâncias", "Fragâncias"), ("resinas", "Resinas")]
    
    flowers_visitor = forms.MultipleChoiceField(choices=list_type, widget=forms.CheckboxSelectMultiple, required=False, label="Tipo de visitantes")
    resources_visitor = forms.MultipleChoiceField(choices=list_resources, widget=forms.CheckboxSelectMultiple, required=False, label="Tipo de recursos")
    use_now = forms.BooleanField(required=False, label="Agora (preenche data e hora)")

    def clean_flowers_visitor(self):
        return ','.join(self.cleaned_data['flowers_visitor'])
    def clean_resources_visitor(self):
        return ','.join(self.cleaned_data['resources_visitor'])

    class Meta:
        model = RegisterVisitorModel 
        fields = ["name", "popular_name", "photo", "use_now", "date", "time", "latitude", "longitude", "behavior", "num_visitor", "flowers_visitor", "type_visitor", "resources_visitor"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "time": forms.TimeInput(attrs={"type": "time"}),
        }

    # Grande chatgpt daqui pra baixo
    def clean(self):
        cleaned = super().clean()
        use_now = cleaned.get("use_now")
        date = cleaned.get("date")
        time = cleaned.get("time")
        if not use_now:
            if not date:
                self.add_error("date", "Data é obrigatória se não marcar 'Agora'.")
            if not time:
                self.add_error("time", "Hora é obrigatória se não marcar 'Agora'.")
        return cleaned

    def clean_type_visitor(self):
        return ",".join(self.cleaned_data.get("type_visitor", []))

    def clean_resources_visitor(self):
        return ",".join(self.cleaned_data.get("resources_visitor", []))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.type_visitor:
            self.initial["type_visitor"] = self.instance.type_visitor.split(",")
        if self.instance and self.instance.resources_visitor:
            self.initial["resources_visitor"] = self.instance.resources_visitor.split(",")
        if self.instance and self.instance.use_now:
            self.initial["use_now"] = True
