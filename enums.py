from enum import Enum


class CharacterSkinsEnum(Enum):

    MEN1 = 'men1'
    MEN2 = 'men2'
    MEN3 = 'men3'
    WOMEN1 = 'women1'
    WOMEN2 = 'women2'
    WOMEN3 = 'women3'
    CORRUPTED1 = 'corrupted1'
    ZOMBIE1 = 'zombie1'
    MARAUDER1 = 'marauder1'
    GOBLIN1 = 'goblin1'


MALE_SKINS = [
    CharacterSkinsEnum.MEN1,
    CharacterSkinsEnum.MEN2,
    CharacterSkinsEnum.MEN3,
]

FEMALE_SKINS = [
    CharacterSkinsEnum.WOMEN1,
    CharacterSkinsEnum.WOMEN2,
    CharacterSkinsEnum.WOMEN3,
]

DEFAULT_SKINS = MALE_SKINS + FEMALE_SKINS

SEASON_SKINS = [
    CharacterSkinsEnum.CORRUPTED1,
    CharacterSkinsEnum.ZOMBIE1,
    CharacterSkinsEnum.MARAUDER1,
    CharacterSkinsEnum.GOBLIN1,
]

ALL_SKINS = DEFAULT_SKINS + SEASON_SKINS


class CharacterSexEnum(Enum):

    MALE = 'm'
    FEMALE = 'f'
    RANDOM = 'r'


SEX_SKIN_MAP = {
    'm': MALE_SKINS,
    'f': FEMALE_SKINS,
    'r': DEFAULT_SKINS,
}


class MapTypesEnum(Enum):

    MONSTER = 'monster'
    RESOURCE = 'resource'
    WORKSHOP = 'workshop'
    BANK = 'bank'
    GRAND_EXCHANGE = 'grand_exchange'
    TASKS_MASTER = 'tasks_master'
    NPC = 'npc'


class MapLayerEnum(Enum):

    INTERIOR = 'interior'
    OVERWORLD = 'overworld'
    UNDERGROUND = 'underground'


class MapAccessTypeEnum(Enum):

    STANDARD = 'standard'
    TELEPORTATION = 'teleportation'
    CONDITIONAL = 'conditional'
    BLOCKED = 'blocked'


class ActionTypeEnum(Enum):

    MOVE = 'move'
    TRANSITION = 'transition'
    EQUIP = 'equip'
    UNEQUIP = 'unequip'
    FIGHT = 'fight'
    GATHERING = 'gathering'
    CRAFTING = 'crafting'
    RECYCLING = 'recycling'
    DELETE_ITEM = 'delete item'
    USE_ITEM = 'use item'
    REST = 'rest'
    CHANGE_SKIN = 'change skin'
    NEW_TASK = 'new task'
    COMPLETE_TASK = 'complete task'
    CANCEL_TASK = 'cancel task'
    EXCHANGE_TASK = 'exchange task coins'
    TRADE_TASK = 'trade task'
    CLAIM_PENDING_ITEM = 'claim pending item'
    BUY_NPC_ITEM = 'buy npc item'
    SELL_NPC_ITEM = 'sell npc item'
    BUY_BANK_EXPANSION = 'buy bank expansion'
    DEPOSIT_BANK = 'deposit item'
    DEPOSIT_BANK_GOLD = 'deposit gold'
    WITHDRAW_BANK = 'withdraw item'
    WITHDRAW_GOLD = 'withdraw gold'
    GIVE_GOLD = 'give gold'
    GIVE_ITEM = 'give item'
    BUY_GE_ITEM = 'buy ge item'
    CANCEL_GE_ORDER = 'cancel ge order'
    CREATE_GE_BUY_ORDER = 'create ge buy order'
    CREATE_GE_SELL_ORDER = 'create ge sell order'
    FILL_GE_ORDER = 'fill ge order'
    SHOW_BANK = 'show bank'
    SHOW_PENDING_ITEMS = 'show pending items'
    SHOW_GE_ORDERS = 'show ge orders'
    SHOW_ACCOUNT_DETAILS = 'show account details'
    CHANGE_PASSWORD = 'change password'
    LOGIN_WITH_PASSWORD = 'login with password'
    SELECT_CHARACTER = 'select character'

    USE_SCENARIO = 'use scenario'


ACCOUNT_ACTIONS = [
    ActionTypeEnum.SHOW_ACCOUNT_DETAILS,
    ActionTypeEnum.CHANGE_PASSWORD,
    ActionTypeEnum.LOGIN_WITH_PASSWORD,
    ActionTypeEnum.SELECT_CHARACTER,
]


