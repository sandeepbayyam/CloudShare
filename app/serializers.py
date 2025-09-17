from rest_framework import serializers
from .models import Destination


class DestinationSerializer(serializers.ModelSerializer):
    """
    Serializer for the Destination model.
    Handles validation and serialization of Destination objects.
    """
    class Meta:
        model = Destination
        fields = "__all__"
