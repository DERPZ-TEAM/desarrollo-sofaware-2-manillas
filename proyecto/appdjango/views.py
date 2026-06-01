from django.shortcuts import render
from django.http import HttpResponse
from .models import Clientes

def mclientes(request):
    obj = Clientes.objects.all().values("nombre")
    revolver_var = "<h2>hola </h2>"
    for i in obj:
      revolver_var +=f"{i}"
    return HttpResponse(revolver_var)

