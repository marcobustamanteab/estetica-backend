# authentication/serializers_roles.py
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
    user_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Group
        fields = ['id', 'name', 'permissions', 'user_count']
        
    def get_user_count(self, obj):
        # This safely gets the count of users for this group
        return obj.user_set.count() if hasattr(obj, 'user_set') else 0