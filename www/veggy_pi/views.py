from django.shortcuts import render
from django.contrib.auth import get_user_model

from rest_framework import viewsets, authentication, permissions


# from veggy_pi.models import RPiPin
# from veggy_pi.serializers import RPiPinSerializer, UserSerializer
# 
# 
# User = get_user_model()
# 
# class DefaultsMixin(object):
#     authentication_classes = (
#         authentication.BasicAuthentication,
#         authentication.TokenAuthentication,
#     )
#     permission_classe = (
#         permissions.IsAuthenticated,
#     )
#     paginate_by = 25
#     paginate_by_param = u'page_size'
#     max_paginate_by = 100
# 
# class RPiPinViewSet(DefaultsMixin, viewsets.ModelViewSet):
#     queryset = RPiPin.objects.order_by(u'pin')
#     serializer_class = RPiPinSerializer
# 
# class UserViewSet(DefaultsMixin, viewsets.ReadOnlyModelViewSet):
#     lookup_field = User.USERNAME_FIELD
#     lookup_url_kwarg = User.USERNAME_FIELD
#     queryset = User.objects.order_by(User.USERNAME_FIELD)
#     serializer_class = UserSerializer

# Create your views here.
