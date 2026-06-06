import functools
from base import BaseClient
from enums import MapTypesEnum, TaskTypeEnum
from items_scripts import ItemsScenarios


class _ScenarioHelpers(BaseClient):
    """Base class for scenario collections.

    All helpers are static methods that take the active character as
    the first argument, so that ScenariosStorage can bind ``self.character``
    once via :func:`functools.partial` and the rest of the codebase keeps
    treating scenarios as zero-argument callables.
    """

    EQUIPMENT_SLOTS = [
        'weapon_slot', 'shield_slot', 'helmet_slot', 'body_armor_slot',
        'leg_armor_slot', 'boots_slot', 'ring1_slot', 'ring2_slot',
        'amulet_slot', 'artifact1_slot', 'artifact2_slot', 'artifact3_slot',
        'rune_slot', 'utility1_slot', 'utility2_slot', 'bag_slot',
    ]

    @classmethod
    def _fetch_location_coordinates(cls, character, content_code='', content_type=''):
        params = {'size': 1}

        if content_code:
            params['content_code'] = content_code

        if content_type:
            params['content_type'] = content_type

        result = None
        response = character._get(url='/maps', data=params)

        if response.status_code == 200:
            data = response.json().get('data', [])

            if data:
                location = data[0]
                result = (location['x'], location['y'], location.get('layer', 'overworld'))

        return result

    @classmethod
    def _get_location_for_content(cls, character, content_code='', content_type=''):
        location = cls._fetch_location_coordinates(character, content_code, content_type)

        if location is None and (error_block := character._get(url='/maps', data={'size': 1}).json().get('error')):
            print(f'Can\'t get location data. {error_block.get("message", "Unknown error.")}.')

        return location

    @classmethod
    def _ensure_at(cls, character, target_x, target_y, target_layer=None):
        already_there = (
            character.x == target_x
            and character.y == target_y
            and (target_layer is None or character.layer == target_layer)
        )

        result = already_there or character.move(target_x, target_y) is not None

        return result

    @classmethod
    def _sell_item(cls, character, item_name='', quantity=1):
        ge = cls._get_location_for_content(character, content_type=MapTypesEnum.GRAND_EXCHANGE.value)

        if ge:
            character.move(*ge[:2])

        character.ge_create_sell_order(item_name, quantity, price=0)


class GatherScenarios(_ScenarioHelpers):
    """Collection of gather-resource scenarios.

    All methods are static and take ``character`` as the first argument.
    """

    CATEGORY = 'Gather resources'

    @classmethod
    def get_scenarios(cls, character):
        scenarios_list = [
            cls.gather_copper_ore,
            cls.gather_ash_wood,
        ]

        if character.mining_level >= 10:
            scenarios_list.append(cls.gather_iron_ore)

        if character.mining_level >= 20:
            scenarios_list.extend([
                cls.gather_iron_ore,
                cls.gather_coal,
            ])

        if character.mining_level >= 30:
            scenarios_list.append(cls.gather_gold_ore)

        if character.woodcutting_level >= 10:
            scenarios_list.append(cls.gather_spruce_wood)

        if character.woodcutting_level >= 20:
            scenarios_list.append(cls.gather_birch_wood)

        if character.woodcutting_level >= 30:
            scenarios_list.append(cls.gather_dead_wood)

        scenarios_list.extend([
            cls.gather_resource_from_location,
            cls.gather_resource_from_monsters,
        ])

        return scenarios_list

    @classmethod
    def gather_resource_from_location(cls, character, item_code='', quantity=1):
        cls._gather_resource(character, type_from='resources', item_code=item_code, quantity=quantity)

    @classmethod
    def gather_resource_from_monsters(cls, character, item_code='', quantity=1):
        cls._gather_resource(character, type_from='monsters', item_code=item_code, quantity=quantity)

    @classmethod
    def gather_copper_ore(cls, character, quantity=1):
        cls.gather_resource_from_location(character, 'copper_ore', quantity)

    @classmethod
    def gather_iron_ore(cls, character, quantity=1):
        cls.gather_resource_from_location(character, 'iron_ore', quantity)

    @classmethod
    def gather_coal(cls, character, quantity=1):
        cls.gather_resource_from_location(character, 'coal', quantity)

    @classmethod
    def gather_gold_ore(cls, character, quantity=1):
        cls.gather_resource_from_location(character, 'gold_ore', quantity)

    @classmethod
    def gather_ash_wood(cls, character, quantity=1):
        cls.gather_resource_from_location(character, 'ash_wood', quantity)

    @classmethod
    def gather_spruce_wood(cls, character, quantity=1):
        cls.gather_resource_from_location(character, 'spruce_wood', quantity)

    @classmethod
    def gather_birch_wood(cls, character, quantity=1):
        cls.gather_resource_from_location(character, 'birch_wood', quantity)

    @classmethod
    def gather_dead_wood(cls, character, quantity=1):
        cls.gather_resource_from_location(character, 'dead_wood', quantity)

    @classmethod
    def _gather_resource(cls, character, type_from='', item_code='', quantity=1):
        item_data = cls._gather_item_data(character, type_from, item_code)

        if item_data is None:
            return

        cls._run_gather_loop(character, type_from, item_data, item_code, quantity)

    @classmethod
    def _gather_item_data(cls, character, type_from, item_code):
        response = character._get(
            url=f'/{type_from}',
            data={
                'drop': item_code,
                'size': 1,
            },
        )

        result = None

        if response.status_code == 200:
            result = response.json()['data'][0]
        elif error_block := response.json().get('error'):
            print(f'Can\'t get item data. {error_block.get("message", "Unknown error.")}.')

        return result

    @classmethod
    def _run_gather_loop(cls, character, type_from, item_data, item_code, quantity):
        content_code = item_data['code']
        location = cls._get_location_for_content(character, content_code)

        if not location:
            return

        x, y, _ = location
        character.move(x, y)

        current_quantity = cls._build_quantity_counter(character, item_code)

        while current_quantity() < quantity:
            if type_from == 'resources':
                character.gathering()
            elif type_from == 'monsters':
                cls._ensure_at(character, x, y)
                character.fight()

    @classmethod
    def _build_quantity_counter(cls, character, item_code):
        def current_quantity():
            result = 0

            for slot in character.inventory or []:
                if slot.get('code') == item_code:
                    result = slot.get('quantity', 0)
                    break

            return result

        return current_quantity


