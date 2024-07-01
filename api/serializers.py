from rest_framework import serializers
from .models import Proveedor, Cliente, Producto, Transaccion, KiloProveedor, Configuracion, SensorData, ServoMotorState
from django.contrib.auth.models import User

# Serializador para el modelo de usuario de Django.
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password']  # Campos a serializar del modelo User.

# Serializador para el modelo Proveedor.
class ProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proveedor
        fields = ['id', 'user', 'puntos_acumulados']  # Campos a serializar del modelo Proveedor.

# Serializador para el modelo Cliente.
class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = ['id', 'nombre', 'apellidos', 'dni', 'ruc', 'ubicacion']  # Campos a serializar del modelo Cliente.

# Serializador para el modelo Producto.
class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = ['id', 'nombre', 'descripcion', 'precio', 'puntos_requeridos', 'tipo', 'imagen']  # Campos a serializar del modelo Producto.

# Serializador para el modelo Transaccion.
class TransaccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaccion
        fields = ['id', 'proveedor', 'cliente', 'producto', 'cantidad', 'total', 'puntos_utilizados', 'tipo', 'fecha']  # Campos a serializar del modelo Transaccion.

# Serializador para el modelo KiloProveedor.
class KiloProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = KiloProveedor
        fields = ['id', 'proveedor', 'kilos', 'descripcion', 'fecha']  # Campos a serializar del modelo KiloProveedor.

# Serializador para el modelo Configuracion.
class ConfiguracionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Configuracion
        fields = ['conversion_rate']  # Campo a serializar del modelo Configuracion.

# Serializador para el modelo SensorData.
class SensorSerializer(serializers.ModelSerializer):
    class Meta:
        model = SensorData
        fields = ['temperature', 'humidity']  # Campos a serializar del modelo SensorData.

# Serializador para el modelo ServoMotorState.
class ServoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServoMotorState
        fields = ['is_active']  # Campo a serializar del modelo ServoMotorState.
