from django.db import models
from django.contrib.auth.models import User

# Modelo para los proveedores, relacionado uno a uno con el modelo de usuario de Django.
class Proveedor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    puntos_acumulados = models.PositiveIntegerField(default=0)  # Puntos acumulados por el proveedor.

    def __str__(self):
        return self.user.username  # Representación en cadena del proveedor.

# Modelo para los clientes.
class Cliente(models.Model):
    nombre = models.CharField(max_length=255)  # Nombre del cliente.
    apellidos = models.CharField(max_length=255)  # Apellidos del cliente.
    dni = models.CharField(max_length=8, unique=True)  # DNI del cliente, debe ser único.
    ruc = models.CharField(max_length=11, blank=True, null=True)  # RUC del cliente, opcional.
    ubicacion = models.CharField(max_length=255)  # Ubicación del cliente.

    def __str__(self):
        return f'{self.nombre} {self.apellidos}'  # Representación en cadena del cliente.

# Modelo para los productos.
class Producto(models.Model):
    TIPO_PRODUCTO_CHOICES = [
        ('V', 'Venta'),  # Producto de venta.
        ('C', 'Canje'),  # Producto de canje.
    ]
    nombre = models.CharField(max_length=255)  # Nombre del producto.
    descripcion = models.TextField()  # Descripción del producto.
    precio = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Precio del producto, opcional.
    puntos_requeridos = models.PositiveIntegerField(null=True, blank=True)  # Puntos requeridos para canje, opcional.
    tipo = models.CharField(max_length=1, choices=TIPO_PRODUCTO_CHOICES)  # Tipo de producto (Venta o Canje).
    imagen = models.ImageField(upload_to='productos/', null=True, blank=True, default='productos/default.jpg')  # Imagen del producto, opcional.

    def __str__(self):
        return self.nombre  # Representación en cadena del producto.

# Modelo para las transacciones.
class Transaccion(models.Model):
    TIPO_TRANSACCION_CHOICES = [
        ('V', 'Venta'),  # Transacción de venta.
        ('C', 'Canje'),  # Transacción de canje.
    ]
    proveedor = models.ForeignKey(Proveedor, null=True, blank=True, on_delete=models.CASCADE)  # Proveedor involucrado, opcional.
    cliente = models.ForeignKey(Cliente, null=True, blank=True, on_delete=models.CASCADE)  # Cliente involucrado, opcional.
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)  # Producto involucrado.
    cantidad = models.PositiveIntegerField()  # Cantidad de producto.
    total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Total de la transacción, opcional.
    puntos_utilizados = models.PositiveIntegerField(null=True, blank=True)  # Puntos utilizados en la transacción, opcional.
    tipo = models.CharField(max_length=1, choices=TIPO_TRANSACCION_CHOICES)  # Tipo de transacción (Venta o Canje).
    fecha = models.DateTimeField(auto_now_add=True)  # Fecha de la transacción.

    def __str__(self):
        return f'{self.tipo} - {self.producto.nombre} - {self.fecha}'  # Representación en cadena de la transacción.

# Modelo para registrar los kilos aportados por los proveedores.
class KiloProveedor(models.Model):
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE)  # Proveedor que aportó los kilos.
    kilos = models.DecimalField(max_digits=10, decimal_places=2)  # Cantidad de kilos aportados.
    fecha = models.DateTimeField(auto_now_add=True)  # Fecha de registro.
    descripcion = models.CharField(max_length=2000, default="")  # Descripción del aporte.

    def __str__(self):
        return f'{self.proveedor.user.username} - {self.kilos} kg - {self.fecha}'  # Representación en cadena del registro.

# Modelo para la configuración del sistema.
class Configuracion(models.Model):
    conversion_rate = models.PositiveIntegerField(default=100)  # Tasa de conversión, por ejemplo, puntos por unidad monetaria.

# Modelo para los datos de sensores.
class SensorData(models.Model):
    temperature = models.FloatField(default=0.0)  # Temperatura registrada por el sensor.
    humidity = models.FloatField(default=0.0)  # Humedad registrada por el sensor.
    timestamp = models.DateTimeField(auto_now_add=True)  # Fecha y hora del registro.

# Modelo para el estado del servo motor.
class ServoMotorState(models.Model):
    is_active = models.BooleanField(default=False)  # Estado del servo motor (activo o inactivo).
    timestamp = models.DateTimeField(auto_now_add=True)  # Fecha y hora del registro.
