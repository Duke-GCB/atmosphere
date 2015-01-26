"""
requests  - tracks requests
"""
from uuid import uuid4

from django.db import models
from django.utils import timezone

from core.models import Allocation, AtmosphereUser as User, \
    IdentityMembership, Quota


def get_status_type(status="pending"):
    (status_type, _) = StatusType.objects.get_or_create(name=status)
    return status_type


class StatusType(models.Model):
    name = models.CharField(max_length=32)
    description = models.CharField(max_length=256, default="", blank=True)
    start_date = models.DateTimeField(default=timezone.now())
    end_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'status_type'
        app_label = 'core'

    @classmethod
    def default(cls):
        return StatusType(name="pending")


class BaseRequestMixin(models.Model):
    uuid = models.CharField(max_length=36, default=uuid4)
    request = models.TextField()
    description = models.CharField(max_length=1024, default="", blank=True)
    status = models.ForeignKey(StatusType)

    # Associated creator and identity
    created_by = models.ForeignKey(User)
    membership = models.ForeignKey(IdentityMembership)

    admin_message = models.CharField(max_length=1024, default="", blank=True)

    # Request Timeline
    start_date = models.DateTimeField(default=timezone.now())
    end_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    @classmethod
    def is_active(cls, provider, user):
        """
        Returns whether or not the resource request is currently active for the
        given user and provider
        """
        status = StatusType.default()
        return cls.objects.filter(
            user=user, provider=provider, status=status).count() > 0


class AllocationRequest(BaseRequestMixin):
    """
    """
    class Meta:
        db_table = "allocation_request"
        app_label = "core"


class QuotaRequest(BaseRequestMixin):
    """
    """
    class Meta:
        db_table = "quota_request"
        app_label = "core"