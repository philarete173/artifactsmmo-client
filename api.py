import configparser
import inspect
import random
import re
import sys
from time import sleep

from base import BaseClient
from enums import (
    CharacterSexEnum,
    ActionTypeEnum,
    EquipmentSlotsEnum,
    MapTypesEnum,
    ItemTypesEnum,
)
from scripts import (
    ScenariosStorage,
)


class BaseGameClient(BaseClient):
    """Basic client for sending requests with authorization token."""

    def __init__(self):
        super().__init__()

        self.config = self._get_config()

        self.base_headers.update({
            "Authorization": f"Bearer {self.config.get('General', 'TOKEN')}"
        })

    def _get_config(self):
        """Open config file."""

        config = configparser.ConfigParser()
        config.read('config.ini')

        return config


class GameClient(BaseGameClient):
    """Client for interacting with the game world."""

    def __init__(self):
        super().__init__()

        self.main_menu_map = {
            ActionTypeEnum.MOVE.value: self.character_movement,
            ActionTypeEnum.FIGHT.value: self.character_fight,
            ActionTypeEnum.GATHERING.value: self.character_gathering,
            ActionTypeEnum.CRAFTING.value: self.character_crafting,
            ActionTypeEnum.EQUIP.value: self.character_equip,
            ActionTypeEnum.UNEQUIP.value: self.character_unequip,
            ActionTypeEnum.NEW_TASK.value: self.character_get_new_task,
            ActionTypeEnum.COMPLETE_TASK.value: self.character_complete_task,
            ActionTypeEnum.EXCHANGE_TASK.value: self.character_exchange_task_coins,
            ActionTypeEnum.BUY_ITEM.value: self.character_buy_item,
            ActionTypeEnum.SELL_ITEM.value: self.character_sell_item,
            ActionTypeEnum.DEPOSIT_BANK.value: self.character_deposit_item_to_bank,
            ActionTypeEnum.DEPOSIT_BANK_GOLD.value: self.character_deposit_gold_to_bank,
            ActionTypeEnum.WITHDRAW_BANK.value: self.character_withdraw_item_from_bank,
            ActionTypeEnum.WITHDRAW_GOLD.value: self.character_withdraw_gold_from_bank,
            ActionTypeEnum.USE_SCENARIO.value: self.use_scenario,
        }

        self.check_server_status()

        self.character = self.select_character()
        self.scenarios_storage = ScenariosStorage(self.character)

    def main_loop(self):
        """User interaction in an infinite loop."""

        while True:
            current_location_data = self.get_location_data(self.character.x, self.character.y)
            location_type = current_location_data.get('content', {}).get('type', None)

            available_actions, available_actions_str = self._prepare_actions_menu_data(
                ActionTypeEnum.LOCATION_ACTIONS_MAP.value.get(location_type),
            )
            try:
                current_action_idx = int(input(
                    'What do you want to do?\n'
                    f'{available_actions_str}\n'
                    'Please type a number: '
                ))
                current_action = available_actions[current_action_idx]
            except ValueError:
                print('Invalid input. Please try again.')
                continue

            current_action_method = self.main_menu_map.get(current_action)

            if current_action_method:
                try:
                    current_action_method()
                except Exception as error:
                    print(f'Something went wrong. Error: {error}.  Plaease try again.')
            else:
                print('This is not a valid action!')

            print('')

    def select_character(self):
        """Selecting a character from the list on the account."""

        characters = self.get_characters_list()

        characters_map, characters_map_string = self._prepare_actions_menu_data(
            [character["name"] for character in characters],
        )
        print(f'Characters on account: {", ".join(characters_map.values())}')

        character_selected = False
        while not character_selected:
            character_select = input(
                'Which character do you want to choose?\n'
                f'{characters_map_string}\n'
                'Please type a number: '
            )
            if not int(character_select) in characters_map:
                print('Failed to select a character, try again.')
            else:
                character_selected = True

        selected_character_name = characters_map[int(character_select)]
        selected_character = Character(selected_character_name)
        print(f'Selected character {selected_character_name}.')

        return selected_character

    def check_server_status(self):
        """Checking the status of the server. If unavailable, the process will be terminated."""

        status_request = self._get()

        if status_request.status_code == 200:
            print(f'Server status is "{status_request.json()["data"]["status"]}".')
            for announcement in status_request.json()['data']['announcements']:
                print(announcement['message'])
        else:
            sys.exit('Can\'t reach the server. Please try again later.')

    def get_characters_list(self):
        """Getting a list of characters. If there are no characters, it will create one."""

        url = '/my/characters'

        characters_list = self._get(url=url)

        if characters_list.status_code == 404:
            print(f'{characters_list.json()["error"]["message"]} You have to create a character first.')
            character_created = self.create_new_character()

            if character_created:
                characters_list = self._get(url=url)

        if characters_list.status_code == 200:
            result = characters_list.json()['data']
        else:
            result = []

        return result

    def create_new_character(self):
        """Creating a new character."""

        url = '/characters/create'

        name_correct = False
        while not name_correct:
            character_name = input('What will the new character\'s name be?: ')
            if not re.match(r'^[a-zA-Z0-9_-]{3,12}$', character_name):
                print('That name doesn\'t fit, try another')
            else:
                name_correct = True

        if name_correct:
            character_sex = ''
            while character_sex not in ['m', 'f', 'r']:
                character_sex = input('What sex will the character be? male(m)/female(f)/random(r): ')

            print(f'The new character\'s name is {character_name}, creating...')
            create_request = self._post(
                url=url,
                data={
                    'name': character_name,
                    'skin': random.choice(CharacterSexEnum.SEX_SKIN_MAP.value[character_sex]),
                },
            )

            character_created = create_request.status_code == 200

            if create_request.status_code == 200:
                print(f'Character {character_name} succesfully created.')
            else:
                print(create_request.json()['error']['message'])

            return character_created

    def _prepare_actions_menu_data(self, iterable):
        """"""
        items_map = {idx: item for idx, item in enumerate(iterable, 1)}
        items_map_str = "\n".join(f"{idx} - {name.capitalize().replace('_', ' ')}" for idx, name in items_map.items())

        return items_map, items_map_str

    def character_movement(self):
        locations_type_map, locations_type_str = self._prepare_actions_menu_data(
            [element.value for element in MapTypesEnum],
        )
        location_type_idx = int(input(
            'What type of location you want to move to?\n'
            f'{locations_type_str}\n'
            'Please type a number: '
        ))
        chosen_location_type = locations_type_map[location_type_idx]
        chosen_location_type_maps_list = self.get_maps_data(chosen_location_type)
        chosen_location_type_maps, chosen_location_type_str = self._prepare_actions_menu_data(
            sorted({map_data.get('content', {}).get('code', '') for map_data in chosen_location_type_maps_list})
        )
        if len(chosen_location_type_maps) > 1:
            chosen_location_idx = int(input(
                'Where do you want to move?\n'
                f'{chosen_location_type_str}\n'
                'Please type a number: '
            ))

        else:
            chosen_location_idx = 1

        chosen_location = next(
            filter(
                lambda map_data: map_data['content']['code'] == chosen_location_type_maps[chosen_location_idx],
                chosen_location_type_maps_list,
            )
        )

        self.character.move(chosen_location['x'], chosen_location['y'])

    def character_fight(self):
        count = input('How many times to fight?: ')
        for _ in range(int(count)):
            self.character.fight()

    def character_gathering(self):
        count = input('How many times to gather?: ')
        for _ in range(int(count)):
            self.character.gathering()

    def character_crafting(self):
        location_data = self.get_location_data(self.character.x, self.character.y)

        if location_data.get('content') and location_data['content']['type'] == MapTypesEnum.WORKSHOP.value:
            workshop_type = location_data['content']['code']
            items_list = self.get_crafting_list(
                craft_skill=workshop_type,
                skill_level=getattr(self.character, f'{workshop_type}_level', 1),
            )
            items_map, items_map_str = self._prepare_actions_menu_data(
                [item['name'] for item in items_list],
            )
            craft_idx = int(input(
                'What item do you want to craft?\n'
                f'{items_map_str}\n'
                'Please type a number: '
            ))

            craft_name = next(
                filter(
                    lambda item: item['name'] == items_map[craft_idx],
                    items_list,
                ),
                {},
            ).get(
                'code',
                '',
            )
            quantity = int(input('Нow many do you want to create?: '))

            self.character.crafting(craft_name, quantity)
        else:
            print('You can\'t craft anything at this location.')

    def character_equip(self):
        inventory_map, inventory_map_str = self._prepare_actions_menu_data(
            [item['code'] for item in self.character.inventory if item['code']]
        )
        chosen_item_idx = int(input(
            'What item do you want to equip?\n'
            f'{inventory_map_str}\n'
            'Please type a number: '
        ))

        item_data = self.get_item_by_code(inventory_map[chosen_item_idx])
        if item_data['type'] in ItemTypesEnum.EQUIP_TYPES.value and item_data['level'] <= self.character.level:
            equipment_slot = next(
                filter(
                    lambda item: item_data['type'] == item.value or item.value.startswith(item_data['type']),
                    EquipmentSlotsEnum,
                )
            )
            if equipment_slot:
                self.character.equip(item_data['code'], equipment_slot.value)

        else:
            print('You can\'t equip this item.')

    def character_unequip(self):
        slots_map, slots_map_str = self._prepare_actions_menu_data([action.value for action in EquipmentSlotsEnum])
        slot_idx = int(input(
            'Which slot do you want to unequip?\n'
            f'{slots_map_str}\n'
            'Please type a number: '
        ))
        slot = slots_map[slot_idx]

        self.character.unequip(slot)

    def character_get_new_task(self):
        self.character.get_task()

    def character_complete_task(self):
        self.character.complete_task()

    def character_exchange_task_coins(self):
        self.character.exchange_task_coins()

    def character_buy_item(self):
        item_name = input('What item do you want to buy?: ')
        quantity = int(input('Нow many do you want to buy?: '))

        self.character.buy_item(item_name, quantity)

    def character_sell_item(self):
        items_map, items_map_str = self._prepare_actions_menu_data(
            [item['code'] for item in self.character.inventory if item['quantity']]
        )
        item_idx = int(input(
            'What item do you want to sell?\n'
            f'{items_map_str}\n'
            'Please type a number: '
        ))
        item_name = items_map[item_idx]
        inventory_quantity = next(
            filter(
                lambda item: item['code'] == item_name,
                self.character.inventory,
            ),
            {},
        ).get('quantity', 0)
        quantity = int(input(f'Нow many do you want to sell (You have {inventory_quantity})?: '))

        self.character.sell_item(item_name, quantity)

    def character_deposit_item_to_bank(self):
        inventory_map, inventory_map_str = self._prepare_actions_menu_data(
            [item['code'] for item in self.character.inventory if item['code']]
        )
        chosen_item_idx = int(input(
            'What item do you want to deposit?\n'
            f'{inventory_map_str}\n'
            'Please type a number: '
        ))

        item_code = inventory_map[chosen_item_idx]
        inventory_quantity = next(
            filter(
                lambda item: item['code'] == item_code,
                self.character.inventory,
            ),
            {},
        ).get('quantity', 0)
        quantity = int(input(f'Нow many do you want to deposit (You have {inventory_quantity})?: '))

        self.character.deposit_item(item_code, quantity)

    def character_withdraw_item_from_bank(self):
        bank_items_data = self.get_bank_items()
        bank_items_map, bank_items_map_str = self._prepare_actions_menu_data(
            [item['code'] for item in bank_items_data]
        )

        chosen_item_idx = int(input(
            'What item do you want to withdraw?\n'
            f'{bank_items_map_str}\n'
            'Please type a number: '
        ))

        item_code = bank_items_map[chosen_item_idx]
        inventory_quantity = next(
            filter(
                lambda item: item['code'] == item_code,
                bank_items_data,
            ),
            {},
        ).get('quantity', 0)
        quantity = int(input(f'Нow many do you want to withdraw (The bank holds {inventory_quantity})?: '))

        self.character.withdraw_item(item_code, quantity)

    def character_deposit_gold_to_bank(self):
        quantity = int(input(f'How many gold do you want to deposit (You have {self.character.gold})?: '))

        self.character.deposit_gold(quantity)

    def character_withdraw_gold_from_bank(self):
        quantity = int(input(f'How many gold do you want to withdraw (The bank holds {self.get_bank_gold()})?: '))

        self.character.withdraw_gold(quantity)

    def use_scenario(self):

        scenarios_category_map, scenarios_category_str = self._prepare_actions_menu_data(
            self.scenarios_storage.scenarios_category_map.keys(),
        )

        scenario_category_idx_select = int(input(
            'Which type of scenario do you want to launch?\n'
            f'{scenarios_category_str}\n'
            'Please type a number: '
        ))
        category_scenarios = self.scenarios_storage.scenarios_category_map[scenarios_category_map[scenario_category_idx_select]]()
        scenarios_map, scenarios_map_str = self._prepare_actions_menu_data([scenario.__name__ for scenario in category_scenarios])

        scenario_idx_select = int(input(
            'Which scenario do you want to launch?\n'
            f'{scenarios_map_str}\n'
            'Please type a number: '
        ))

        selected_scenario = next(
            filter(
                lambda scenario: scenario.__name__ == scenarios_map[scenario_idx_select],
                category_scenarios,
            )
        )
        params = {}
        print('Specify the values of the scenario startup parameters')
        for name, parameter in dict(inspect.signature(selected_scenario).parameters).items():
            parameter_type = type(parameter.default)
            params[name] = parameter_type(input(f'{name} (default: {parameter.default}): '))

        if bool(params.get('sell', '')):
            repeats = int(input('How many times to repeat the scenario?: '))
        else:
            repeats = 1

        for _ in range(repeats):
            selected_scenario(**params)

    def get_location_data(self, x=0, y=0):
        """Get data about location."""

        location_data = self._get(
            url=f'/maps/{x}/{y}',
        )

        if location_data.status_code == 200:
            result = location_data.json().get('data', {})
        else:
            print(location_data.json()['error']['message'])
            result = {}

        return result

    def get_maps_data(self, map_type=''):
        """Get list of maps by content type."""

        maps_data = self._get(
            url='/maps',
            data={
                'content_type': map_type,
            }
        )

        if maps_data.status_code == 200:
            result = maps_data.json().get('data', [])
            if total_pages := maps_data.json().get('pages', 1) > 1:
                for page in range(2, total_pages + 1):
                    maps_data = self._get(
                        url='/maps',
                        data={
                            'content_type': map_type,
                            'page': page,
                        }
                    )
                    result.extend(maps_data.json().get('data', []))
        else:
            print(maps_data.json()['error']['message'])
            result = []

        return result

    def get_crafting_list(self, craft_skill='', skill_level=1):
        """Get items that you can craft with your current skill level."""

        items_data = self._get(
            url='/items',
            data={
                'craft_skill': craft_skill,
                'max_level': skill_level,
            }
        )

        if items_data.status_code == 200:
            result = items_data.json().get('data', [])
            total_pages = items_data.json().get('pages', 1)
            if total_pages > 1:
                for page in range(2, total_pages + 1):
                    items_data = self._get(
                        url='/maps',
                        data={
                            'craft_skill': craft_skill,
                            'max_level': skill_level,
                            'page': page,
                        }
                    )
                    result.extend(items_data.json().get('data', []))
        else:
            print(items_data.json()['error']['message'])
            result = []

        return result

    def get_items_by_type(self, item_type=''):
        """Get list of items by type."""

        items_data = self._get(
            url='/items',
            data={
                'type': item_type,
            }
        )

        if items_data.status_code == 200:
            result = items_data.json().get('data', [])
            total_pages = items_data.json().get('pages', 1)
            if total_pages > 1:
                for page in range(2, total_pages + 1):
                    items_data = self._get(
                        url='/items',
                        data={
                            'type': item_type,
                            'page': page,
                        }
                    )
                    result.extend(items_data.json().get('data', []))
        else:
            print(items_data.json()['error']['message'])
            result = []

        return result

    def get_item_by_code(self, item_code=''):
        """Get item by it code."""

        item_data = self._get(
            url=f'/items/{item_code}'
        )

        if item_data.status_code == 200:
            result = item_data.json().get('data', {}).get('item', {})

        else:
            result = {}

        return result

    def get_bank_items(self):
        """Get bank items."""

        bank_items_data = self._get(
            url='/my/bank/items',
        )

        if bank_items_data.status_code == 200:
            result = bank_items_data.json().get('data', [])
            total_pages = bank_items_data.json().get('pages', 1)
            if total_pages > 1:
                for page in range(2, total_pages + 1):
                    bank_items_data = self._get(
                        url='/my/bank/items',
                        data={
                            'page': page,
                        }
                    )
                    result.extend(bank_items_data.json().get('data', []))
        else:
            print(bank_items_data.json()['error']['message'])
            result = []

        return result

    def get_bank_gold(self):
        """Get bank gold quantity."""

        bank_gold_data = self._get(
            url='/my/bank/gold',
        )

        if bank_gold_data.status_code == 200:
            gold_quantity = bank_gold_data.json().get('data', {}).get('quantity', 0)
        else:
            gold_quantity = 0

        return gold_quantity


