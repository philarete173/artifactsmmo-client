from base.base import BaseEnumerate


class CharacterSkinsEnum(BaseEnumerate):

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
        MEN1,
        MEN2,
        MEN3,
    ]

    FEMALE_SKINS = [
        WOMEN1,
        WOMEN2,
        WOMEN3,
    ]

    DEFAULT_SKINS = MALE_SKINS + FEMALE_SKINS

    SEASON_SKINS = [
        CORRUPTED1,
        ZOMBIE1,
        MARAUDER1,
        GOBLIN1,
    ]

    ALL_SKINS = DEFAULT_SKINS + SEASON_SKINS


class CharacterSexEnum(BaseEnumerate):

    MALE = 'm'
    FEMALE = 'f'
    RANDOM = 'r'


    SEX_SKIN_MAP = {
        MALE: CharacterSkinsEnum.MALE_SKINS,
        FEMALE: CharacterSkinsEnum.FEMALE_SKINS,
        RANDOM: CharacterSkinsEnum.DEFAULT_SKINS,
    }


class CharacterDataBlocksEnum(BaseEnumerate):

    INVENTORY = 'inventory'
    EQUIPMENT = 'equipment'
    STATS = 'stats'
    SKILLS = 'skills'


class MapTypesEnum(BaseEnumerate):

    MONSTER = 'monster'
    RESOURCE = 'resource'
    WORKSHOP = 'workshop'
    BANK = 'bank'
    GRAND_EXCHANGE = 'grand_exchange'
    TASKS_MASTER = 'tasks_master'
    NPC = 'npc'


class MapLayerEnum(BaseEnumerate):

    INTERIOR = 'interior'
    OVERWORLD = 'overworld'
    UNDERGROUND = 'underground'


class MapAccessTypeEnum(BaseEnumerate):

    STANDARD = 'standard'
    TELEPORTATION = 'teleportation'
    CONDITIONAL = 'conditional'
    BLOCKED = 'blocked'


class ActionTypeEnum(BaseEnumerate):

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
    STATS = 'stats'
    SKILLS = 'skills'
    INVENTORY = 'inventory'
    EQUIPMENT = 'equipment'
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
    CREATE_CHARACTER = 'create character'

    USE_SCENARIO = 'use scenario'


    ACCOUNT_ACTIONS = [
        SHOW_ACCOUNT_DETAILS,
        CHANGE_PASSWORD,
        LOGIN_WITH_PASSWORD,
        SELECT_CHARACTER,
        CREATE_CHARACTER,
    ]

    CHARACTER_ACTIONS = [
        STATS,
        SKILLS,
        INVENTORY,
        EQUIPMENT,
        CHANGE_SKIN,
    ]

    LOCATION_ACTIONS = [
        MOVE,
        EQUIP,
        UNEQUIP,
        USE_ITEM,
        REST,
        USE_SCENARIO,
    ]

    ADVANCED_ACTIONS = [
        SHOW_BANK,
        SHOW_PENDING_ITEMS,
        SHOW_GE_ORDERS,
        CLAIM_PENDING_ITEM,
        GIVE_GOLD,
        GIVE_ITEM,
    ]

    LOCATION_ACTIONS_MAP = {
        None: LOCATION_ACTIONS,
        MapTypesEnum.MONSTER: LOCATION_ACTIONS + [FIGHT],
        MapTypesEnum.RESOURCE: LOCATION_ACTIONS + [GATHERING],
        MapTypesEnum.WORKSHOP: LOCATION_ACTIONS + [CRAFTING, RECYCLING],
        MapTypesEnum.BANK: LOCATION_ACTIONS + [
            DEPOSIT_BANK,
            DEPOSIT_BANK_GOLD,
            WITHDRAW_BANK,
            WITHDRAW_GOLD,
            BUY_BANK_EXPANSION,
        ],
        MapTypesEnum.GRAND_EXCHANGE: LOCATION_ACTIONS + [
            BUY_GE_ITEM,
            CANCEL_GE_ORDER,
            CREATE_GE_BUY_ORDER,
            CREATE_GE_SELL_ORDER,
            FILL_GE_ORDER,
        ],
        MapTypesEnum.TASKS_MASTER: LOCATION_ACTIONS + [
            NEW_TASK,
            COMPLETE_TASK,
            CANCEL_TASK,
            EXCHANGE_TASK,
            TRADE_TASK,
        ],
        MapTypesEnum.NPC: LOCATION_ACTIONS + [
            BUY_NPC_ITEM,
            SELL_NPC_ITEM,
        ],
    }


