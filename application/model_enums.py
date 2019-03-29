from enum import Enum


class DistanceUnit(Enum):
    KILOMETER = 'km.'
    MILE = 'mi.'

    @classmethod
    def choices(cls):
        return [(v.name, v.value) for v in cls]


class TravelType(Enum):
    NONE = 'Aucun'
    CAR = 'Voiture'
    FLIGHT = 'Avion'

    @classmethod
    def choices(cls):
        return [(v.name, v.value) for v in cls]


class StayType(Enum):
    HOTEL = 'Hôtel/Motel'
    FRIENDS = 'Chez des Amis'
    CAMPING = 'Sous tente'
    HOUSE = 'Maison de Vacances'

    @classmethod
    def choices(cls):
        return [(v.name, v.value) for v in cls]