class CraftResourcesScenarios(_ScenarioHelpers):
    """Collection of basic-resource crafting scenarios (ingots, planks)."""

    CATEGORY = 'Craft resources'

    @classmethod
    def get_scenarios(cls, character):
        scenarios_list = [
            cls.craft_copper,
            cls.craft_ash_planks,
        ]

        if character.mining_level >= 10:
            scenarios_list.append(cls.craft_iron)

        if character.mining_level >= 20:
            scenarios_list.append(cls.craft_steel)

        if character.mining_level >= 30:
            scenarios_list.append(cls.craft_gold)

        if character.woodcutting_level >= 10:
            scenarios_list.append(cls.craft_spruce_planks)

        if character.woodcutting_level >= 20:
            scenarios_list.append(cls.craft_hardwood_planks)

        if character.woodcutting_level >= 30:
            scenarios_list.append(cls.craft_dead_wood_planks)

        return scenarios_list

    @classmethod
    def craft_copper(cls, character, quantity=1):
        GatherScenarios.gather_copper_ore(character, 8 * quantity)
        cls._craft_metal(character, 'copper', quantity)

    @classmethod
    def craft_iron(cls, character, quantity=1):
        GatherScenarios.gather_iron_ore(character, 8 * quantity)
        cls._craft_metal(character, 'iron', quantity)

    @classmethod
    def craft_steel(cls, character, quantity=1):
        GatherScenarios.gather_iron_ore(character, 3 * quantity)
        GatherScenarios.gather_coal(character, 5 * quantity)
        cls._craft_metal(character, 'steel', quantity)

    @classmethod
    def craft_gold(cls, character, quantity=1):
        GatherScenarios.gather_gold_ore(character, 8 * quantity)
        cls._craft_metal(character, 'gold', quantity)

    @classmethod
    def craft_ash_planks(cls, character, quantity=1):
        GatherScenarios.gather_ash_wood(character, 8 * quantity)
        cls._craft_planks(character, 'ash_plank', quantity)

    @classmethod
    def craft_spruce_planks(cls, character, quantity=1):
        GatherScenarios.gather_spruce_wood(character, 8 * quantity)
        cls._craft_planks(character, 'spruce_plank', quantity)

    @classmethod
    def craft_hardwood_planks(cls, character, quantity=1):
        GatherScenarios.gather_ash_wood(character, 3 * quantity)
        GatherScenarios.gather_birch_wood(character, 5 * quantity)
        cls._craft_planks(character, 'hardwood_plank', quantity)

    @classmethod
    def craft_dead_wood_planks(cls, character, quantity=1):
        GatherScenarios.gather_dead_wood(character, 8 * quantity)
        cls._craft_planks(character, 'dead_wood_plank', quantity)

    @classmethod
    def _craft_metal(cls, character, item_code='', quantity=1):
        ws = cls._get_location_for_content(character, content_code='mining')

        if ws:
            character.move(*ws[:2])

        character.crafting(item_code, quantity)

    @classmethod
    def _craft_planks(cls, character, item_code='', quantity=1):
        ws = cls._get_location_for_content(character, content_code='woodcutting')

        if ws:
            character.move(*ws[:2])

        character.crafting(item_code, quantity)


