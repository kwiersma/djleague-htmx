import django.utils.timezone
import factory
from factory.django import DjangoModelFactory

from accounts.models import CustomUser


class BaseFactory(DjangoModelFactory):
    uuid = factory.Faker("uuid4")
    created_date = django.utils.timezone.now()
    updated_date = django.utils.timezone.now()


class CustomUserFactory(BaseFactory):
    class Meta:
        model = CustomUser

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.Faker("email")
    username = factory.Faker("email")
    password = factory.Faker("password")
    is_active = True
