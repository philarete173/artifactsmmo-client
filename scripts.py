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
        ge = cls._get_location_for_content(character, content_type=MapTypesEnum.GRAND_EXCHANGE)

        if ge:
            character.move(*ge[:2])

        character.ge_create_sell_order(item_name, quantity, price=0)

    @classmethod
    def _get_workshop_for_item_code(cls, character, item_code):
        response = character._get(url=f'/items/{item_code}')
        item = response.json().get('data', {}) if response.status_code == 200 else {}
        craft = item.get('craft') or {}
        skill = craft.get('skill', '')
        if skill:
            workshop = cls._get_location_for_content(character, content_code=skill)
            if workshop:
                return workshop
        fallback = cls._get_location_for_content(character, content_type=MapTypesEnum.WORKSHOP)
        return fallback

    @classmethod
    def _handle_post_craft(cls, character, item_code='', quantity=1):
        choice = input(
            f'Crafted {item_code} x{quantity}. What to do?\n'
            '[s]ell, [r]ecycle, [n]othing: '
        ).strip().lower()

        if choice == 's':
            cls._sell_item(character, item_code, quantity)
        elif choice == 'r':
            ws = cls._get_workshop_for_item_code(character, item_code)
            if ws:
                if character.x != ws[0] or character.y != ws[1]:
                    character.move(*ws[:2])
                character.recycling(item_code, quantity)
            else:
                print('No workshop found for recycling.')


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
        location = _ScenarioHelpers._get_location_for_content(character, content_type=MapTypesEnum.TASKS_MASTER)

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

            if character.task_type == TaskTypeEnum.MONSTERS:
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
        bank = _ScenarioHelpers._get_location_for_content(character, content_type=MapTypesEnum.BANK)

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
        bank = _ScenarioHelpers._get_location_for_content(character, content_type=MapTypesEnum.BANK)

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
        OtherScenarios,
    )

    def __init__(self, character):
        super().__init__()

        self.character = character

        self.scenarios_category_map = {
            collection.CATEGORY: self._build_category_factory(collection)
            for collection in self.SCENARIO_COLLECTIONS
        }

        for method in OtherScenarios.get_scenarios(self.character):
            name = method.__name__.replace('_', ' ').capitalize()
            self.scenarios_category_map[name] = self._build_single_factory(method)

    def _build_category_factory(self, collection):
        def factory():
            return [
                functools.partial(method, self.character)
                for method in collection.get_scenarios(self.character)
            ]

        return factory

    def _build_single_factory(self, method):
        def factory():
            return [functools.partial(method, self.character)]

        return factory
