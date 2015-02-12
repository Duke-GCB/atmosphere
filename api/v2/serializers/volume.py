from core.models import Volume
from rest_framework import serializers
from .provider import ProviderSummarySerializer


class VolumeSerializer(serializers.HyperlinkedModelSerializer):
    provider = ProviderSummarySerializer()

    class Meta:
        model = Volume
        view_name = 'api_v2:volume-detail'
        fields = ('id', 'url', 'size', 'name', 'start_date', 'provider')


class VolumeSummarySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Volume
        view_name = 'api_v2:volume-detail'
        fields = ('id', 'url', 'size', 'name', 'start_date', 'provider')
