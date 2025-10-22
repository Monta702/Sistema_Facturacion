from django.db import models
from decimal import Decimal
from datetime import timedelta
import random

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
    





class Invoice(models.Model):
    TYPE_CHOICES = [
        ('A', 'Factura A'),
        ('B', 'Factura B'),
        ('C', 'Factura C'),
    ]
    
    STATUS_CHOICES = [
        ('DRAFT', 'Borrador'),
        ('ISSUED', 'Emitida'),
        ('PAID', 'Pagada'),
        ('CANCELLED', 'Anulada'),
    ]
    
    # Numeración
    invoice_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    point_of_sale = models.CharField(max_length=5, default='0001')
    
    # Tipo y estado
    invoice_type = models.CharField(max_length=1, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    # Cliente
    client = models.ForeignKey('billing.Client', on_delete=models.PROTECT, related_name='invoices')
    
    # Fechas
    issue_date = models.DateField(verbose_name="Fecha de emisión")
    due_date = models.DateField(null=True, blank=True, verbose_name="Fecha de vencimiento")
    
    # Totales (se calculan automáticamente)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    iva_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Simulación AFIP
    cae = models.CharField(max_length=20, blank=True)
    cae_expiration = models.DateField(null=True, blank=True)
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=100, blank=True)  # Usuario que creó
    
    notes = models.TextField(blank=True, verbose_name="Observaciones")
    
    class Meta:
        db_table = 'invoices'
        ordering = ['-issue_date', '-invoice_number']
        verbose_name = 'Factura'
        verbose_name_plural = 'Facturas'
    
    def __str__(self):
        return f"Factura {self.invoice_type} {self.invoice_number or 'BORRADOR'}"
    
    def generate_invoice_number(self):
        """Genera el número de factura correlativo"""
        if self.invoice_number:
            return
        
        last_invoice = Invoice.objects.filter(
            invoice_type=self.invoice_type,
            point_of_sale=self.point_of_sale,
            invoice_number__isnull=False
        ).order_by('-invoice_number').first()
        
        if last_invoice:
            last_number = int(last_invoice.invoice_number.split('-')[1])
            new_number = last_number + 1
        else:
            new_number = 1
        
        self.invoice_number = f"{self.point_of_sale}-{new_number:08d}"
    #GENERADOR DE CAE SIMULADO, REEMPLAZA LA API DE LA AFIP
    def generate_cae(self):
        
        if not self.cae:
            self.cae = ''.join([str(random.randint(0, 9)) for _ in range(14)])
            self.cae_expiration = self.issue_date + timedelta(days=10)
    
    def calculate_totals(self):
        """Calcula los totales de la factura"""
        items = self.items.all()
        self.subtotal = sum(item.subtotal for item in items)
        self.iva_amount = sum(item.iva_amount for item in items)
        self.total = sum(item.total for item in items)
    
    def issue(self):
        """Emite la factura (cambia estado y genera número/CAE)"""
        if self.status != 'DRAFT':
            raise ValueError("Solo se pueden emitir facturas en borrador")
        
        self.generate_invoice_number()
        self.generate_cae()
        self.status = 'ISSUED'
        self.save()


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('billing.Product', on_delete=models.PROTECT)
    
    # Copiamos datos del producto para inmutabilidad
    description = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    iva_rate = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Calculados
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    iva_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    class Meta:
        db_table = 'invoice_items'
        verbose_name = 'Item de Factura'
        verbose_name_plural = 'Items de Factura'
    
    def __str__(self):
        return f"{self.description} x{self.quantity}"
    
    def calculate_amounts(self):
        """Calcula los montos del item"""
        self.subtotal = self.quantity * self.unit_price
        self.iva_amount = self.subtotal * (self.iva_rate / Decimal('100'))
        self.total = self.subtotal + self.iva_amount
    
    def save(self, *args, **kwargs):
        # Calcular montos antes de guardar
        self.calculate_amounts()
        super().save(*args, **kwargs)
        
        # Actualizar totales de la factura
        if self.invoice_id:
            self.invoice.calculate_totals()
            self.invoice.save()