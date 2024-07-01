from django.db.models.functions import TruncMonth
from django.contrib.auth.models import User
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Proveedor, Cliente, Producto, Transaccion, KiloProveedor, Configuracion, ServoMotorState, SensorData
from .serializers import ConfiguracionSerializer, ProveedorSerializer, ClienteSerializer, ProductoSerializer, TransaccionSerializer, KiloProveedorSerializer, UserSerializer, ServoSerializer, SensorSerializer
from django.db.models import Sum

# Vista para obtener las transacciones de canje realizadas por un proveedor
@api_view(['GET'])
def canjes_por_proveedor(request):
    user = request.user  # Obtener el usuario autenticado
    try:
        proveedor = Proveedor.objects.get(user=user)  # Obtener el proveedor asociado al usuario
        transacciones = Transaccion.objects.filter(proveedor=proveedor)  # Obtener todas las transacciones del proveedor
        
        response_data = []  # Lista para almacenar los datos de respuesta
        for transaccion in transacciones:
            producto = transaccion.producto
            # Construir la URL absoluta de la imagen del producto, si existe
            imagen_url = request.build_absolute_uri(producto.imagen.url) if producto.imagen else None
            transaccion_data = {
                "id": transaccion.id,
                "proveedor": transaccion.proveedor.id,
                "producto": {
                    "id": producto.id,
                    "nombre": producto.nombre,
                    "descripcion": producto.descripcion,
                    "precio": str(producto.precio),  # Convertir el precio a cadena para evitar problemas de serialización
                    "puntos_requeridos": producto.puntos_requeridos,
                    "tipo": producto.tipo,
                    "imagen": imagen_url
                },
                "cantidad": transaccion.cantidad,
                "puntos_utilizados": transaccion.puntos_utilizados,
                "tipo": transaccion.tipo
            }
            response_data.append(transaccion_data)  # Agregar los datos de la transacción a la lista de respuesta
        
        return Response(response_data, status=status.HTTP_200_OK)  # Devolver la respuesta con los datos de las transacciones
    
    except Proveedor.DoesNotExist:
        return Response({'error': 'Proveedor no encontrado.'}, status=status.HTTP_404_NOT_FOUND)  # Devolver un error si el proveedor no existe

# Vista para obtener los kilos intercambiados por un proveedor, agrupados por mes
@api_view(['GET'])
def kilos_intercambiados(request):
    user = request.user  # Obtener el usuario autenticado
    try:
        proveedor = Proveedor.objects.get(user=user)  # Obtener el proveedor asociado al usuario
        kilos = KiloProveedor.objects.filter(proveedor=proveedor)  # Obtener todos los registros de kilos del proveedor
        # Agrupar los registros por mes y sumar los kilos por mes
        kilos_by_month = kilos.annotate(month=TruncMonth('fecha')).values('month').annotate(total_kilos=Sum('kilos')).order_by('month')
        
        response_data = []  # Lista para almacenar los datos de respuesta
        for entry in kilos_by_month:
            response_data.append({
                'month': entry['month'].strftime('%Y-%m'),  # Formatear la fecha del mes
                'total_kilos': entry['total_kilos']  # Total de kilos intercambiados en el mes
            })

        return Response(response_data, status=status.HTTP_200_OK)  # Devolver la respuesta con los datos de kilos por mes
    except Proveedor.DoesNotExist:
        return Response({'error': 'Proveedor no encontrado.'}, status=status.HTTP_404_NOT_FOUND)  # Devolver un error si el proveedor no existe

