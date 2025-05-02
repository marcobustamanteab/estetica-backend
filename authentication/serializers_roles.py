from rest_framework import serializers
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

class ContentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentType
        fields = ['id', 'app_label', 'model']

class PermissionSerializer(serializers.ModelSerializer):
    content_type = ContentTypeSerializer()
    
    class Meta:
        model = Permission
        fields = ['id', 'name', 'codename', 'content_type']

class GroupSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)
    
    # Eliminamos user_set por ahora, ya que causa problemas con prefetch_related
    # Si necesitas esta información, puedes volver a añadirla más tarde con un enfoque diferente
    
    class Meta:
        model = Group
        fields = ['id', 'name', 'permissions']