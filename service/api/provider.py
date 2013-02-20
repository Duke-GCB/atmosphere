"""
atmosphere service provider rest api.

"""

from rest_framework.reverse import reverse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from atmosphere.logger import logger

from auth.decorators import api_auth_token_required


from core.models.euca_key import Euca_Key
from core.models.group import Group
from core.models.provider import Provider as CoreProvider

from service.api.serializers import ProviderSerializer

class ProviderList(APIView):
    """
    List of active providers
    """
    @api_auth_token_required
    def get(self, request):
        """
        List all providers accessible by request user
        """
        username = request.user.username
        group = Group.objects.get(name=username)
        providers = group.providers.filter(active=True, end_date=None).order_by('id')
        #providers = CoreProvider.objects.order_by('id')
        serialized_data = ProviderSerializer(providers).data
        return Response(serialized_data)

class Provider(APIView):
    """
    Show single provider
    """
    @api_auth_token_required
    def get(self, request, provider_id):
        """
        return provider if accessible by request user
        """
        username = request.user.username
        group = Group.objects.get(name=username)
        provider = group.providers.get(id=provider_id, active=True, end_date=None)

        serialized_data = ProviderSerializer(provider).data
        return Response(serialized_data)