# Vista para registrar un nuevo usuario
@api_view(['POST'])
def register(request):
    username = request.data.get('username')  # Obtener el nombre de usuario del cuerpo de la solicitud
    password = request.data.get('password')  # Obtener la contraseña del cuerpo de la solicitud

    if username is None or password is None:
        return Response({'error': 'Por favor, proporciona nombre de usuario y contraseña'}, status=status.HTTP_400_BAD_REQUEST)  # Verificar que se proporcionen ambos datos

    if User.objects.filter(username=username).exists():
        return Response({'error': 'El nombre de usuario ya existe'}, status=status.HTTP_400_BAD_REQUEST)  # Verificar que el nombre de usuario no exista ya

    user = User.objects.create_user(username=username, password=password)  # Crear el nuevo usuario
    refresh = RefreshToken.for_user(user)  # Crear tokens JWT para el usuario
    return Response({
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }, status=status.HTTP_201_CREATED)  # Devolver los tokens de acceso y actualización

# Vista para actualizar un usuario existente
@api_view(['PUT'])
def update_user(request, pk):
    try:
        user = User.objects.get(pk=pk)  # Obtener el usuario por su ID
    except User.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)  # Devolver un error si el usuario no existe

    username = request.data.get('username')  # Obtener el nuevo nombre de usuario del cuerpo de la solicitud
    password = request.data.get('password')  # Obtener la nueva contraseña del cuerpo de la solicitud

    if username is not None:
        if User.objects.filter(username=username).exclude(id=user.id).exists():
            return Response({'error': 'El nombre de usuario ya existe'}, status=status.HTTP_400_BAD_REQUEST)  # Verificar que el nuevo nombre de usuario no exista ya
        user.username = username  # Actualizar el nombre de usuario

    if password is not None:
        user.set_password(password)  # Actualizar la contraseña

    user.save()  # Guardar los cambios

    refresh = RefreshToken.for_user(user)  # Crear nuevos tokens JWT para el usuario
    return Response({
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'user': {
            'id': user.id,
            'username': user.username,
        }
    }, status=status.HTTP_200_OK)  # Devolver los tokens de acceso y actualización y los datos del usuario

# Vista para autenticar un usuario
@api_view(['POST'])
def login(request):
    username = request.data.get('username')  # Obtener el nombre de usuario del cuerpo de la solicitud
    password = request.data.get('password')  # Obtener la contraseña del cuerpo de la solicitud

    if username is None or password is None:
        return Response({'error': 'Por favor, proporciona nombre de usuario y contraseña'}, status=status.HTTP_400_BAD_REQUEST)  # Verificar que se proporcionen ambos datos

    user = User.objects.filter(username=username).first()  # Buscar el usuario por nombre de usuario

    if user is None or not user.check_password(password):
        return Response({'error': 'Credenciales inválidas'}, status=status.HTTP_401_UNAUTHORIZED)  # Verificar las credenciales

    refresh = RefreshToken.for_user(user)  # Crear tokens JWT para el usuario
    return Response({
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }, status=status.HTTP_200_OK)  # Devolver los tokens de acceso y actualización

# Vista para autenticar un usuario con restricciones adicionales para proveedores
@api_view(['POST'])
def login_user(request):
    username = request.data.get('username')  # Obtener el nombre de usuario del cuerpo de la solicitud
    password = request.data.get('password')  # Obtener la contraseña del cuerpo de la solicitud

    if username is None or password is None:
        return Response({'error': 'Por favor, proporciona nombre de usuario y contraseña'}, status=status.HTTP_400_BAD_REQUEST)  # Verificar que se proporcionen ambos datos

    user = User.objects.filter(username=username).first()  # Buscar el usuario por nombre de usuario

    if user is None or not user.check_password(password):
        return Response({'error': 'Credenciales inválidas'}, status=status.HTTP_401_UNAUTHORIZED)  # Verificar las credenciales

    if Proveedor.objects.filter(user=user).exists():
        return Response({'error': 'El usuario es un proveedor y no puede iniciar sesión aquí'}, status=status.HTTP_403_FORBIDDEN)  # Restricción adicional para proveedores

    refresh = RefreshToken.for_user(user)  # Crear tokens JWT para el usuario
    return Response({
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }, status=status.HTTP_200_OK)  # Devolver los tokens de acceso y actualización

