import re
import sys

from base.character import Character
from base.enums import (
    ActionTypeEnum,
    CharacterSkinsEnum,
    EquipmentSlotsEnum,
    GEOrderTypeEnum,
    ImageCategoryEnum,
    ItemTypesEnum,
    MapLayerEnum,
    MapTypesEnum,
)
from base.client import GameClient
from scripts import ScenariosStorage


class ConsoleGameClient(GameClient):
    """Console front-end for the ArtifactsMMO client.

    Adds terminal menu loops, user prompts, and all interactive
    character action methods on top of the shared ArtifactsClient API.
    """

    def __init__(self, display=None):
        from console_client.api import ConsoleDisplay
        super().__init__(display=display or ConsoleDisplay())

    # ── Menu loops ──────────────────────────────────────────────

    def main_loop(self):
        """Top-level menu: account-level actions plus character selection."""

        self.show_current_season()

        while True:
            actions_map, actions_str = self.display.prepare_menu(ActionTypeEnum.ACCOUNT_ACTIONS)
            idx = self.display.prompt_int(
                'What do you want to do at the account level?\n'
                f'{actions_str}\n'
                'Please type a number: '
            )
            if idx is None or idx not in actions_map:
                continue

            current_action = actions_map[idx]

            if current_action == ActionTypeEnum.SELECT_CHARACTER:
                self._choose_character()
                if self.character is not None:
                    self.character_action_loop()
                continue

            self._dispatch_account_action(current_action)

            self.display.print('')

    def _dispatch_account_action(self, current_action):
        method = self.account_menu_map.get(current_action)

        if method is None:
            self.display.print('This is not a valid action!')
            return

        try:
            method()
        except Exception as error:
            self.display.print(f'Something went wrong. Error: {error}. Please try again.')

    def character_action_loop(self):
        """Per-character action menu with 3 top-level categories."""

        while True:
            current_location_data = self.get_location_data(
                self.character.layer, self.character.x, self.character.y,
            )
            self.display.show_location(current_location_data)

            choice = self.display.prompt_int(
                'What do you want to do?\n'
                '1 - Basic actions\n'
                '2 - Advanced actions\n'
                '3 - Character actions\n'
                'Please type a number: '
            )
            if choice is None:
                continue

            if choice == 1:
                self._handle_basic_actions(current_location_data)
            elif choice == 2:
                self._handle_advanced_actions()
            elif choice == 3:
                self._handle_character_actions()

            self.display.print('')

    def _handle_basic_actions(self, location_data):
        location_type = ((location_data.get('interactions') or {}).get('content') or {}).get('type', None)
        actions = list(ActionTypeEnum.LOCATION_ACTIONS_MAP.get(location_type, []))

        if (location_data.get('interactions') or {}).get('transition'):
            actions.append(ActionTypeEnum.TRANSITION)

        actions_map, actions_str = self.display.prepare_menu(actions)
        idx = self.display.prompt_int(
            'Basic actions:\n'
            f'{actions_str}\n'
            'Please type a number: '
        )
        if idx is None or idx not in actions_map:
            return

        current_action = actions_map[idx]
        method = self.main_menu_map.get(current_action)
        if method is None:
            self.display.print('This is not a valid action!')
        else:
            try:
                method()
            except Exception as error:
                self.display.print(f'Something went wrong. Error: {error}. Please try again.')

    def _handle_advanced_actions(self):
        actions_map, actions_str = self.display.prepare_menu(ActionTypeEnum.ADVANCED_ACTIONS)
        idx = self.display.prompt_int(
            'Advanced actions:\n'
            f'{actions_str}\n'
            'Please type a number: '
        )
        if idx is None or idx not in actions_map:
            return

        current_action = actions_map[idx]
        method = self.main_menu_map.get(current_action)
        if method is None:
            self.display.print('This is not a valid action!')
        else:
            try:
                method()
            except Exception as error:
                self.display.print(f'Something went wrong. Error: {error}. Please try again.')

    def _handle_character_actions(self):
        actions_map, actions_str = self.display.prepare_menu(ActionTypeEnum.CHARACTER_ACTIONS)
        idx = self.display.prompt_int(
            'Character actions:\n'
            f'{actions_str}\n'
            'Please type a number: '
        )
        if idx is None or idx not in actions_map:
            return

        current_action = actions_map[idx]
        if current_action == ActionTypeEnum.STATS:
            self._show_character_stats()
        elif current_action == ActionTypeEnum.SKILLS:
            self._show_character_skills()
        elif current_action == ActionTypeEnum.INVENTORY:
            self._show_character_inventory()
        elif current_action == ActionTypeEnum.EQUIPMENT:
            self._show_character_equipment()
        elif current_action == ActionTypeEnum.CHANGE_SKIN:
            self.character_change_skin()

    # ── Display helpers ─────────────────────────────────────────

    def _show_character_stats(self):
        self.display.show_stats(self.character)

    def _show_character_skills(self):
        self.display.show_skills(self.character)

    def _show_character_inventory(self):
        inventory = getattr(self.character, 'inventory', None) or []
        unique_codes = set(slot.get('code') for slot in inventory if slot.get('code'))
        self.display.print('Loading items data...', end='\r')
        item_names = {}
        for item_code in unique_codes:
            item = self.get_item(item_code)
            item_names[item_code] = (item or {}).get('name', item_code)
        self.display.show_inventory(self.character, item_names)

    def _show_character_equipment(self):
        effects_data = self.get_effects()
        effect_names = {effect['code']: effect['name'] for effect in effects_data if 'code' in effect}

        unique_codes = set()
        for slot_name in ('weapon', 'shield', 'helmet', 'body_armor', 'leg_armor', 'boots',
                          'ring1', 'ring2', 'amulet', 'artifact1', 'artifact2', 'artifact3',
                          'rune', 'utility1', 'utility2', 'bag'):
            item_code = getattr(self.character, f'{slot_name}_slot', None)
            if item_code:
                unique_codes.add(item_code)

        self.display.print('Loading items data...', end='\r')
        items_data = {}
        for code in unique_codes:
            items_data[code] = self.get_item(code)
        self.display.show_equipment(self.character, effect_names, items_data)

    # ── Character selection ─────────────────────────────────────

    def _choose_character(self):
        character = self.select_character()
        if character is None:
            return

        self.character = character
        self.scenarios_storage = ScenariosStorage(self.character)

    def select_character(self):
        """Selecting a character from the list on the account. Returns the
        Character instance, or None if the user pressed Enter to go back."""

        characters = self.get_my_characters()

        if not characters:
            self.display.print('You have no characters. Creating a new one...')
            created = self._prompt_and_create_character()
            if not created:
                sys.exit('Failed to create a character. Aborting.')
            characters = self.get_my_characters()

        if not characters:
            sys.exit('No characters available and the API is unreachable with the current token.')

        return self._prompt_character_choice(characters)

    def _prompt_character_choice(self, characters):
        characters_map, characters_map_str = self._prepare_actions_menu_data(
            [character["name"] for character in characters],
        )
        self.display.print(f'Characters on account: {", ".join(characters_map.values())}')

        idx = self._prompt_int(
            'Which character do you want to choose?\n'
            f'{characters_map_str}\n'
            'Please type a number: '
        )

        if idx is None or idx not in characters_map:
            return None

        return self._build_character(characters_map[idx])

    def _build_character(self, name):
        character = Character(name, parent=self, display=self.display)
        self.display.print(f'Selected character {name}.')
        self.display.print(f'Level {character.level}, HP {character.hp}/{character.max_hp}, '
                           f'Gold {character.gold}, Cooldown {character.cooldown}s.')
        self.display.show_image(ImageCategoryEnum.CHARACTERS, character.skin)

        return character

    # ── Season / server info ────────────────────────────────────

    def show_current_season(self):
        """Show the current season info at startup. Also acts as a
        network availability check (exits if the server is unreachable)."""

        response = self._get()

        if response.status_code != 200:
            sys.exit('Can\'t reach the server. Please try again later.')

        data = response.json().get('data', {})
        self.display.print(f'Game version: {data.get("version", "?")}.')

        season = data.get('season') or {}
        name = season.get('name', '?')
        number = season.get('number', '?')
        start = season.get('start_date', '?')
        self.display.print(f'Current season: {name} (#{number}), started {start}.')

    # ── Account management (console-specific) ───────────────────

    def _prompt_and_create_character(self):
        """Prompt for name/sex via display and create character (console path)."""
        name = self._display_prompt_character_name()
        if name is None:
            return False
        sex = self._display_prompt_character_sex()
        if sex is None:
            return False
        ok = self.create_character(name, sex)
        if ok:
            self.display.print('You can now select the new character from the menu.')
        return ok

    def _display_prompt_character_name(self):
        while True:
            name = self.display.prompt_str('New character name (3-12 chars, a-z, 0-9, _ -): ')
            if name is None:
                return None
            if re.match(r'^[a-zA-Z0-9_-]{3,12}$', name):
                return name
            self.display.print('Name must be 3-12 characters using only a-z, 0-9, _, -.')

    def _display_prompt_character_sex(self):
        while True:
            sex = self.display.prompt_str('Sex: male (m) / female (f) / random (r): ')
            if sex is None:
                return None
            sex = sex.strip().lower()
            if sex in ('m', 'f', 'r'):
                return sex
            self.display.print('Please enter m, f, or r.')

    def delete_character(self, name=''):
        """Delete a character."""

        if not name:
            name = input('What is the name of the character to delete?: ')

        confirm = self._prompt_yes_no(f'Are you sure you want to permanently delete {name}?')
        if not confirm:
            self.display.print('Deletion cancelled.')
            return False

        response = self._post_with_reauth(url='/characters/delete', data={'name': name})

        if response.status_code == 200:
            self.display.print(f'Character {name} successfully deleted.')
            return True

        if error_block := response.json().get('error'):
            self.display.print(error_block.get('message', 'Unknown error.'))

        return False

    def _show_account_details(self):
        """Display account details (console path from account menu)."""
        data = self.get_account_details()
        if data is not None:
            self.display.print('=== Account details ===')
            for key, value in data.items():
                self.display.print(f'  {key}: {value}')

    def change_password(self):
        """Change account password."""

        current = input('Enter current password: ')
        new = input('Enter new password: ')
        response = self._post_with_reauth(url='/my/change_password', data={
            'current_password': current,
            'new_password': new,
        })

        if response.status_code == 200:
            self.display.print('Password changed. Note: your token has been reset, update config.ini.')
            return

        if error_block := response.json().get('error'):
            self.display.print(error_block.get('message', 'Unknown error.'))

    def login_with_password(self):
        """Force a fresh login (replace the current token with one obtained
        from username/password). Useful when the saved token is expired or
        has been reset."""

        if self.request_new_token():
            self._propagate_token_to_characters()
            self.character.refresh()

    # ── Utility wrappers ────────────────────────────────────────

    def _prepare_actions_menu_data(self, iterable):
        return self.display.prepare_menu(iterable)

    def _prompt_int(self, prompt, min_val=None, max_val=None):
        return self.display.prompt_int(prompt, min_val, max_val)

    def _prompt_str(self, prompt, allow_empty=True):
        return self.display.prompt_str(prompt, allow_empty)

    # ── Character actions (dispatched via main_menu_map) ────────

    def character_movement(self):
        layer = getattr(self.character, 'layer', MapLayerEnum.OVERWORLD)
        maps = self.get_maps_data(layer=layer)
        available_types_map, available_types_str = self._build_location_type_menu(maps)

        location_type_idx = self._prompt_int(
            'What type of location do you want to move to?\n'
            f'{available_types_str}\n'
            'Please type a number: '
        )
        if location_type_idx is None:
            return

        chosen_locations = self._select_destinations(maps, available_types_map, location_type_idx)
        if not chosen_locations:
            return

        self._prompt_and_move(chosen_locations)

    def _build_location_type_menu(self, maps):
        available_types = sorted(
            map_type
            for map_type in{((_map.get('interactions') or {}).get('content') or {}).get('type', '') for _map in maps}
            if map_type
        )
        return self._prepare_actions_menu_data(available_types)

    def _select_destinations(self, maps, available_types_map, location_type_idx):
        if location_type_idx == 0:
            return maps

        chosen_location_type = available_types_map[location_type_idx]
        return [
            _map
            for _map in maps
            if ((_map.get('interactions') or {}).get('content') or {}).get('type', '') == chosen_location_type
        ]

    def _prompt_and_move(self, chosen_locations):
        chosen_locations_map, chosen_locations_str = self._prepare_actions_menu_data(
            [
                f'{_map.get("interactions", {}).get("content", {}).get("code")} (Location {_map["x"]}, {_map["y"]})'
                for _map in chosen_locations
            ]
        )

        if len(chosen_locations_map) == 0:
            self.display.print('No destinations of the chosen type.')
            return

        if len(chosen_locations_map) == 1:
            chosen_location_idx = 1
        else:
            chosen_location_idx = self._prompt_int(
                'Where do you want to move?\n'
                f'{chosen_locations_str}\n'
                'Please type a number: '
            )
            if chosen_location_idx is None:
                return

        chosen_location = chosen_locations[chosen_location_idx - 1]
        self.character.move(x=chosen_location['x'], y=chosen_location['y'])

    def character_transition(self):
        self.character.transition()

    def character_fight(self):
        count = self._prompt_int('How many times to fight?: ', min_val=1)
        if count is None:
            return

        self._do_fight(count)

    def _do_fight(self, count):
        participants = self._collect_boss_participants() if self._at_boss() else []
        self.display.start_batch(count)
        for _ in range(count):
            self.character.fight(participants=participants or None)
        self.display.end_batch()

    def _at_boss(self):
        cur_location = self.get_location_data(self.character.layer, self.character.x, self.character.y)
        monster_code = (cur_location.get('content') or {}).get('code')
        if not monster_code:
            return False
        monster = self.get_monster(monster_code)
        return monster.get('type') == 'boss'

    def _collect_boss_participants(self):
        use_multi = self._prompt_yes_no('Boss detected. Use multi-character fight?')
        if not use_multi:
            return []

        my_chars = self.get_my_characters()
        others = [c['name'] for c in my_chars if c['name'] != self.character.name]
        if not others:
            return []

        return self._parse_participants(others)

    def _parse_participants(self, others):
        others_map, others_str = self._prepare_actions_menu_data(others)
        sel = input(
            'Select participants (comma separated, max 2):\n'
            f'{others_str}\n'
        )

        result = []
        try:
            result = [others_map[int(s.strip())] for s in sel.split(',') if s.strip().isdigit()]
        except (ValueError, KeyError):
            result = []

        return result

    def character_gathering(self):
        count = self._prompt_int('How many times to gather?: ', min_val=1)
        if count is None:
            return

        self._do_gather(count)

    def _do_gather(self, count):
        self.display.start_batch(count)
        for _ in range(count):
            self.character.gathering()
        self.display.end_batch()

    def character_crafting(self):
        items_list = self._fetch_craftable_items()
        if items_list is None:
            return

        items_map, items_map_str = self._prepare_actions_menu_data([item['name'] for item in items_list])
        craft_idx = self._prompt_int(
            'What item do you want to craft?\n'
            f'{items_map_str}\n'
            'Please type a number: '
        )
        if craft_idx is None:
            return

        self._do_crafting(items_list, items_map, craft_idx)

    def _do_crafting(self, items_list, items_map, craft_idx):
        craft_code = self._resolve_craft_code(items_list, items_map, craft_idx)
        quantity = self._prompt_int('How many do you want to create?: ', min_val=1)
        if quantity is None:
            return

        self.character.crafting(craft_code, quantity)

    def _fetch_craftable_items(self):
        location_data = self.get_location_data(self.character.layer, self.character.x, self.character.y)
        content = location_data.get('content') or {}

        if content.get('type') != MapTypesEnum.WORKSHOP:
            self.display.print('You can\'t craft anything at this location.')
            return None

        workshop_type = content.get('code', '')
        items_list = self.get_items(
            craft_skill=workshop_type,
            max_level=getattr(self.character, f'{workshop_type}_level', 1),
        )

        if not items_list:
            self.display.print('No craftable items available for your level at this workshop.')
            return None

        return items_list

    def _resolve_craft_code(self, items_list, items_map, craft_idx):
        return next(
            (it['code'] for it in items_list if it['name'] == items_map[craft_idx]),
            '',
        )

    def character_recycling(self):
        if not self._at_workshop():
            self.display.print('You can\'t recycle anything at this location.')
            return

        inventory = self._non_empty_inventory()
        if not inventory:
            self.display.print('Your inventory is empty.')
            return

        inventory_map, inventory_map_str = self._prepare_actions_menu_data(
            [f"{slot['code']} (x{slot.get('quantity', 1)})" for slot in inventory]
        )
        chosen_item_idx = self._prompt_int(
            'What item do you want to recycle?\n'
            f'{inventory_map_str}\n'
            'Please type a number: '
        )
        if chosen_item_idx is None:
            return

        self._do_recycle(inventory, inventory_map, chosen_item_idx)

    def _do_recycle(self, inventory, inventory_map, chosen_item_idx):
        chosen_label = inventory_map[chosen_item_idx]
        item_code = chosen_label.split(' (')[0]
        max_qty = next(
            (s.get('quantity', 1) for s in inventory if s['code'] == item_code),
            1,
        )
        quantity = self._prompt_int(f'How many do you want to recycle (max {max_qty})?: ', min_val=1)
        if quantity is None:
            return

        self._ensure_at_correct_workshop(item_code)
        self.character.recycling(item_code, quantity)

    def _ensure_at_correct_workshop(self, item_code):
        item = self.get_item(code=item_code)
        craft = item.get('craft') or {}
        skill = craft.get('skill', '')
        if skill:
            response = self._get_with_reauth(url='/maps', data={'content_code': skill, 'size': 1})
            if response.status_code == 200:
                data = response.json().get('data', [])
                if data:
                    loc = data[0]
                    self.character.move(loc['x'], loc['y'])

    def _at_workshop(self):
        location_data = self.get_location_data(self.character.layer, self.character.x, self.character.y)
        return location_data.get('interactions', {}).get('content', {}).get('type') == MapTypesEnum.WORKSHOP

    def _non_empty_inventory(self):
        return [slot for slot in self.character.inventory if slot.get('code')]

    def character_equip(self):
        inventory = self._non_empty_inventory()
        if not inventory:
            self.display.print('Your inventory is empty.')
            return

        inventory_map, inventory_map_str = self._prepare_actions_menu_data(
            [slot['code'] for slot in inventory]
        )
        chosen_item_idx = self._prompt_int(
            'What item do you want to equip?\n'
            f'{inventory_map_str}\n'
            'Please type a number: '
        )
        if chosen_item_idx is None:
            return

        self._do_equip(inventory_map, chosen_item_idx)

    def _do_equip(self, inventory_map, chosen_item_idx):
        item_code = inventory_map[chosen_item_idx]
        item_data = self.get_item(item_code)
        if item_data['type'] not in ItemTypesEnum.EQUIP_TYPES:
            self.display.print('This item type is not equippable.')
            return

        if item_data.get('level', 0) > self.character.level:
            self.display.print(f"You need to be level {item_data['level']} to equip this item.")
            return

        matching_slots = [
            s for s in EquipmentSlotsEnum
            if s == item_data['type']
            or s.startswith(item_data['type'])
            or s == item_code
        ]

        if not matching_slots:
            self.display.print('Could not determine a slot for this item.')
            return

        if len(matching_slots) == 1:
            equip_slot = matching_slots[0]
        else:
            def _slot_label(s):
                return s.replace('_slot', '').replace('_', ' ').title()

            slot_options = [
                {
                    'code': s,
                    'name': f'{_slot_label(s)} (occupied)'
                            if getattr(self.character, f'{s}_slot', None)
                            else f'{_slot_label(s)} (empty)'
                }
                for s in matching_slots
            ]
            slots_map, slots_map_str = self._prepare_actions_menu_data(slot_options)
            chosen_idx = self._prompt_int(
                'Which slot do you want to equip to?\n'
                f'{slots_map_str}\n'
                'Please type a number: '
            )
            if chosen_idx is None:
                return
            equip_slot = slots_map[chosen_idx]['code']

        quantity = None
        if equip_slot in ('utility1', 'utility2'):
            inv_qty = next(
                (s.get('quantity', 1) for s in (self.character.inventory or [])
                 if s.get('code') == item_code),
                1,
            )
            qty = self._prompt_int(f'How many to equip (max {inv_qty})?: ', min_val=1)
            if qty is not None:
                quantity = qty

        self.character.equip(item_code, equip_slot, quantity)

    def character_unequip(self):
        slots_map, slots_map_str = self._prepare_actions_menu_data(
            [action for action in EquipmentSlotsEnum]
        )
        slot_idx = self._prompt_int(
            'Which slot do you want to unequip?\n'
            f'{slots_map_str}\n'
            'Please type a number: '
        )
        if slot_idx is None:
            return

        self.character.unequip(slots_map[slot_idx])

    def character_use_item(self):
        inventory = self._non_empty_inventory()
        if not inventory:
            self.display.print('Your inventory is empty.')
            return

        inventory_map, inventory_map_str = self._prepare_actions_menu_data(
            [slot['code'] for slot in inventory]
        )
        chosen_item_idx = self._prompt_int(
            'What item do you want to use?\n'
            f'{inventory_map_str}\n'
            'Please type a number: '
        )
        if chosen_item_idx is None:
            return

        self._do_use_item(inventory, inventory_map, chosen_item_idx)

    def _do_use_item(self, inventory, inventory_map, chosen_item_idx):
        item_code = inventory_map[chosen_item_idx]
        max_qty = next(
            (s.get('quantity', 1) for s in inventory if s['code'] == item_code),
            1,
        )
        quantity = self._prompt_int(f'How many do you want to use (max {max_qty})?: ', min_val=1)
        if quantity is None:
            return

        self.character.use_item(item_code, quantity)

    def character_delete_item(self):
        inventory = self._non_empty_inventory()
        if not inventory:
            self.display.print('Your inventory is empty.')
            return

        inventory_map, inventory_map_str = self._prepare_actions_menu_data(
            [f"{slot['code']} (x{slot.get('quantity', 1)})" for slot in inventory]
        )
        chosen_item_idx = self._prompt_int(
            'What item do you want to delete?\n'
            f'{inventory_map_str}\n'
            'Please type a number: '
        )
        if chosen_item_idx is None:
            return

        self._do_delete_item(inventory, inventory_map, chosen_item_idx)

    def _do_delete_item(self, inventory, inventory_map, chosen_item_idx):
        chosen_label = inventory_map[chosen_item_idx]
        item_code = chosen_label.split(' (')[0]
        max_qty = next(
            (s.get('quantity', 1) for s in inventory if s['code'] == item_code),
            1,
        )
        quantity = self._prompt_int(f'How many do you want to delete (max {max_qty})?: ', min_val=1)
        if quantity is None:
            return

        self.character.delete_item(item_code, quantity)

    def character_rest(self):
        self.character.rest()

    def character_change_skin(self):
        skins_map, skins_str = self._prepare_actions_menu_data(
            [skin for skin in CharacterSkinsEnum]
        )
        locked = ', '.join(s for s in CharacterSkinsEnum.SEASON_SKINS)
        sel = self._prompt_int(
            'What skin do you want to change to?\n'
            f'{skins_str}\n'
            f'Season skins ({locked}) require unlocking via achievement points.\n'
            'Please type a number: '
        )
        if sel is None:
            return

        self.character.change_skin(skins_map[sel])

    def character_get_new_task(self):
        self.character.get_task()

    def character_complete_task(self):
        self.character.complete_task()

    def character_cancel_task(self):
        self.character.cancel_task()

    def character_exchange_task_coins(self):
        self.character.exchange_task_coins()

    def character_trade_task(self):
        items_map, items_str = self._prepare_actions_menu_data(
            [slot['code'] for slot in self.character.inventory if slot.get('code')]
        )
        idx = self._prompt_int(
            'What item do you want to trade with the Tasks Master?\n'
            f'{items_str}\n'
            'Please type a number: '
        )
        if idx is None:
            return

        self._do_trade_task(items_map, idx)

    def _do_trade_task(self, items_map, idx):
        item_code = items_map[idx]
        qty = self._prompt_int('How many?: ', min_val=1)
        if qty is None:
            return

        self.character.trade_task(item_code, qty)

    def character_claim_pending_item(self):
        items = self.get_my_pending_items()
        if not items:
            self.display.print('No pending items to claim.')
            return

        items_map, items_str = self._prepare_actions_menu_data(
            [f"{it['id']} - {it['description']}" for it in items]
        )
        idx = self._prompt_int(
            'Which pending item do you want to claim?\n'
            f'{items_str}\n'
            'Please type a number: '
        )
        if idx is None:
            return

        self.character.claim_pending_item(items[idx - 1]['id'])

    def character_npc_buy_item(self):
        item_code = input('What item code do you want to buy from the NPC?: ')
        quantity = self._prompt_int('How many?: ', min_val=1)
        if quantity is None:
            return

        self.character.npc_buy(item_code, quantity)

    def character_npc_sell_item(self):
        inventory = self._non_empty_inventory()
        items_map, items_str = self._prepare_actions_menu_data(
            [slot['code'] for slot in inventory]
        )
        idx = self._prompt_int(
            'What item do you want to sell to the NPC?\n'
            f'{items_str}\n'
            'Please type a number: '
        )
        if idx is None:
            return

        self._do_npc_sell(inventory, items_map, idx)

    def _do_npc_sell(self, inventory, items_map, idx):
        item_code = items_map[idx]
        max_qty = next(
            (s.get('quantity', 1) for s in inventory if s['code'] == item_code),
            1,
        )
        qty = self._prompt_int(f'How many (max {max_qty})?: ', min_val=1)
        if qty is None:
            return

        self.character.npc_sell(item_code, qty)

    def character_buy_bank_expansion(self):
        self.character.buy_bank_expansion()

    def character_deposit_item_to_bank(self):
        inventory = self._non_empty_inventory()
        if not inventory:
            self.display.print('Your inventory is empty.')
            return

        inventory_map, inventory_map_str = self._prepare_actions_menu_data(
            [slot['code'] for slot in inventory]
        )
        chosen_item_idx = self._prompt_int(
            'What item do you want to deposit?\n'
            f'{inventory_map_str}\n'
            'Please type a number: '
        )
        if chosen_item_idx is None:
            return

        self._do_deposit_item(inventory, inventory_map, chosen_item_idx)

    def _do_deposit_item(self, inventory, inventory_map, chosen_item_idx):
        item_code = inventory_map[chosen_item_idx]
        max_qty = next(
            (s.get('quantity', 1) for s in inventory if s['code'] == item_code),
            1,
        )
        quantity = self._prompt_int(f'How many do you want to deposit (max {max_qty})?: ', min_val=1)
        if quantity is None:
            return

        self.character.deposit_item(item_code, quantity)

    def character_withdraw_item_from_bank(self):
        bank_items = self.get_my_bank_items()
        if not bank_items:
            self.display.print('Bank is empty.')
            return

        bank_items_map, bank_items_map_str = self._prepare_actions_menu_data(
            [item['code'] for item in bank_items]
        )
        chosen_item_idx = self._prompt_int(
            'What item do you want to withdraw?\n'
            f'{bank_items_map_str}\n'
            'Please type a number: '
        )
        if chosen_item_idx is None:
            return

        self._do_withdraw_item(bank_items, bank_items_map, chosen_item_idx)

    def _do_withdraw_item(self, bank_items, bank_items_map, chosen_item_idx):
        item_code = bank_items_map[chosen_item_idx]
        max_qty = next(
            (s.get('quantity', 0) for s in bank_items if s['code'] == item_code),
            0,
        )
        quantity = self._prompt_int(f'How many do you want to withdraw (bank has {max_qty})?: ', min_val=1)
        if quantity is None:
            return

        self.character.withdraw_item(item_code, quantity)

    def character_deposit_gold_to_bank(self):
        quantity = self._prompt_int(f'How many gold do you want to deposit (you have {self.character.gold})?: ', min_val=1)
        if quantity is None:
            return

        self.character.deposit_gold(quantity)

    def character_withdraw_gold_from_bank(self):
        bank = self.get_my_bank()
        quantity = self._prompt_int(f'How many gold do you want to withdraw (bank has {bank.get("gold", 0)})?: ', min_val=1)
        if quantity is None:
            return

        self.character.withdraw_gold(quantity)

    def character_give_gold(self):
        my_chars = self.get_my_characters()
        others_map, others_str = self._prepare_actions_menu_data(
            [c['name'] for c in my_chars if c['name'] != self.character.name]
        )
        if not others_map:
            self.display.print('You have no other characters.')
            return

        idx = self._prompt_int(
            'To which character do you want to give gold?\n'
            f'{others_str}\n'
            'Please type a number: '
        )
        if idx is None:
            return

        self._do_give_gold(others_map, idx)

    def _do_give_gold(self, others_map, idx):
        target = others_map[idx]
        qty = self._prompt_int(f'How many gold to give to {target} (you have {self.character.gold})?: ', min_val=1)
        if qty is None:
            return

        self.character.give_gold(target, qty)

    def character_give_item(self):
        my_chars = self.get_my_characters()
        others_map, others_str = self._prepare_actions_menu_data(
            [c['name'] for c in my_chars if c['name'] != self.character.name]
        )
        if not others_map:
            self.display.print('You have no other characters.')
            return

        idx = self._prompt_int(
            'To which character do you want to give items?\n'
            f'{others_str}\n'
            'Please type a number: '
        )
        if idx is None:
            return

        self._do_give_item(others_map, idx)

    def _do_give_item(self, others_map, idx):
        target = others_map[idx]
        inventory = self._non_empty_inventory()
        if not inventory:
            self.display.print('Your inventory is empty.')
            return

        items_map, items_str = self._prepare_actions_menu_data(
            [slot['code'] for slot in inventory]
        )
        iidx = self._prompt_int(
            'What item do you want to give?\n'
            f'{items_str}\n'
            'Please type a number: '
        )
        if iidx is None:
            return

        self._finish_give_item(inventory, items_map, iidx, target)

    def _finish_give_item(self, inventory, items_map, iidx, target):
        item_code = items_map[iidx]
        max_qty = next(
            (s.get('quantity', 1) for s in inventory if s['code'] == item_code),
            1,
        )
        qty = self._prompt_int(f'How many (max {max_qty})?: ', min_val=1)
        if qty is None:
            return

        self.character.give_item(target, item_code, qty)

    def character_ge_buy_item(self):
        orders = self.get_my_ge_orders(order_type=GEOrderTypeEnum.SELL)
        if not orders:
            self.display.print('No sell orders available to buy from.')
            return

        orders_map, orders_str = self._prepare_actions_menu_data(
            [f"{o['code']} @ {o['price']}g (x{o['quantity']})" for o in orders]
        )
        idx = self._prompt_int(
            'Which order do you want to buy from?\n'
            f'{orders_str}\n'
            'Please type a number: '
        )
        if idx is None:
            return

        self._do_ge_buy(orders, idx)

    def _do_ge_buy(self, orders, idx):
        order = orders[idx - 1]
        qty = self._prompt_int(f'How many to buy (max {order["quantity"]})?: ', min_val=1)
        if qty is None:
            return

        self.character.ge_buy(order['id'], qty)

    def character_ge_create_sell_order(self):
        inventory = self._non_empty_inventory()
        items_map, items_str = self._prepare_actions_menu_data(
            [slot['code'] for slot in inventory]
        )
        idx = self._prompt_int(
            'What item do you want to sell on the GE?\n'
            f'{items_str}\n'
            'Please type a number: '
        )
        if idx is None:
            return

        self._do_ge_create_sell_order(inventory, items_map, idx)

    def _do_ge_create_sell_order(self, inventory, items_map, idx):
        item_code = items_map[idx]
        max_qty = next(
            (s.get('quantity', 1) for s in inventory if s['code'] == item_code),
            1,
        )
        qty = self._prompt_int(f'How many to sell (max {max_qty})?: ', min_val=1)
        if qty is None:
            return

        price = self._prompt_int('At what price per unit?: ', min_val=1)
        if price is None:
            return

        self.character.ge_create_sell_order(item_code, qty, price)

    def character_ge_create_buy_order(self):
        item_code = input('What item code do you want to create a buy order for?: ')
        qty = self._prompt_int('How many?: ', min_val=1)
        if qty is None:
            return

        price = self._prompt_int('At what price per unit?: ', min_val=1)
        if price is None:
            return

        self.character.ge_create_buy_order(item_code, qty, price)

    def character_ge_fill_order(self):
        orders = self.get_my_ge_orders(order_type=GEOrderTypeEnum.BUY)
        if not orders:
            self.display.print('No buy orders to fill.')
            return

        orders_map, orders_str = self._prepare_actions_menu_data(
            [f"{o['code']} @ {o['price']}g (x{o['quantity']})" for o in orders]
        )
        idx = self._prompt_int(
            'Which buy order do you want to fill?\n'
            f'{orders_str}\n'
            'Please type a number: '
        )
        if idx is None:
            return

        self._do_ge_fill(orders, idx)

    def _do_ge_fill(self, orders, idx):
        order = orders[idx - 1]
        qty = self._prompt_int(f'How many to fill (max {order["quantity"]})?: ', min_val=1)
        if qty is None:
            return

        self.character.ge_fill(order['id'], qty)

    def character_ge_cancel_order(self):
        orders = self.get_my_ge_orders()
        if not orders:
            self.display.print('You have no open GE orders.')
            return

        orders_map, orders_str = self._prepare_actions_menu_data(
            [f"[{o['type']}] {o['code']} @ {o['price']}g (x{o['quantity']})" for o in orders]
        )
        idx = self._prompt_int(
            'Which order do you want to cancel?\n'
            f'{orders_str}\n'
            'Please type a number: '
        )
        if idx is None:
            return

        self.character.ge_cancel(orders[idx - 1]['id'])

    # ── Display-only views ──────────────────────────────────────

    def show_bank(self):
        bank = self.get_my_bank()
        bank_items = self.get_my_bank_items()
        if not bank:
            self.display.print('Could not get bank details.')
            return

        self._print_bank(bank, bank_items)

    def _print_bank(self, bank, bank_items):
        self.display.print('=== Bank details ===')
        self.display.print(f'  Slots: {bank.get("slots")}')
        self.display.print(f'  Expansions: {bank.get("expansions")}')
        self.display.print(f'  Next expansion cost: {bank.get("next_expansion_cost")}g')
        self.display.print(f'  Gold: {bank.get("gold")}g')

        if bank_items:
            self.display.print('  Items:')
            for it in bank_items:
                self.display.print(f'    {it["code"]} x{it.get("quantity", 1)}')
        else:
            self.display.print('  Items: (empty)')

    def show_pending_items(self):
        items = self.get_my_pending_items()
        if not items:
            self.display.print('No pending items.')
            return

        self.display.print('=== Pending items ===')
        for it in items:
            self.display.print(f'  [{it.get("source", "?")}] {it.get("description", "")} '
                  f'(id={it.get("id")}, gold={it.get("gold", 0)})')
            for sub in it.get('items', []) or []:
                self.display.print(f'    -> {sub["code"]} x{sub.get("quantity", 1)}')

    def show_ge_orders(self):
        orders = self.get_my_ge_orders()
        if not orders:
            self.display.print('No open GE orders.')
            return

        self.display.print('=== My GE orders ===')
        for o in orders:
            self.display.print(f'  [{o["type"]}] {o["code"]} x{o["quantity"]} @ {o["price"]}g '
                  f'(id={o["id"]}, created={o.get("created_at", "?")})')

    # ── Scenarios ───────────────────────────────────────────────

    def use_scenario(self):
        scenarios_category_map, scenarios_category_str = self._prepare_actions_menu_data(
            list(self.scenarios_storage.scenarios_category_map.keys()),
        )

        category_idx = self._prompt_int(
            'Which type of scenario do you want to launch?\n'
            f'{scenarios_category_str}\n'
            'Please type a number: '
        )
        if category_idx is None:
            return

        category = scenarios_category_map[category_idx]
        category_scenarios = self.scenarios_storage.scenarios_category_map[category]()
        scenarios_map, scenarios_map_str = self._prepare_actions_menu_data(
            [self._scenario_name(scenario) for scenario in category_scenarios]
        )

        if not scenarios_map:
            self.display.print('No scenarios available in this category yet.')
            return

        if len(scenarios_map) == 1:
            scenario_idx = next(iter(scenarios_map))
        else:
            scenario_idx = self._prompt_int(
                'Which scenario do you want to launch?\n'
                f'{scenarios_map_str}\n'
                'Please type a number: '
            )
            if scenario_idx is None:
                return

        self._run_scenario(category_scenarios, scenarios_map, scenario_idx)

    def _run_scenario(self, category_scenarios, scenarios_map, scenario_idx):
        selected_scenario = next(
            scenario for scenario in category_scenarios
            if self._scenario_name(scenario) == scenarios_map[scenario_idx]
        )
        params = self._collect_scenario_params(selected_scenario)
        repeats = self._scenario_repeats(params)
        self._invoke_scenario(selected_scenario, params, repeats, self.display)

    def _collect_scenario_params(self, scenario):
        import inspect
        sig = inspect.signature(scenario)
        params = {}
        for name, param in sig.parameters.items():
            if param.default is inspect.Parameter.empty:
                val = self._prompt_int(f'Enter value for "{name}": ', min_val=1)
                if val is not None:
                    params[name] = val
            else:
                hint = f' (default: {param.default})'
                val = self._prompt_int(f'Enter value for "{name}"{hint}: ', min_val=1)
                if val is not None:
                    params[name] = val
        return params

    def _scenario_repeats(self, params):
        return params.pop('quantity', params.pop('count', 1))

    def _scenario_name(self, scenario):
        return scenario.func.__name__.replace('_', ' ').title()

    def _invoke_scenario(self, scenario, params, repeats, display=None):
        if display and repeats > 1:
            display.start_batch(repeats)
        for _ in range(max(1, repeats)):
            scenario(**params)
        if display and repeats > 1:
            display.end_batch()
