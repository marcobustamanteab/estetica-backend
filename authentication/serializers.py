from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer # type: ignore

User = get_user_model()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Agregar información personalizada al token
        token['username'] = user.username
        token['email'] = user.email
        token['is_staff'] = user.is_staff
        return token

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer para mostrar información del usuario
    """
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'profile_image')
        read_only_fields = ('id',)

class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer para registrar nuevos usuarios
    """
    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        # Eliminamos phone_number
        fields = ('username', 'email', 'password', 'password2', 'first_name', 'last_name')
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Las contraseñas no coinciden"})
        return attrs
    
    def create(self, validated_data):
        # Eliminar password2 ya que no es parte del modelo User
        validated_data.pop('password2')
        
        # Crear usuario
        user = User.objects.create_user(**validated_data)
        return user
    
class AdminUserSerializer(serializers.ModelSerializer):
    """
    Serializer para administradores que permite gestionar todos los campos de usuarios
    """
    password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 
                  'is_active', 'is_staff', 'profile_image', 'password')
        read_only_fields = ('id',)
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        
        if password:
            user.set_password(password)
            user.save()
        
        return user
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        
        # Actualizar campos normales
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Manejar la contraseña especialmente
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance