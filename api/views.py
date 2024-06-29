from django.shortcuts import render
from django.db.models.functions import TruncMonth
from django.contrib.auth.models import User
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Proveedor, Cliente, Producto, Transaccion, KiloProveedor,Configuracion,ServoMotorState,SensorData
from .serializers import ConfiguracionSerializer,ProveedorSerializer, ClienteSerializer, ProductoSerializer, TransaccionSerializer, KiloProveedorSerializer, UserSerializer, ServoSerializer,SensorSerializer
from django.db.models import Sum
@api_view(['GET'])
def canjes_por_proveedor(request):
    user = request.user
    try:
        proveedor = Proveedor.objects.get(user=user)
        transacciones = Transaccion.objects.filter(proveedor=proveedor)
        
        response_data = []
        for transaccion in transacciones:
            producto = transaccion.producto
            imagen_url = request.build_absolute_uri(producto.imagen.url) if producto.imagen else None
            transaccion_data = {
                "id": transaccion.id,
                "proveedor": transaccion.proveedor.id,
                "producto": {
                    "id": producto.id,
                    "nombre": producto.nombre,
                    "descripcion": producto.descripcion,
                    "precio": str(producto.precio),
                    "puntos_requeridos": producto.puntos_requeridos,
                    "tipo": producto.tipo,
                    "imagen": imagen_url
                },
                "cantidad": transaccion.cantidad,
                "puntos_utilizados": transaccion.puntos_utilizados,
                "tipo": transaccion.tipo
            }
            response_data.append(transaccion_data)
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    except Proveedor.DoesNotExist:
        return Response({'error': 'Proveedor no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def kilos_intercambiados(request):
    user = request.user
    try:
        proveedor = Proveedor.objects.get(user=user)
        kilos = KiloProveedor.objects.filter(proveedor=proveedor)
        kilos_by_month = kilos.annotate(month=TruncMonth('fecha')).values('month').annotate(total_kilos=Sum('kilos')).order_by('month')
        
        response_data = []
        for entry in kilos_by_month:
            response_data.append({
                'month': entry['month'].strftime('%Y-%m'),
                'total_kilos': entry['total_kilos']
            })

        return Response(response_data, status=status.HTTP_200_OK)
    except Proveedor.DoesNotExist:
        return Response({'error': 'Proveedor no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def register(request):
    username = request.data.get('username')
    password = request.data.get('password')

    if username is None or password is None:
        return Response({'error': 'Please provide both username and password'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(username=username, password=password)
    refresh = RefreshToken.for_user(user)
    return Response({
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }, status=status.HTTP_201_CREATED)

@api_view(['PUT'])
def update_user(request, pk):
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    username = request.data.get('username')
    password = request.data.get('password')

    if username is not None:
        if User.objects.filter(username=username).exclude(id=user.id).exists():
            return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)
        user.username = username

    if password is not None:
        user.set_password(password)

    user.save()

    refresh = RefreshToken.for_user(user)
    return Response({
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'user': {
            'id': user.id,
            'username': user.username,
        }
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
def login(request):
    username = request.data.get('username')
    password = request.data.get('password')

    if username is None or password is None:
        return Response({'error': 'Please provide both username and password'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.filter(username=username).first()

    if user is None or not user.check_password(password):
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

    refresh = RefreshToken.for_user(user)
    return Response({
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
def login_user(request):
    username = request.data.get('username')
    password = request.data.get('password')

    if username is None or password is None:
        return Response({'error': 'Please provide both username and password'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.filter(username=username).first()

    if user is None or not user.check_password(password):
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

    if Proveedor.objects.filter(user=user).exists():
        return Response({'error': 'User is a provider and cannot log in here'}, status=status.HTTP_403_FORBIDDEN)

    refresh = RefreshToken.for_user(user)
    return Response({
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }, status=status.HTTP_200_OK)
    
class UserList(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
class UserDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class ProveedorList(generics.ListCreateAPIView):
    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer

class ProveedorDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer

class ClienteList(generics.ListCreateAPIView):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer

class ClienteDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer

class ProductoList(generics.ListCreateAPIView):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer

class ProductoDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer

@api_view(['POST'])
def canjear_puntos(request):
    proveedor_id = request.data.get('proveedor_id')
    producto_id = request.data.get('producto_id')
    cantidad = request.data.get('cantidad', 1)

    try:
        proveedor = Proveedor.objects.get(id=proveedor_id)
        producto = Producto.objects.get(id=producto_id)

        if producto.tipo != 'C':
            return Response({'error': 'El producto no está disponible para canje.'}, status=status.HTTP_400_BAD_REQUEST)

        puntos_requeridos = producto.puntos_requeridos * cantidad
        if proveedor.puntos_acumulados < puntos_requeridos:
            return Response({'error': 'No tienes suficientes puntos para este canje.'}, status=status.HTTP_400_BAD_REQUEST)

        proveedor.puntos_acumulados -= puntos_requeridos
        proveedor.save()

        transaccion = Transaccion.objects.create(
            proveedor=proveedor,
            producto=producto,
            cantidad=cantidad,
            puntos_utilizados=puntos_requeridos,
            tipo='C'
        )

        return Response(TransaccionSerializer(transaccion).data, status=status.HTTP_201_CREATED)

    except Proveedor.DoesNotExist:
        return Response({'error': 'Proveedor no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
    except Producto.DoesNotExist:
        return Response({'error': 'Producto no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def consultar_puntos(request, proveedor_id):
    try:
        proveedor = Proveedor.objects.get(id=proveedor_id)
        return Response({'puntos_acumulados': proveedor.puntos_acumulados}, status=status.HTTP_200_OK)
    except Proveedor.DoesNotExist:
        return Response({'error': 'Proveedor no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def register_proveedor(request):
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({'error': 'Username and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.create_user(username=username, password=password)
        Proveedor.objects.create(user=user, puntos_acumulados=0)
        return Response({'message': 'User registered successfully.'}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def proveedor_profile(request):
    user = request.user
    try:
        proveedor = Proveedor.objects.get(user=user)
        productos = Producto.objects.filter(tipo='C')
        return Response({
            'user_name': user.username,
            'proveedor': ProveedorSerializer(proveedor).data,
            'productos': ProductoSerializer(productos, many=True).data
        }, status=status.HTTP_200_OK)
    except Proveedor.DoesNotExist:
        return Response({'error': 'Proveedor no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

class TransaccionesList(generics.ListCreateAPIView):
    queryset = Transaccion.objects.all()
    serializer_class = TransaccionSerializer

class TransaccionDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Transaccion.objects.all()
    serializer_class = TransaccionSerializer

@api_view(['GET', 'POST'])
def kilos_list_create(request):
    configuracion = Configuracion.objects.first()
    if not configuracion:
        configuracion = Configuracion.objects.create()

    conversion_rate = configuracion.conversion_rate

    if request.method == 'GET':
        kilos = KiloProveedor.objects.all()
        serializer = KiloProveedorSerializer(kilos, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = KiloProveedorSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            proveedor = Proveedor.objects.get(id=request.data['proveedor'])
            proveedor.puntos_acumulados += int(request.data['kilos']) * conversion_rate
            proveedor.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class KiloDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = KiloProveedor.objects.all()
    serializer_class = KiloProveedorSerializer

@api_view(['GET', 'PUT'])
def configuracion_detail(request):
    configuracion = Configuracion.objects.first()
    if not configuracion:
        configuracion = Configuracion.objects.create()

    if request.method == 'GET':
        serializer = ConfiguracionSerializer(configuracion)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = ConfiguracionSerializer(configuracion, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
@api_view(['GET', 'PUT'])
def servo_motor_state_detail(request):
    servo_motor_state = ServoMotorState.objects.first()
    if not servo_motor_state:
        servo_motor_state = ServoMotorState.objects.create()

    if request.method == 'GET':
        serializer = ServoSerializer(servo_motor_state)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = ServoSerializer(servo_motor_state, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['GET', 'PUT'])
def sensor_data_detail(request):
    sensor_data = SensorData.objects.first()
    if not sensor_data:
        sensor_data = SensorData.objects.create()

    if request.method == 'GET':
        serializer = SensorSerializer(sensor_data)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = SensorSerializer(sensor_data, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)