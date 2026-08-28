"""Shared abstract base models for Maira Bijouterie.

Every app can inherit from these instead of ``models.Model`` so that
common fields (created_at/updated_at) are defined once and reused.
"""
from django.db import models


class TimeStampedModel(models.Model):
    """Abstract base model adding created_at and updated_at timestamps.

    Inheriting models automatically track when a row is created and when it
    was last modified, which is useful for admin sorting and dashboards.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
