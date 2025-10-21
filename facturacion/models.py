from django.db import models
from decimal import Decimal

class Client(models.Model):
    TYPE_CHOICES = [
        ('MONOTRIBUTO', 'Monotributo'),
        ('RESPONSABLE_INSCRIPTO', 'Responsable Inscripto'),
        ('CONSUMIDOR_FINAL', 'Consumidor Final'),
        ('EXENTO', 'Exento'),
    ]
    
    name = models.CharField(max_length=200, verbose_name="Nombre")
    tax_id = models.CharField(max_length=20, unique=True, verbose_name="CUIT/DNI")
    client_type = models.CharField(max_length=30, choices=TYPE_CHOICES, verbose_name="Tipo")
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    address = models.TextField(verbose_name="Dirección")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    
    class Meta:
        db_table = 'clients'
        ordering = ['-created_at']
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
    
    def __str__(self):
        return f"{self.name} ({self.tax_id})"
    


class Product(models.Model):
    IVA_CHOICES = [
        (Decimal('21.00'), 'IVA 21%'),
        (Decimal('10.50'), 'IVA 10.5%'),
        (Decimal('0.00'), 'Exento'),
    ]
    
    code = models.CharField(max_length=50, unique=True, verbose_name="Código")
    name = models.CharField(max_length=200, verbose_name="Nombre")
    description = models.TextField(blank=True, verbose_name="Descripción")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio")
    iva_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        choices=IVA_CHOICES,
        default=Decimal('21.00'),
        verbose_name="Alícuota IVA"
    )
    stock = models.IntegerField(default=0, verbose_name="Stock")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'products'
        ordering = ['name']
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def price_with_iva(self):
        """Retorna el precio con IVA incluido"""
        return self.price * (1 + self.iva_rate / Decimal('100'))