class CraftEquipmentScenarios(_ScenarioHelpers):
    """Collection of equipment crafting scenarios (weapons, gear, jewelry)."""

    CATEGORY = 'Craft equipment'

    @classmethod
    def get_scenarios(cls, character):
        scenarios_list = [
            cls.craft_wooden_staff,
            cls.craft_wooden_shield,
            cls.craft_copper_dagger,
            cls.craft_copper_helmet,
            cls.craft_copper_boots,
            cls.craft_copper_ring,
        ]

        if character.weaponcrafting_level >= 5:
            scenarios_list.extend([
                cls.craft_sticky_dagger,
                cls.craft_sticky_sword,
            ])

        if character.weaponcrafting_level >= 10:
            scenarios_list.extend([
                cls.craft_iron_dagger,
                cls.craft_iron_sword,
                cls.craft_greater_wooden_staff,
                cls.craft_fire_bow,
            ])

        if character.weaponcrafting_level >= 15:
            scenarios_list.extend([
                cls.craft_multislimes_sword,
                cls.craft_mushstaff,
                cls.craft_mushmush_bow,
            ])

        if character.gearcrafting_level >= 5:
            scenarios_list.extend([
                cls.craft_copper_armor,
                cls.craft_copper_legs_armor,
                cls.craft_feather_coat,
            ])

        if character.gearcrafting_level >= 10:
            scenarios_list.extend([
                cls.craft_iron_boots,
                cls.craft_adventurer_helmet,
                cls.craft_adventurer_pants,
                cls.craft_adventurer_vest,
                cls.craft_slime_shield,
            ])

        if character.gearcrafting_level >= 15:
            scenarios_list.extend([
                cls.craft_adventurer_boots,
            ])

        if character.jewelrycrafting_level >= 5:
            scenarios_list.extend([
                cls.craft_life_amulet,
            ])

        if character.jewelrycrafting_level >= 10:
            scenarios_list.extend([
                cls.craft_iron_ring,
                cls.craft_fire_and_earth_amulet,
                cls.craft_air_and_water_amulet,
            ])

        if character.jewelrycrafting_level >= 15:
            scenarios_list.extend([
                cls.craft_air_ring,
                cls.craft_earth_ring,
                cls.craft_fire_ring,
                cls.craft_water_ring,
                cls.craft_life_ring,
            ])

        return scenarios_list

    @classmethod
    def craft_wooden_staff(cls, character, quantity=1, sell=False):
        CraftResourcesScenarios.craft_ash_planks(character, 3 * quantity)
        GatherScenarios.gather_ash_wood(character, 4 * quantity)
        cls._craft_weapon(character, 'wooden_stick', quantity)
        cls._craft_weapon(character, 'wooden_staff', quantity)

        if sell:
            _ScenarioHelpers._sell_item(character, 'wooden_staff', quantity)

    @classmethod
    def craft_wooden_shield(cls, character, quantity=1, sell=False):
        CraftResourcesScenarios.craft_ash_planks(character, 6 * quantity)
        cls._craft_gear(character, 'wooden_shield', quantity)

        if sell:
            _ScenarioHelpers._sell_item(character, 'wooden_shield', quantity)

    @classmethod
    def craft_copper_dagger(cls, character, quantity=1, sell=False):
        CraftResourcesScenarios.craft_copper(character, 6 * quantity)
        cls._craft_weapon(character, 'copper_dagger', quantity)

        if sell:
            _ScenarioHelpers._sell_item(character, 'copper_dagger', quantity)

    @classmethod
    def craft_copper_helmet(cls, character, quantity=1, sell=False):
        CraftResourcesScenarios.craft_copper(character, 6 * quantity)
        cls._craft_gear(character, 'copper_helmet', quantity)

        if sell:
            _ScenarioHelpers._sell_item(character, 'copper_helmet', quantity)

    @classmethod
    def craft_copper_boots(cls, character, quantity=1, sell=False):
        CraftResourcesScenarios.craft_copper(character, 8 * quantity)
        cls._craft_gear(character, 'copper_boots', quantity)

        if sell:
            _ScenarioHelpers._sell_item(character, 'copper_boots', quantity)

    @classmethod
    def craft_copper_ring(cls, character, quantity=1, sell=False):
        CraftResourcesScenarios.craft_copper(character, 6 * quantity)
        cls._craft_jewelry(character, 'copper_ring', quantity)

        if sell:
            _ScenarioHelpers._sell_item(character, 'copper_ring', quantity)

    @classmethod
    def craft_copper_armor(cls, character, quantity=1, sell=False):
        CraftResourcesScenarios.craft_copper(character, 5 * quantity)
        GatherScenarios.gather_resource_from_monsters(character, 'feather', 2 * quantity)
        cls._craft_gear(character, 'copper_armor', quantity)

        if sell:
            _ScenarioHelpers._sell_item(character, 'copper_armor', quantity)

    @classmethod
    def craft_copper_legs_armor(cls, character, quantity=1, sell=False):
        CraftResourcesScenarios.craft_copper(character, 6 * quantity)
        cls._craft_gear(character, 'copper_legs_armor', quantity)

        if sell:
            _ScenarioHelpers._sell_item(character, 'copper_legs_armor', quantity)

    @classmethod
    def craft_feather_coat(cls, character, quantity=1, sell=False):
        GatherScenarios.gather_resource_from_monsters(character, 'feather', 6 * quantity)
        cls._craft_gear(character, 'feather_coat', quantity)

        if sell:
            _ScenarioHelpers._sell_item(character, 'feather_coat', quantity)

    @classmethod
    def craft_life_amulet(cls, character, quantity=1, sell=False):
        GatherScenarios.gather_resource_from_monsters(character, 'blue_slimeball', 2 * quantity)
        GatherScenarios.gather_resource_from_monsters(character, 'red_slimeball', 2 * quantity)
        GatherScenarios.gather_resource_from_monsters(character, 'feather', 4 * quantity)
        cls._craft_jewelry(character, 'life_amulet', quantity)

        if sell:
            _ScenarioHelpers._sell_item(character, 'life_amulet', quantity)

    @classmethod
    def craft_sticky_dagger(cls, character, quantity=1, sell=False):
        CraftResourcesScenarios.craft_copper(character, 5 * quantity)
        GatherScenarios.gather_resource_from_monsters(character, 'green_slimeball', 2 * quantity)
        cls._craft_weapon(character, 'sticky_dagger', quantity)

        if sell:
            _ScenarioHelpers._sell_item(character, 'sticky_dagger', quantity)

    @classmethod
    def craft_sticky_sword(cls, character, quantity=1, sell=False):
        CraftResourcesScenarios.craft_copper(character, 5 * quantity)
        GatherScenarios.gather_resource_from_monsters(character, 'yellow_slimeball', 2 * quantity)
        cls._craft_weapon(character, 'sticky_sword', quantity)

        if sell:
            _ScenarioHelpers._sell_item(character, 'sticky_sword', quantity)

    @classmethod
    def craft_iron_dagger(cls, character, quantity=1, sell=False):
        CraftResourcesScenarios.craft_copper(character, 2 * quantity)
        CraftResourcesScenarios.craft_iron(character, 6 * quantity)
        cls._craft_weapon(character, 'iron_dagger', quantity)

        if sell:
            _ScenarioHelpers._sell_item(character, 'iron_dagger', quantity)

    @classmethod
    def craft_iron_sword(cls, character, quantity=1, sell=False):
        CraftResourcesScenarios.craft_iron(character, 8 * quantity)
        cls._craft_weapon(character, 'iron_sword', quantity)

        if sell:
            _ScenarioHelpers._sell_item(character, 'iron_sword', quantity)

    @classmethod
    def craft_greater_wooden_staff(cls, character, quantity=1, sell=False):
        CraftResourcesScenarios.craft_ash_planks(character, 3 * quantity)
        CraftResourcesScenarios.craft_spruce_planks(character, 4 * quantity)
        cls._craft_weapon(character, 'greater_wooden_staff', quantity)

        if sell:
            _ScenarioHelpers._sell_item(character, 'greater_wooden_staff', quantity)

    @classmethod
    def craft_fire_bow(cls, character, quantity=1, sell=False):
        CraftResourcesScenarios.craft_spruce_planks(character, 4 * quantity)
        GatherScenarios.gather_resource_from_monsters(character, 'red_slimeball', 2 * quantity)
        cls._craft_weapon(character, 'fire_bow', quantity)

        if sell:
            _ScenarioHelpers._sell_item(character, 'fire_bow', quantity)

    @classmethod
    def craft_iron_boots(cls, character, quantity=1, sell=False):
        CraftResourcesScenarios.craft_iron(character, 5 * quantity)
        GatherScenarios.gather_resource_from_monsters(character, 'feather', 3 * quantity)
        cls._craft_gear(character, 'iron_boots', quantity)

        if sell:
            _ScenarioHelpers._sell_item(character, 'iron_boots', quantity)

    @classmethod
    def craft_iron_ring(cls, character, quantity=1, sell=False):
        CraftResourcesScenarios.craft_iron(character, 6 * quantity)
        cls._craft_jewelry(character, 'iron_ring', quantity)

        if sell:
            _ScenarioHelpers._sell_item(character, 'iron_ring', quantity)

    @classmethod
    def craft_fire_and_earth_amulet(cls, character, quantity=1, sell=False):
        CraftResourcesScenarios.craft_copper(character, 3 * quantity)
        CraftResourcesScenarios.craft_iron(character, 4 * quantity)
        GatherScenarios.gather_resource_from_monsters(character, 'red_slimeball', 3 * quantity)
        GatherScenarios.gather_resource_from_monsters(character, 'yellow_slimeball', 3 * quantity)
        cls._craft_jewelry(character, 'fire_and_earth_amulet', quantity)

        if sell:
            _ScenarioHelpers._sell_item(character, 'fire_and_earth_amulet', quantity)

    @classmethod
    def craft_air_and_water_amulet(cls, character, quantity=1, sell=False):
        CraftResourcesScenarios.craft_copper(character, 2 * quantity)
        CraftResourcesScenarios.craft_iron(character, 6 * quantity)
        GatherScenarios.gather_resource_from_monsters(character, 'green_slimeball', 3 * quantity)
        GatherScenarios.gather_resource_from_monsters(character, 'blue_slimeball', 3 * quantity)
        cls._craft_jewelry(character, 'air_and_water_amulet', quantity)

        if sell:
            _ScenarioHelpers._sell_item(character, 'air_and_water_amulet', quantity)

    @classmethod
    def craft_slime_shield(cls, character, quantity=1, sell=False):
        CraftResourcesScenarios.craft_spruce_planks(character, 6 * quantity)
        GatherScenarios.gather_resource_from_monsters(character, 'green_slimeball', 3 * quantity)
        GatherScenarios.gather_resource_from_monsters(character, 'blue_slimeball', 3 * quantity)
        GatherScenarios.gather_resource_from_monsters(character, 'red_slimeball', 3 * quantity)
        GatherScenarios.gather_resource_from_monsters(character, 'yellow_slimeball', 3 * quantity)
        cls._craft_gear(character, 'slime_shield', quantity)

        if sell:
            _ScenarioHelpers._sell_item(character, 'slime_shield', quantity)

    @classmethod
    def craft_adventurer_helmet(cls, character, quantity=1, sell=False):
        CraftResourcesScenarios.craft_spruce_planks(character, 3 * quantity)
        GatherScenarios.gather_resource_from_monsters(character, 'feather', 4 * quantity)
        GatherScenarios.gather_resource_from_monsters(character, 'cowhide', 3 * quantity)
        GatherScenarios.gather_resource_from_monsters(character, 'mushroom', 4 * quantity)
        cls._craft_gear(character, 'adventurer_helmet', quantity)

        if sell:
            _ScenarioHelpers._sell_item(character, 'adventurer_helmet', quantity)

    @classmethod
    def craft_adventurer_pants(cls, character, quantity=1, sell=False):
        CraftResourcesScenarios.craft_iron(character, 2 * quantity)
        GatherScenarios.gather_resource_from_monsters(character, 'cowhide', 8 * quantity)
        GatherScenarios.gather_resource_from_monsters(character, 'mushroom', 2 * quantity)
        cls._craft_gear(character, 'adventurer_pants', quantity)

        if sell:
            _ScenarioHelpers._sell_item(character, 'adventurer_pants', quantity)

    @classmethod
    def craft_adventurer_vest(cls, character, quantity=1, sell=False):
        CraftResourcesScenarios.craft_spruce_planks(character, 4 * quantity)
        GatherScenarios.gather_resource_from_monsters(character, 'feather', 2 * quantity)
        GatherScenarios.gather_resource_from_monsters(character, 'cowhide', 6 * quantity)
        GatherScenarios.gather_resource_from_monsters(character, 'yellow_slimeball', 4 * quantity)
        cls._craft_gear(character, 'adventurer_vest', quantity)

        if sell:
            _ScenarioHelpers._sell_item(character, 'adventurer_vest', quantity)

    @classmethod
    def craft_adventurer_boots(cls, character, quantity=1, sell=False):
        CraftResourcesScenarios.craft_spruce_planks(character, 2 * quantity)
        GatherScenarios.gather_resource_from_monsters(character, 'cowhide', 6 * quantity)
        GatherScenarios.gather_resource_from_monsters(character, 'wolf_hair', 4 * quantity)
        GatherScenarios.gather_resource_from_monsters(character, 'mushroom', 3 * quantity)
        CraftResourcesScenarios.craft_spruce_planks(character, 2 * quantity)
        cls._craft_gear(character, 'adventurer_boots', quantity)

        if sell:
            _ScenarioHelpers._sell_item(character, 'adventurer_boots', quantity)

    @classmethod
    def craft_multislimes_sword(cls, character, quantity=1, sell=False):
        cls.craft_iron_sword(character, quantity)
        GatherScenarios.gather_resource_from_monsters(character, 'red_slimeball', 3 * quantity)
        GatherScenarios.gather_resource_from_monsters(character, 'green_slimeball', 3 * quantity)
        GatherScenarios.gather_resource_from_monsters(character, 'blue_slimeball', 3 * quantity)
        GatherScenarios.gather_resource_from_monsters(character, 'yellow_slimeball', 3 * quantity)
        cls._craft_weapon(character, 'multislimes_sword', quantity)

        if sell:
            _ScenarioHelpers._sell_item(character, 'multislimes_sword', quantity)

    @classmethod
    def craft_mushstaff(cls, character, quantity=1, sell=False):
        CraftResourcesScenarios.craft_spruce_planks(character, 5 * quantity)
        CraftResourcesScenarios.craft_iron(character, quantity)
        GatherScenarios.gather_resource_from_monsters(character, 'mushroom', 5 * quantity)
        GatherScenarios.gather_resource_from_monsters(character, 'flying_wing', 2 * quantity)
        cls._craft_weapon(character, 'mushstaff', quantity)

        if sell:
            _ScenarioHelpers._sell_item(character, 'mushstaff', quantity)

    @classmethod
    def craft_mushmush_bow(cls, character, quantity=1, sell=False):
        CraftResourcesScenarios.craft_spruce_planks(character, 6 * quantity)
        GatherScenarios.gather_resource_from_monsters(character, 'wolf_hair', 3 * quantity)
        GatherScenarios.gather_resource_from_monsters(character, 'mushroom', 4 * quantity)
        cls._craft_weapon(character, 'mushmush_bow', quantity)

        if sell:
            _ScenarioHelpers._sell_item(character, 'mushmush_bow', quantity)

    @classmethod
    def craft_air_ring(cls, character, quantity=1, sell=False):
        cls.craft_iron_ring(character, quantity)
        GatherScenarios.gather_resource_from_monsters(character, 'green_slimeball', 4 * quantity)
        GatherScenarios.gather_resource_from_monsters(character, 'flying_wing', 2 * quantity)
        cls._craft_jewelry(character, 'air_ring', quantity)

        if sell:
            _ScenarioHelpers._sell_item(character, 'air_ring', quantity)

    @classmethod
    def craft_earth_ring(cls, character, quantity=1, sell=False):
        cls.craft_iron_ring(character, quantity)
        GatherScenarios.gather_resource_from_monsters(character, 'yellow_slimeball', 4 * quantity)
        GatherScenarios.gather_resource_from_monsters(character, 'mushroom', 2 * quantity)
        cls._craft_jewelry(character, 'earth_ring', quantity)

        if sell:
            _ScenarioHelpers._sell_item(character, 'earth_ring', quantity)

    @classmethod
    def craft_fire_ring(cls, character, quantity=1, sell=False):
        cls.craft_iron_ring(character, quantity)
        GatherScenarios.gather_resource_from_monsters(character, 'red_slimeball', 4 * quantity)
        GatherScenarios.gather_resource_from_monsters(character, 'mushroom', 2 * quantity)
        cls._craft_jewelry(character, 'fire_ring', quantity)

        if sell:
            _ScenarioHelpers._sell_item(character, 'fire_ring', quantity)

    @classmethod
    def craft_water_ring(cls, character, quantity=1, sell=False):
        cls.craft_iron_ring(character, quantity)
        GatherScenarios.gather_resource_from_monsters(character, 'blue_slimeball', 4 * quantity)
        GatherScenarios.gather_resource_from_monsters(character, 'flying_wing', 2 * quantity)
        cls._craft_jewelry(character, 'water_ring', quantity)

        if sell:
            _ScenarioHelpers._sell_item(character, 'water_ring', quantity)

    @classmethod
    def craft_life_ring(cls, character, quantity=1, sell=False):
        cls.craft_iron_ring(character, quantity)
        GatherScenarios.gather_resource_from_monsters(character, 'feather', 2 * quantity)
        GatherScenarios.gather_resource_from_monsters(character, 'mushroom', 2 * quantity)
        cls._craft_jewelry(character, 'life_ring', quantity)

        if sell:
            _ScenarioHelpers._sell_item(character, 'life_ring', quantity)

    @classmethod
    def _craft_weapon(cls, character, item_code='', quantity=1):
        ws = cls._get_location_for_content(character, content_code='weaponcrafting')

        if ws:
            character.move(*ws[:2])

        character.crafting(item_code, quantity)

    @classmethod
    def _craft_gear(cls, character, item_code='', quantity=1):
        ws = cls._get_location_for_content(character, content_code='gearcrafting')

        if ws:
            character.move(*ws[:2])

        character.crafting(item_code, quantity)

    @classmethod
    def _craft_jewelry(cls, character, item_code='', quantity=1):
        ws = cls._get_location_for_content(character, content_code='jewelrycrafting')

        if ws:
            character.move(*ws[:2])

        character.crafting(item_code, quantity)


