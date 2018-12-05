# Packages
from django.conf.urls import url
from canonicalwebteam.django_views import TemplateFinder


urlpatterns = [url(r"^(?P<template>.*)$", TemplateFinder.as_view())]