GLOBAL_ACTIONS = [
    ActionTypeEnum.MOVE,
    ActionTypeEnum.EQUIP,
    ActionTypeEnum.UNEQUIP,
    ActionTypeEnum.USE_ITEM,
    ActionTypeEnum.REST,
    ActionTypeEnum.CHANGE_SKIN,
    ActionTypeEnum.SHOW_BANK,
    ActionTypeEnum.SHOW_PENDING_ITEMS,
    ActionTypeEnum.SHOW_GE_ORDERS,
    ActionTypeEnum.CLAIM_PENDING_ITEM,
    ActionTypeEnum.GIVE_GOLD,
    ActionTypeEnum.GIVE_ITEM,
    ActionTypeEnum.USE_SCENARIO,
]

AVAILABLE_ACTIONS = list(GLOBAL_ACTIONS) + [
    ActionTypeEnum.FIGHT,
    ActionTypeEnum.GATHERING,
    ActionTypeEnum.CRAFTING,
    ActionTypeEnum.RECYCLING,
    ActionTypeEnum.NEW_TASK,
    ActionTypeEnum.COMPLETE_TASK,
    ActionTypeEnum.CANCEL_TASK,
    ActionTypeEnum.EXCHANGE_TASK,
    ActionTypeEnum.TRADE_TASK,
    ActionTypeEnum.BUY_NPC_ITEM,
    ActionTypeEnum.SELL_NPC_ITEM,
    ActionTypeEnum.BUY_BANK_EXPANSION,
    ActionTypeEnum.DEPOSIT_BANK,
    ActionTypeEnum.DEPOSIT_BANK_GOLD,
    ActionTypeEnum.WITHDRAW_BANK,
    ActionTypeEnum.WITHDRAW_GOLD,
    ActionTypeEnum.BUY_GE_ITEM,
    ActionTypeEnum.CANCEL_GE_ORDER,
    ActionTypeEnum.CREATE_GE_BUY_ORDER,
    ActionTypeEnum.CREATE_GE_SELL_ORDER,
    ActionTypeEnum.FILL_GE_ORDER,
    ActionTypeEnum.DELETE_ITEM,
]

LOCATION_ACTIONS_MAP = {
    None: list(GLOBAL_ACTIONS),
    MapTypesEnum.MONSTER.value: GLOBAL_ACTIONS + [ActionTypeEnum.FIGHT],
    MapTypesEnum.RESOURCE.value: GLOBAL_ACTIONS + [ActionTypeEnum.GATHERING],
    MapTypesEnum.WORKSHOP.value: GLOBAL_ACTIONS + [ActionTypeEnum.CRAFTING, ActionTypeEnum.RECYCLING],
    MapTypesEnum.BANK.value: GLOBAL_ACTIONS + [
        ActionTypeEnum.DEPOSIT_BANK,
        ActionTypeEnum.DEPOSIT_BANK_GOLD,
        ActionTypeEnum.WITHDRAW_BANK,
        ActionTypeEnum.WITHDRAW_GOLD,
        ActionTypeEnum.BUY_BANK_EXPANSION,
    ],
    MapTypesEnum.GRAND_EXCHANGE.value: GLOBAL_ACTIONS + [
        ActionTypeEnum.BUY_GE_ITEM,
        ActionTypeEnum.CANCEL_GE_ORDER,
        ActionTypeEnum.CREATE_GE_BUY_ORDER,
        ActionTypeEnum.CREATE_GE_SELL_ORDER,
        ActionTypeEnum.FILL_GE_ORDER,
    ],
    MapTypesEnum.TASKS_MASTER.value: GLOBAL_ACTIONS + [
        ActionTypeEnum.NEW_TASK,
        ActionTypeEnum.COMPLETE_TASK,
        ActionTypeEnum.CANCEL_TASK,
        ActionTypeEnum.EXCHANGE_TASK,
        ActionTypeEnum.TRADE_TASK,
    ],
    MapTypesEnum.NPC.value: GLOBAL_ACTIONS + [
        ActionTypeEnum.BUY_NPC_ITEM,
        ActionTypeEnum.SELL_NPC_ITEM,
    ],
}


class CraftSkillEnum(Enum):

    WEAPONCRAFTING = 'weaponcrafting'
    GEARCRAFTING = 'gearcrafting'
    JEWELRYCRAFTING = 'jewelrycrafting'
    COOKING = 'cooking'
    ALCHEMY = 'alchemy'


class GatheringSkillEnum(Enum):

    MINING = 'mining'
    WOODCUTTING = 'woodcutting'
    FISHING = 'fishing'
    ALCHEMY = 'alchemy'


class ItemTypesEnum(Enum):

    UTILITY = 'utility'
    BODY_ARMOR = 'body_armor'
    WEAPON = 'weapon'
    RESOURCE = 'resource'
    LEG_ARMOR = 'leg_armor'
    HELMET = 'helmet'
    BOOTS = 'boots'
    SHIELD = 'shield'
    AMULET = 'amulet'
    RING = 'ring'
    ARTIFACT = 'artifact'
    CURRENCY = 'currency'
    CONSUMABLE = 'consumable'
    RUNE = 'rune'
    BAG = 'bag'


