from factory.django import DjangoModelFactory
import factory

from djleague import models


class FantasyTeamFactory(DjangoModelFactory):
    class Meta:
        model = models.FantasyTeam

    name = factory.Faker("last_name")
    owner = factory.Faker("first_name")
    draft_order = 1


class NFLTeam(DjangoModelFactory):
    class Meta:
        model = models.NFLTeam

    abbrev = factory.Faker("first_name")
    city = factory.Faker("city")
    byeweek = 10


class Player(DjangoModelFactory):
    class Meta:
        model = models.Player

    lastname = factory.Faker("last_name")
    firstname = factory.Faker("first_name")
    team = factory.SubFactory(NFLTeam)
    rank = 1
    points = 100
