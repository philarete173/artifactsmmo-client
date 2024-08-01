from enum import Enum


class CharacterSkinsEnum(Enum):
    MEN1 = 'men1'
    MEN2 = 'men2'
    MEN3 = 'men3'
    WOMEN1 = 'women1'
    WOMEN2 = 'women2'
    WOMEN3 = 'women3'

    MALE_SKINS = [
        MEN1,
        MEN2,
        MEN3,
    ]

    FEMALE_SKINS = [
        WOMEN1,
        WOMEN2,
        WOMEN3,
    ]


class CharacterSexEnum(Enum):

    MALE = 'm'
    FEMALE = 'f'
    RANDOM = 'r'

    SEX_SKIN_MAP = {
        'm': CharacterSkinsEnum.MALE_SKINS.value,
        'f': CharacterSkinsEnum.FEMALE_SKINS.value,
        'r': CharacterSkinsEnum.MALE_SKINS.value + CharacterSkinsEnum.FEMALE_SKINS.value,
    }


class ActionTypeEnum(Enum):

    MOVE = 'move'
    EQUIP = 'equip'
    UNEQUIP = 'unequip'
    FIGHT = 'fight'
    GATHERING = 'gathering'
    CRAFTING = 'crafting'
    RECYCLING = 'recycling'
    DELETE = 'delete'

    AVAILABLE_ACTIONS = [
        MOVE,
        FIGHT,
        GATHERING,
        CRAFTING,
    ]


class MapTypesEnum(Enum):

    MONSTER = 'monster'
    RESOURCE = 'resource'
    WORKSHOP = 'workshop'
    BANK = 'bank'
    GRAND_EXCHANGE = 'grand_exchange'
    TASKS_MASTER = 'tasks_master'


class CraftSkillEnum(Enum):

    WEAPONCRAFTING = 'weaponcrafting'
    GEARCRAFTING = 'gearcrafting'
    JEWELRYCRAFTING = 'jewelrycrafting'
    COOKING = 'cooking'
    WOODCUTTING = 'woodcutting'
    MINING = 'mining'
    FISHING = 'fishing'


class ItemTypesEnum(Enum):

    CONSUMABLE = 'consumable'
    BODY_ARMOR = 'body_armor'
    WEAPON = 'weapon'
    RESOURCE = 'resource'
    LEG_ARMOR = 'leg_armor'
    HELMET = 'helmet'
    BOOTS = 'boots'
    SHIELD = 'shield'
    AMULET = 'amulet'
    RING = 'ring'


class EquipmentSlotsEnum(Enum):
    WEAPON = 'weapon'
    SHIELD = 'shield'
    HELMET = 'helmet'
    BODY_ARMOR = 'body_armor'
    LEG_ARMOR = 'leg_armor'
    BOOTS = 'boots'
    RING1 = 'ring1'
    RING2 = 'ring2'
    AMULET = 'amulet'
    ARTIFACT1 = 'artifact1'
    ARTIFACT2 = 'artifact2'
    ARTIFACT3 = 'artifact3'
    CONSUMABLE1 = 'consumable1'
    CONSUMABLE2 = 'consumable2'