# Vista basada en clase para listar y crear usuarios
class UserList(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

# Vista basada en clase para obtener, actualizar o eliminar un usuario específico
class UserDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

# Vista basada en clase para listar y crear proveedores
class ProveedorList(generics.ListCreateAPIView):
    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer

# Vista basada en clase para obtener, actualizar o eliminar un proveedor específico
class ProveedorDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer

# Vista basada en clase para listar y crear clientes
class ClienteList(generics.ListCreateAPIView):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer

# Vista basada en clase para obtener, actualizar o eliminar un cliente específico
class ClienteDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer

# Vista basada en clase para listar y crear productos
class ProductoList(generics.ListCreateAPIView):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer

# Vista basada en clase para obtener, actualizar o eliminar un producto específico
class ProductoDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer

# Vista para canjear puntos por productos
@api_view(['POST'])
def canjear_puntos(request):
    proveedor_id = request.data.get('proveedor_id')  # Obtener el ID del proveedor del cuerpo de la solicitud
    producto_id = request.data.get('producto_id')  # Obtener el ID del producto del cuerpo de la solicitud
    cantidad = request.data.get('cantidad', 1)  # Obtener la cantidad deseada (por defecto 1)

    try:
        proveedor = Proveedor.objects.get(id=proveedor_id)  # Obtener el proveedor por su ID
        producto = Producto.objects.get(id=producto_id)  # Obtener el producto por su ID

        if producto.tipo != 'C':  # Verificar que el producto esté disponible para canje
            return Response({'error': 'El producto no está disponible para canje.'}, status=status.HTTP_400_BAD_REQUEST)

        puntos_requeridos = producto.puntos_requeridos * cantidad  # Calcular los puntos requeridos para el canje
        if proveedor.puntos_acumulados < puntos_requeridos:  # Verificar que el proveedor tenga suficientes puntos
            return Response({'error': 'No tienes suficientes puntos para este canje.'}, status=status.HTTP_400_BAD_REQUEST)

        proveedor.puntos_acumulados -= puntos_requeridos  # Restar los puntos utilizados del proveedor
        proveedor.save()

        # Crear una nueva transacción de canje
        transaccion = Transaccion.objects.create(
            proveedor=proveedor,
            producto=producto,
            cantidad=cantidad,
            puntos_utilizados=puntos_requeridos,
            tipo='C'
        )

        return Response(TransaccionSerializer(transaccion).data, status=status.HTTP_201_CREATED)  # Devolver los datos de la transacción creada

    except Proveedor.DoesNotExist:
        return Response({'error': 'Proveedor no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
    except Producto.DoesNotExist:
        return Response({'error': 'Producto no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

# Vista para consultar los puntos acumulados por un proveedor
@api_view(['GET'])
def consultar_puntos(request, proveedor_id):
    try:
        proveedor = Proveedor.objects.get(id=proveedor_id)  # Obtener el proveedor por su ID
        return Response({'puntos_acumulados': proveedor.puntos_acumulados}, status=status.HTTP_200_OK)  # Devolver los puntos acumulados del proveedor
    except Proveedor.DoesNotExist:
        return Response({'error': 'Proveedor no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

# Vista para registrar un nuevo proveedor
@api_view(['POST'])
def register_proveedor(request):
    username = request.data.get('username')  # Obtener el nombre de usuario del cuerpo de la solicitud
    password = request.data.get('password')  # Obtener la contraseña del cuerpo de la solicitud
    
    if not username or not password:
        return Response({'error': 'Username and password are required.'}, status=status.HTTP_400_BAD_REQUEST)  # Verificar que se proporcionen ambos datos

    try:
        user = User.objects.create_user(username=username, password=password)  # Crear el nuevo usuario
        Proveedor.objects.create(user=user, puntos_acumulados=0)  # Crear el nuevo proveedor asociado al usuario
        return Response({'message': 'User registered successfully.'}, status=status.HTTP_201_CREATED)  # Devolver mensaje de éxito
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)  # Devolver error en caso de fallo

# Vista para obtener el perfil de un proveedor
@api_view(['GET'])
def proveedor_profile(request):
    user = request.user  # Obtener el usuario autenticado
    try:
        proveedor = Proveedor.objects.get(user=user)  # Obtener el proveedor asociado al usuario
        productos = Producto.objects.filter(tipo='C')  # Obtener todos los productos disponibles para canje
        return Response({
            'user_name': user.username,
            'proveedor': ProveedorSerializer(proveedor).data,
            'productos': ProductoSerializer(productos, many=True).data
        }, status=status.HTTP_200_OK)  # Devolver los datos del proveedor y productos
    except Proveedor.DoesNotExist:
        return Response({'error': 'Proveedor no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

# Vista basada en clase para listar y crear transacciones
class TransaccionesList(generics.ListCreateAPIView):
    queryset = Transaccion.objects.all()
    serializer_class = TransaccionSerializer

# Vista basada en clase para obtener, actualizar o eliminar una transacción específica
class TransaccionDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Transaccion.objects.all()
    serializer_class = TransaccionSerializer

# Vista para listar y crear registros de kilos de proveedores
@api_view(['GET', 'POST'])
def kilos_list_create(request):
    configuracion = Configuracion.objects.first()  # Obtener la configuración (o crearla si no existe)
    if not configuracion:
        configuracion = Configuracion.objects.create()

    conversion_rate = configuracion.conversion_rate  # Obtener la tasa de conversión de la configuración

    if request.method == 'GET':
        kilos = KiloProveedor.objects.all()  # Obtener todos los registros de kilos
        serializer = KiloProveedorSerializer(kilos, many=True)
        return Response(serializer.data)  # Devolver los datos de los registros de kilos

    elif request.method == 'POST':
        serializer = KiloProveedorSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            proveedor = Proveedor.objects.get(id=request.data['proveedor'])  # Obtener el proveedor por su ID
            proveedor.puntos_acumulados += int(request.data['kilos']) * conversion_rate  # Actualizar los puntos acumulados del proveedor
            proveedor.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)  # Devolver los datos del registro de kilos creado
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Vista basada en clase para obtener, actualizar o eliminar un registro de kilos de proveedor específico
class KiloDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = KiloProveedor.objects.all()
    serializer_class = KiloProveedorSerializer

# Vista para obtener y actualizar la configuración
@api_view(['GET', 'PUT'])
def configuracion_detail(request):
    configuracion = Configuracion.objects.first()  # Obtener la configuración (o crearla si no existe)
    if not configuracion:
        configuracion = Configuracion.objects.create()

    if request.method == 'GET':
        serializer = ConfiguracionSerializer(configuracion)
        return Response(serializer.data)  # Devolver los datos de la configuración

    elif request.method == 'PUT':
        serializer = ConfiguracionSerializer(configuracion, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)  # Devolver los datos de la configuración actualizada
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Vista para obtener y actualizar el estado del servomotor
@api_view(['GET', 'PUT'])
def servo_motor_state_detail(request):
    servo_motor_state = ServoMotorState.objects.first()  # Obtener el estado del servomotor (o crearlo si no existe)
    if not servo_motor_state:
        servo_motor_state = ServoMotorState.objects.create()

    if request.method == 'GET':
        serializer = ServoSerializer(servo_motor_state)
        return Response(serializer.data)  # Devolver los datos del estado del servomotor

    elif request.method == 'PUT':
        serializer = ServoSerializer(servo_motor_state, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)  # Devolver los datos del estado del servomotor actualizado
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
# Vista para obtener y actualizar los datos del sensor
@api_view(['GET', 'PUT'])
def sensor_data_detail(request):
    sensor_data = SensorData.objects.first()  # Obtener los datos del sensor (o crearlos si no existen)
    if not sensor_data:
        sensor_data = SensorData.objects.create()

    if request.method == 'GET':
        serializer = SensorSerializer(sensor_data)
        return Response(serializer.data)  # Devolver los datos del sensor

    elif request.method == 'PUT':
        serializer = SensorSerializer(sensor_data, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)  # Devolver los datos del sensor actualizados
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)