class CraftSkillEnum(BaseEnumerate):

    WEAPONCRAFTING = 'weaponcrafting'
    GEARCRAFTING = 'gearcrafting'
    JEWELRYCRAFTING = 'jewelrycrafting'
    COOKING = 'cooking'
    ALCHEMY = 'alchemy'


class GatheringSkillEnum(BaseEnumerate):

    MINING = 'mining'
    WOODCUTTING = 'woodcutting'
    FISHING = 'fishing'
    ALCHEMY = 'alchemy'


class ItemTypesEnum(BaseEnumerate):

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
        UTILITY,
        BODY_ARMOR,
        WEAPON,
        LEG_ARMOR,
        HELMET,
        BOOTS,
        SHIELD,
        AMULET,
        RING,
        ARTIFACT,
        RUNE,
        BAG,
    ]


class EquipmentSlotsEnum(BaseEnumerate):

    HELMET = 'helmet'
    BODY_ARMOR = 'body_armor'
    LEG_ARMOR = 'leg_armor'
    BOOTS = 'boots'
    WEAPON = 'weapon'
    SHIELD = 'shield'
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


class TaskTypeEnum(BaseEnumerate):

    MONSTERS = 'monsters'
    ITEMS = 'items'


class GEOrderTypeEnum(BaseEnumerate):

    SELL = 'sell'
    BUY = 'buy'


class LogTypeEnum(BaseEnumerate):

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


class EffectTypeEnum(BaseEnumerate):

    EQUIPMENT = 'equipment'
    CONSUMABLE = 'consumable'
    COMBAT = 'combat'


class EffectSubtypeEnum(BaseEnumerate):

    STAT = 'stat'
    OTHER = 'other'
    HEAL = 'heal'
    BUFF = 'buff'
    DEBUFF = 'debuff'
    SPECIAL = 'special'
    GATHERING = 'gathering'
    TELEPORT = 'teleport'
    GOLD = 'gold'


class NPCTypeEnum(BaseEnumerate):

    MERCHANT = 'merchant'
    TRADER = 'trader'


class MonsterTypeEnum(BaseEnumerate):

    NORMAL = 'normal'
    ELITE = 'elite'
    BOSS = 'boss'


class PendingItemSourceEnum(BaseEnumerate):

    ACHIEVEMENT = 'achievement'
    GRAND_EXCHANGE = 'grand_exchange'
    ADMIN = 'admin'
    EVENT = 'event'
    OTHER = 'other'


class CharacterLeaderboardTypeEnum(BaseEnumerate):

    COMBAT = 'combat'
    WOODCUTTING = 'woodcutting'
    MINING = 'mining'
    FISHING = 'fishing'
    WEAPONCRAFTING = 'weaponcrafting'
    GEARCRAFTING = 'gearcrafting'
    JEWELRYCRAFTING = 'jewelrycrafting'
    COOKING = 'cooking'
    ALCHEMY = 'alchemy'


class AccountLeaderboardTypeEnum(BaseEnumerate):

    ACHIEVEMENTS_POINTS = 'achievements_points'
    GOLD = 'gold'


class AccountStatusEnum(BaseEnumerate):

    STANDARD = 'standard'
    FOUNDER = 'founder'
    GOLD_FOUNDER = 'gold_founder'
    VIP_FOUNDER = 'vip_founder'


class FightResultEnum(BaseEnumerate):

    WIN = 'win'
    LOSS = 'loss'


class ImageCategoryEnum(BaseEnumerate):

    CHARACTERS = 'characters'
    MAPS = 'maps'