EQUIP_TYPES = [
    ItemTypesEnum.UTILITY,
    ItemTypesEnum.BODY_ARMOR,
    ItemTypesEnum.WEAPON,
    ItemTypesEnum.LEG_ARMOR,
    ItemTypesEnum.HELMET,
    ItemTypesEnum.BOOTS,
    ItemTypesEnum.SHIELD,
    ItemTypesEnum.AMULET,
    ItemTypesEnum.RING,
    ItemTypesEnum.ARTIFACT,
    ItemTypesEnum.RUNE,
    ItemTypesEnum.BAG,
]


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
    RUNE = 'rune'
    UTILITY1 = 'utility1'
    UTILITY2 = 'utility2'
    BAG = 'bag'


class TaskTypeEnum(Enum):

    MONSTERS = 'monsters'
    ITEMS = 'items'


class GEOrderTypeEnum(Enum):

    SELL = 'sell'
    BUY = 'buy'


class LogTypeEnum(Enum):

    SPAWN = 'spawn'
    DELETE_CHARACTER = 'delete_character'
    MOVEMENT = 'movement'
    FIGHT = 'fight'
    MULTI_FIGHT = 'multi_fight'
    CRAFTING = 'crafting'
    GATHERING = 'gathering'
    BUY_GE = 'buy_ge'
    SELL_GE = 'sell_ge'
    CREATE_BUY_ORDER_GE = 'create_buy_order_ge'
    FILL_BUY_ORDER_GE = 'fill_buy_order_ge'
    BUY_NPC = 'buy_npc'
    SELL_NPC = 'sell_npc'
    CANCEL_GE = 'cancel_ge'
    DELETE_ITEM = 'delete_item'
    DEPOSIT_ITEM = 'deposit_item'
    WITHDRAW_ITEM = 'withdraw_item'
    DEPOSIT_GOLD = 'deposit_gold'
    WITHDRAW_GOLD = 'withdraw_gold'
    EQUIP = 'equip'
    UNEQUIP = 'unequip'
    NEW_TASK = 'new_task'
    TASK_EXCHANGE = 'task_exchange'
    TASK_CANCELLED = 'task_cancelled'
    TASK_COMPLETED = 'task_completed'
    TASK_TRADE = 'task_trade'
    RECYCLING = 'recycling'
    REST = 'rest'
    USE = 'use'
    BUY_BANK_EXPANSION = 'buy_bank_expansion'
    ACHIEVEMENT = 'achievement'
    GIVE_ITEM = 'give_item'
    GIVE_GOLD = 'give_gold'
    RECEIVE_ITEM = 'receive_item'
    RECEIVE_GOLD = 'receive_gold'
    CHANGE_SKIN = 'change_skin'
    TRANSITION = 'transition'
    CLAIM_ITEM = 'claim_item'


class EffectTypeEnum(Enum):

    EQUIPMENT = 'equipment'
    CONSUMABLE = 'consumable'
    COMBAT = 'combat'


class EffectSubtypeEnum(Enum):

    STAT = 'stat'
    OTHER = 'other'
    HEAL = 'heal'
    BUFF = 'buff'
    DEBUFF = 'debuff'
    SPECIAL = 'special'
    GATHERING = 'gathering'
    TELEPORT = 'teleport'
    GOLD = 'gold'


class NPCTypeEnum(Enum):

    MERCHANT = 'merchant'
    TRADER = 'trader'


class MonsterTypeEnum(Enum):

    NORMAL = 'normal'
    ELITE = 'elite'
    BOSS = 'boss'


class PendingItemSourceEnum(Enum):

    ACHIEVEMENT = 'achievement'
    GRAND_EXCHANGE = 'grand_exchange'
    ADMIN = 'admin'
    EVENT = 'event'
    OTHER = 'other'


class CharacterLeaderboardTypeEnum(Enum):

    COMBAT = 'combat'
    WOODCUTTING = 'woodcutting'
    MINING = 'mining'
    FISHING = 'fishing'
    WEAPONCRAFTING = 'weaponcrafting'
    GEARCRAFTING = 'gearcrafting'
    JEWELRYCRAFTING = 'jewelrycrafting'
    COOKING = 'cooking'
    ALCHEMY = 'alchemy'


class AccountLeaderboardTypeEnum(Enum):

    ACHIEVEMENTS_POINTS = 'achievements_points'
    GOLD = 'gold'


class AccountStatusEnum(Enum):

    STANDARD = 'standard'
    FOUNDER = 'founder'
    GOLD_FOUNDER = 'gold_founder'
    VIP_FOUNDER = 'vip_founder'


class FightResultEnum(Enum):

    WIN = 'win'
    LOSS = 'loss'
