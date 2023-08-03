from __future__ import annotations

from django.apps import AppConfig


class DefaultConfig(AppConfig):
    name = "tests.test_project.app_with_custom_name"
    label = "my_custom_name"
