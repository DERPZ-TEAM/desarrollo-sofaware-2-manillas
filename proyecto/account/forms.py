from django import forms
from .models import Producto, Categoria


class ProductoForm(forms.ModelForm):

    class Meta:
        model = Producto
        fields = ['nombre', 'descripcion', 'precio', 'categoria', 'imagen', 'activo']
        labels = {
            'nombre': 'Nombre',
            'descripcion': 'Descripción',
            'precio': 'Precio',
            'categoria': 'Categoría',
            'imagen': 'Imagen',
            'activo': 'Visible en la tienda',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del producto'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción'
            }),
            'precio': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Precio'
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-select'
            }),
            'imagen': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        error_messages = {
            'nombre': {'required': 'Escribe el nombre del producto.'},
            'descripcion': {'required': 'Escribe una descripción.'},
            'precio': {
                'required': 'Escribe el precio.',
                'invalid': 'El precio debe ser un número.',
            },
            'imagen': {
                'required': 'Sube una imagen del producto.',
                'invalid_image': 'El archivo no es una imagen válida.',
            },
        }

    def clean_precio(self):
        precio = self.cleaned_data['precio']
        if precio < 0:
            raise forms.ValidationError('El precio no puede ser negativo.')
        return precio


class CategoriaForm(forms.ModelForm):

    class Meta:
        model = Categoria
        fields = ['nombre']
        labels = {'nombre': 'Nombre de la categoría'}
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. Manillas'
            }),
        }
        error_messages = {
            'nombre': {
                'required': 'Escribe el nombre de la categoría.',
                'unique': 'Ya existe una categoría con ese nombre.',
            },
        }

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        existe = Categoria.objects.filter(nombre__iexact=nombre)
        if self.instance.pk:
            existe = existe.exclude(pk=self.instance.pk)
        if existe.exists():
            raise forms.ValidationError('Ya existe una categoría con ese nombre.')
        return nombre