class CraftConsumablesScenarios(_ScenarioHelpers):
    """Collection of food/cooking crafting scenarios."""

    CATEGORY = 'Craft consumables'

    @classmethod
    def get_scenarios(cls, character):
        scenarios_list = [
            cls.craft_cooked_gudgeon,
            cls.craft_cooked_chicken,
        ]

        if character.cooking_level >= 5:
            scenarios_list.extend([
                cls.craft_cooked_beef,
            ])

        if character.cooking_level >= 10:
            scenarios_list.extend([
                cls.craft_cheese,
                cls.craft_fried_eggs,
                cls.craft_mushroom_soup,
                cls.craft_beef_stew,
            ])

            if character.fishing_level >= 10:
                scenarios_list.extend([
                    cls.craft_cooked_shrimp,
                ])

        if character.cooking_level >= 15:
            scenarios_list.extend([
                cls.craft_cooked_wolf_meat,
            ])

        if character.cooking_level >= 20 and character.fishing_level >= 20:
            scenarios_list.extend([
                cls.craft_cooked_trout,
            ])

        if character.cooking_level >= 30 and character.fishing_level >= 30:
            scenarios_list.extend([
                cls.craft_cooked_bass,
            ])

        return scenarios_list

    @classmethod
    def craft_cooked_gudgeon(cls, character, quantity=1, sell=False):
        GatherScenarios.gather_resource_from_location(character, 'gudgeon', quantity)
        cls._craft_food(character, 'cooked_gudgeon', quantity)

        if sell:
            _ScenarioHelpers._sell_item(character, 'cooked_gudgeon', quantity)

    @classmethod
    def craft_cooked_chicken(cls, character, quantity=1, sell=False):
        GatherScenarios.gather_resource_from_monsters(character, 'raw_chicken', quantity)
        cls._craft_food(character, 'cooked_chicken', quantity)

        if sell:
            _ScenarioHelpers._sell_item(character, 'cooked_chicken', quantity)

    @classmethod
    def craft_cooked_beef(cls, character, quantity=1, sell=False):
        GatherScenarios.gather_resource_from_monsters(character, 'raw_beef', quantity)
        cls._craft_food(character, 'cooked_beef', quantity)

        if sell:
            _ScenarioHelpers._sell_item(character, 'cooked_beef', quantity)

    @classmethod
    def craft_cooked_shrimp(cls, character, quantity=1, sell=False):
        GatherScenarios.gather_resource_from_location(character, 'shrimp', quantity)
        cls._craft_food(character, 'cooked_shrimp', quantity)

        if sell:
            _ScenarioHelpers._sell_item(character, 'cooked_shrimp', quantity)

    @classmethod
    def craft_cheese(cls, character, quantity=1, sell=False):
        GatherScenarios.gather_resource_from_monsters(character, 'milk_bucket', 3 * quantity)
        cls._craft_food(character, 'cheese', quantity)

        if sell:
            _ScenarioHelpers._sell_item(character, 'cheese', quantity)

    @classmethod
    def craft_fried_eggs(cls, character, quantity=1, sell=False):
        GatherScenarios.gather_resource_from_monsters(character, 'egg', 5 * quantity)
        cls._craft_food(character, 'fried_eggs', quantity)

        if sell:
            _ScenarioHelpers._sell_item(character, 'fried_eggs', quantity)

    @classmethod
    def craft_mushroom_soup(cls, character, quantity=1, sell=False):
        CraftResourcesScenarios.craft_ash_planks(character, quantity)
        GatherScenarios.gather_resource_from_monsters(character, 'milk_bucket', quantity)
        GatherScenarios.gather_resource_from_monsters(character, 'mushroom', quantity)
        cls._craft_food(character, 'mushroom_soup', quantity)

        if sell:
            _ScenarioHelpers._sell_item(character, 'mushroom_soup', quantity)

    @classmethod
    def craft_beef_stew(cls, character, quantity=1, sell=False):
        CraftResourcesScenarios.craft_ash_planks(character, quantity)
        GatherScenarios.gather_resource_from_monsters(character, 'raw_beef', 3 * quantity)
        cls._craft_food(character, 'beef_stew', quantity)

        if sell:
            _ScenarioHelpers._sell_item(character, 'beef_stew', quantity)

    @classmethod
    def craft_cooked_wolf_meat(cls, character, quantity=1, sell=False):
        GatherScenarios.gather_resource_from_monsters(character, 'raw_wolf_meat', quantity)
        cls._craft_food(character, 'cooked_wolf_meat', quantity)

        if sell:
            _ScenarioHelpers._sell_item(character, 'cooked_wolf_meat', quantity)

    @classmethod
    def craft_cooked_trout(cls, character, quantity=1, sell=False):
        GatherScenarios.gather_resource_from_location(character, 'trout', quantity)
        cls._craft_food(character, 'cooked_trout', quantity)

        if sell:
            _ScenarioHelpers._sell_item(character, 'cooked_trout', quantity)

    @classmethod
    def craft_cooked_bass(cls, character, quantity=1, sell=False):
        GatherScenarios.gather_resource_from_location(character, 'bass', quantity)
        cls._craft_food(character, 'cooked_bass', quantity)

        if sell:
            _ScenarioHelpers._sell_item(character, 'cooked_bass', quantity)

    @classmethod
    def _craft_food(cls, character, item_code='', quantity=1):
        ws = cls._get_location_for_content(character, content_code='cooking')

        if ws:
            character.move(*ws[:2])

        character.crafting(item_code, quantity)


