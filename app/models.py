from django.db import models
from .choices import CLOUD_PROVIDERS, PRODUCTS


# Create your models here.
class Source(models.Model):
    """ Model representing a cloud storage source. """
    name = models.CharField(max_length=100, unique=True, help_text="Unique name for the source")
    cloud = models.CharField(max_length=50, choices=CLOUD_PROVIDERS)
    product = models.CharField(max_length=50, choices=PRODUCTS)
    region = models.CharField(max_length=100)
    auth = models.JSONField(default=dict, help_text="JSON object with authentication details")

    # Audit fields for tracking creation and updates to the model instances
    created_by = models.CharField(max_length=150, default="system")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """ String representation of the Source model. """
        return self.name


class Destination(models.Model):
    """ Model representing a cloud storage destination. """
    cloud = models.CharField(max_length=50, choices=CLOUD_PROVIDERS)
    product = models.CharField(max_length=50, choices=PRODUCTS)
    region = models.CharField(max_length=100)
    auth = models.JSONField(default=dict, help_text="JSON object with authentication details")

    # Audit fields for tracking creation and updates to the model instances
    created_by = models.CharField(max_length=150, default="system")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """ String representation of the Destination model. """
        return f"{self.cloud}-{self.product}"
