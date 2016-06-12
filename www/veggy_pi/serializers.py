from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers
from rest_framework.reverse import reverse

import datetime


from veggy_pi.models import *


User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source=u'get_full_name', read_only=True)
    links = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (u'pk', User.USERNAME_FIELD, u'full_name', u'is_active', u'links',)
    
    def get_links(self, obj):
        request = self.context[u'request']
        username = obj.get_username()
        return {
            u'self': reverse(u'user-detail', kwargs={User.USERNAME_FIELD: username}, request=request),
        }
    

class RPiPinSerializer(serializers.ModelSerializer):
    class Meta:
        model = RPiPin
        fields = (u'pin', u'label')
    
    def get_links(self, obj):
        request = self.context[u'request']
        return {
            u'self': reverse(u'rpipin-detail', kwargs={u'pk': obj.pk}, request=request)
        }