class Character(BaseGameClient):
    """Client for character interaction."""

    def __init__(self, name) -> None:
        super().__init__()

        self.name = name
        self.base_character_action_url = f'/my/{self.name}/action'
        self._get_character_info()

    def _get_character_info(self):
        """Getting all character data and storing in instance."""

        character_info_request = self._get(
            url=f'/characters/{self.name}'
        )

        if character_info_request.status_code == 200:
            for key, value in character_info_request.json()['data'].items():
                setattr(self, key, value)

    def _get_last_action(self):
        """Getting info about last action from character log."""

        last_action_data = self._get(
            url=f'/my/logs',
            data={
                'page': 1,
                'size': 1,
            })

        if last_action_data.status_code == 200:
            print(last_action_data.json()['data'][0]['description'])
        elif error_block := last_action_data.json().get('error'):
            print(f'Can\'t get last action. {error_block["message"]}.')

        self._get_character_info()

    def _do_action(self, action_name='', action_data=None):
        """General method for sending an action request."""

        if action_data is None:
            action_data = {}

        action_request = self._post(
            url=f'{self.base_character_action_url}/{action_name}',
            data=action_data,
        )

        if action_request.status_code == 200:
            print(
                f'Performing action {action_request.json()["data"]["cooldown"]["reason"]}. '
                f'It\'ll take {action_request.json()["data"]["cooldown"]["total_seconds"]} seconds.'
            )
            for i in range(action_request.json()["data"]["cooldown"]["total_seconds"], 0, -1):
                print(f'Waiting {i} seconds...', end=' \r')
                sleep(1)

            self._get_last_action()
        elif error_block := action_request.json().get('error'):
            print(f'Can\'t perform action. {error_block["message"]}')

    def move(self, x=0, y=0):
        """Move the character to a given map cell."""

        self._do_action(
            action_name=ActionTypeEnum.MOVE.value,
            action_data={
                'x': x,
                'y': y,
            }
        )

    def fight(self):
        """Start fight."""

        self._do_action(
            action_name=ActionTypeEnum.FIGHT.value,
        )

    def gathering(self):
        """Start gathering resources."""

        self._do_action(
            action_name=ActionTypeEnum.GATHERING.value,
        )

    def crafting(self, item_name='', quantity=1):
        """Start crafting items."""

        self._do_action(
            action_name=ActionTypeEnum.CRAFTING.value,
            action_data={
                'code': item_name,
                'quantity': quantity,
            }
        )

    def equip(self, item_name='', slot=''):
        """Equip item."""

        self._do_action(
            action_name=ActionTypeEnum.EQUIP.value,
            action_data={
                'code': item_name,
                'slot': slot,
            }
        )

    def unequip(self, slot=''):
        """Unequip slot."""

        self._do_action(
            action_name=ActionTypeEnum.UNEQUIP.value,
            action_data={
                'slot': slot,
            }
        )

    def get_task(self):
        """Get new quest."""

        self._do_action(
            action_name='task/new',
        )

    def complete_task(self):
        """Complete the current quest."""

        self._do_action(
            action_name='task/complete',
        )

    def exchange_task_coins(self):
        """Exchange task coins."""

        self._do_action(
            action_name='task/exchange'
        )

    def deposit_item(self, item_code='', quantity=0):
        """Deposit item to bank."""

        self._do_action(
            action_name='bank/deposit',
            action_data={
                'code': item_code,
                'quantity': quantity,
            }
        )

    def deposit_gold(self, quantity=0):
        """Deposit item to bank."""

        self._do_action(
            action_name='bank/deposit/gold',
            action_data={
                'quantity': quantity,
            }
        )

    def withdraw_item(self, item_code='', quantity=0):
        """Withdraw item from bank."""

        self._do_action(
            action_name='bank/withdraw',
            action_data={
                'code': item_code,
                'quantity': quantity,
            }
        )

    def withdraw_gold(self, quantity=0):
        """Withdraw item from bank."""

        self._do_action(
            action_name='bank/withdraw/gold',
            action_data={
                'quantity': quantity,
            }
        )

    def _get_item_data(self, item_name=''):
        """Get item data."""

        item_data = self._get(
            url=f'/items/{item_name}',
        )

        if item_data.status_code == 200:
            result = item_data.json()
        else:
            result = {}

        return result

    def buy_item(self, item_name='', quantity=1):
        """Buy an item from General Exchange."""

        item_data = self._get_item_data(item_name)
        current_price = item_data.get('data', {}).get('ge', {}).get('buy_price', 0)

        if current_price:
            self._do_action(
                action_name='ge/buy',
                action_data={
                    'code': item_name,
                    'quantity': quantity,
                    'price': current_price,
                }
            )

    def sell_item(self, item_name='', quantity=1):
        """Sell an item to General Exchange."""

        for part_quantity in [50 for _ in range(quantity // 50)] + [quantity % 50]:
            item_data = self._get_item_data(item_name)
            current_price = item_data.get('data', {}).get('ge', {}).get('sell_price', 0)

            if current_price:
                self._do_action(
                    action_name='ge/sell',
                    action_data={
                        'code': item_name,
                        'quantity': part_quantity,
                        'price': current_price,
                    }
                )