class RecyclingScenarios(_ScenarioHelpers):
    """Collection of recycling scenarios."""

    CATEGORY = 'Recycling'

    @classmethod
    def get_scenarios(cls, character):
        return [
            cls.recycle_all_unequipped,
        ]

    @classmethod
    def recycle_all_unequipped(cls, character, max_slots=999):
        ws = _ScenarioHelpers._get_location_for_content(character, content_code='weaponcrafting') \
            or _ScenarioHelpers._get_location_for_content(character, content_type=MapTypesEnum.WORKSHOP.value)

        if ws:
            _ScenarioHelpers._recycle_slots(character, ws, max_slots)
        else:
            print('Can\'t locate any workshop.')

    @classmethod
    def _recycle_slots(cls, character, ws, max_slots):
        character.move(*ws[:2])

        count = 0

        for slot_name in _ScenarioHelpers.EQUIPMENT_SLOTS:
            if count >= max_slots:
                break

            code = getattr(character, slot_name, None)

            if not code:
                continue

            character.unequip(slot_name)
            character.recycling(code, 1)
            count += 1


class OtherScenarios(_ScenarioHelpers):
    """Collection of utility scenarios (tasks, bank, deposit)."""

    CATEGORY = 'Other scenarios'

    @classmethod
    def get_scenarios(cls, character):
        return [
            cls.do_quest_from_tasks_master,
            cls.deposit_all_to_bank,
            cls.deposit_gold_to_bank,
        ]

    @classmethod
    def do_quest_from_tasks_master(cls, character, quantity=1):
        location = _ScenarioHelpers._get_location_for_content(character, content_type=MapTypesEnum.TASKS_MASTER.value)

        if location:
            cls._run_task_master_quests(character, location, quantity)
        else:
            print('Can\'t locate Tasks Master.')

    @classmethod
    def _run_task_master_quests(cls, character, location, quantity):
        tasks_x, tasks_y, _ = location

        for _ in range(quantity):
            if not character.task:
                character.move(tasks_x, tasks_y)
                character.get_task()

            if character.task_type == TaskTypeEnum.MONSTERS.value:
                monster_location = _ScenarioHelpers._get_location_for_content(character, character.task)

                if monster_location:
                    cls._run_monster_task(character, tasks_x, tasks_y, monster_location)
            else:
                print('Can\'t process this type of task yet.')
                break

    @classmethod
    def _run_monster_task(cls, character, tasks_x, tasks_y, monster_location):
        while character.task_progress < character.task_total:
            _ScenarioHelpers._ensure_at(character, *monster_location)
            character.fight()

        character.move(tasks_x, tasks_y)
        character.complete_task()

    @classmethod
    def deposit_all_to_bank(cls, character):
        bank = _ScenarioHelpers._get_location_for_content(character, content_type=MapTypesEnum.BANK.value)

        if bank:
            cls._deposit_inventory_to_bank(character, bank)
        else:
            print('Can\'t locate bank.')

    @classmethod
    def _deposit_inventory_to_bank(cls, character, bank):
        character.move(*bank[:2])

        for slot in list(character.inventory or []):
            code = slot.get('code')
            qty = slot.get('quantity', 1)

            if code and qty:
                character.deposit_item(code, qty)

    @classmethod
    def deposit_gold_to_bank(cls, character, quantity=None):
        bank = _ScenarioHelpers._get_location_for_content(character, content_type=MapTypesEnum.BANK.value)

        if bank:
            cls._deposit_gold(character, bank, quantity)
        else:
            print('Can\'t locate bank.')

    @classmethod
    def _deposit_gold(cls, character, bank, quantity):
        character.move(*bank[:2])

        if quantity is None:
            quantity = character.gold

        character.deposit_gold(quantity)


class ScenariosStorage(BaseClient):
    """Aggregator that binds the active character to each scenario.

    Holds ``self.character`` and exposes ``scenarios_category_map`` whose
    values are zero-argument callables returning a list of
    :func:`functools.partial`-bound scenarios from the collection classes.
    """

    SCENARIO_COLLECTIONS = (
        ItemsScenarios,
        RecyclingScenarios,
        OtherScenarios,
    )

    def __init__(self, character):
        super().__init__()

        self.character = character

        self.scenarios_category_map = {
            collection.CATEGORY: self._build_category_factory(collection)
            for collection in self.SCENARIO_COLLECTIONS
        }

    def _build_category_factory(self, collection):
        def factory():
            return [
                functools.partial(method, self.character)
                for method in collection.get_scenarios(self.character)
            ]

        return factory
