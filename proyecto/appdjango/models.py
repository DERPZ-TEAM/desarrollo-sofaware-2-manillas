from django.db import models

class Clientes (models.Model):
    nombre = models.CharField(max_length=50)
    fecha = models.DateTimeField()
    nombreEmpleado = models.ForeignKey('Empleados', on_delete=models.SET_NULL, null=True) # type: ignore

    def __str__ (self):
        return f" Clinete: {self.nombre}- Vendedor: {self.nombreEmpleado.nombre}"


class Empleados (models.Model):
    nombre = models.CharField(max_length=50)
    fecha = models.DateTimeField()

    def __str__ (self):
        return self.nombre