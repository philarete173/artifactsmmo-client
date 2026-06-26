from time import sleep

from base.base import BaseGameClient
from base.enums import ItemTypesEnum


class Character(BaseGameClient):
    """Client for character-level interaction."""

    CHARACTER_INFO_FIELDS = (
        'name', 'account', 'skin', 'level', 'xp', 'max_xp', 'gold',
        'mining_level', 'mining_xp', 'mining_max_xp',
        'woodcutting_level', 'woodcutting_xp', 'woodcutting_max_xp',
        'fishing_level', 'fishing_xp', 'fishing_max_xp',
        'weaponcrafting_level', 'weaponcrafting_xp', 'weaponcrafting_max_xp',
        'gearcrafting_level', 'gearcrafting_xp', 'gearcrafting_max_xp',
        'jewelrycrafting_level', 'jewelrycrafting_xp', 'jewelrycrafting_max_xp',
        'cooking_level', 'cooking_xp', 'cooking_max_xp',
        'alchemy_level', 'alchemy_xp', 'alchemy_max_xp',
        'hp', 'max_hp', 'haste', 'critical_strike', 'wisdom', 'prospecting',
        'initiative', 'threat',
        'attack_fire', 'attack_earth', 'attack_water', 'attack_air',
        'dmg', 'dmg_fire', 'dmg_earth', 'dmg_water', 'dmg_air',
        'res_fire', 'res_earth', 'res_water', 'res_air',
        'effects',
        'x', 'y', 'layer', 'map_id',
        'cooldown', 'cooldown_expiration',
        'weapon_slot', 'shield_slot', 'helmet_slot', 'body_armor_slot',
        'leg_armor_slot', 'boots_slot', 'ring1_slot', 'ring2_slot',
        'amulet_slot', 'artifact1_slot', 'artifact2_slot', 'artifact3_slot',
        'rune_slot', 'utility1_slot', 'utility1_slot_quantity',
        'utility2_slot', 'utility2_slot_quantity', 'bag_slot',
        'task', 'task_type', 'task_progress', 'task_total',
        'inventory_max_items', 'inventory',
    )

    def __init__(self, name, parent=None, display=None) -> None:
        super().__init__()

        self.name = name
        self.parent = parent
        self.display = display
        self.base_character_action_url = f'/my/{self.name}/action'
        self.refresh()

    def _get_with_reauth(self, url, data=None):
        """Run an authenticated GET, automatically offering a re-login if
        the token is rejected. Mirrors GameClient's wrapper but also
        propagates the new token to the parent client so account-level
        calls don't have to re-auth again."""

        self.display.show_loading()
        response = self._get(url=url, data=data)
        self.display.hide_loading()

        if self.is_invalid_token_error(response) and self.ensure_valid_token(probe_response=response):
            self._propagate_token_to_parent()
            self.display.show_loading()
            response = self._get(url=url, data=data)
            self.display.hide_loading()

        return response

    def _post_with_reauth(self, url, data=None):
        """Run an authenticated POST with the same re-login behaviour as
        _get_with_reauth."""

        self.display.show_loading()
        response = self._post(url=url, data=data)
        self.display.hide_loading()

        if self.is_invalid_token_error(response) and self.ensure_valid_token(probe_response=response):
            self._propagate_token_to_parent()
            self.display.show_loading()
            response = self._post(url=url, data=data)
            self.display.hide_loading()

        return response

    def _propagate_token_to_parent(self):
        """Copy the freshly-issued token to the parent GameClient so that
        subsequent account-level calls don't have to re-auth separately."""

        if self.parent is not None and hasattr(self.parent, 'base_headers'):
            self.parent.base_headers['Authorization'] = self.base_headers.get('Authorization', '')

    def refresh(self):
        """Pull fresh character data from the API."""

        self._get_character_info()
        return self

    def _get_character_info(self):
        response = self._get_with_reauth(url=f'/characters/{self.name}')
        if response.status_code != 200:
            if error_block := response.json().get('error'):
                self.display.print(error_block.get('message', 'Unknown error.'))
            return

        for key in self.CHARACTER_INFO_FIELDS:
            if key in response.json().get('data', {}):
                setattr(self, key, response.json()['data'][key])

    def _get_last_action(self):
        last_action_data = self._get_with_reauth(
            url=f'/my/logs',
            data={
                'page': 1,
                'size': 1,
            },
        )

        if last_action_data.status_code == 200:
            logs = last_action_data.json().get('data', [])
            if logs:
                log = logs[0]
                self.display.show_action_log(log.get('description', ''))
                self.display.show_action_details(log)
            else:
                self.display.print('No recent actions.')
        elif error_block := last_action_data.json().get('error'):
            self.display.print(f'Can\'t get last action. {error_block.get("message", "Unknown error.")}.')

        self.refresh()

    def _do_action(self, action_name='', action_data=None):
        if action_data is None:
            action_data = {}

        url = f'{self.base_character_action_url}/{action_name}'
        action_request = self._post_with_reauth(url=url, data=action_data)
        result = self._handle_action_response(action_request, action_name)

        return result

    def _handle_action_response(self, action_request, action_name):
        result = None

        if action_request.status_code == 200:
            data = action_request.json().get('data', {})
            cooldown = data.get('cooldown', {})
            reason = cooldown.get('reason', action_name)
            total_seconds = cooldown.get('total_seconds', 0)
            self.display.show_action_in_progress(reason, total_seconds)

            for i in range(total_seconds, 0, -1):
                self.display.show_action_countdown(i)
                sleep(1)

            self.display.clear_action_countdown()
            self.display.show_action_details(data)
            self._get_last_action()
            result = data
        elif error_block := action_request.json().get('error'):
            self.display.show_action_error(error_block.get("message", "Unknown error."))

        return result

    def move(self, x=0, y=0, map_id=None):
        if map_id is None and self.x == x and self.y == y:
            return True
        data = {}
        if map_id is not None:
            data['map_id'] = map_id
        else:
            data['x'] = x
            data['y'] = y
        return self._do_action('move', data)

    def transition(self):
        return self._do_action('transition')

    def fight(self, participants=None):
        if self.hp < self.max_hp / 2:
            self.display.print(f'HP too low ({self.hp}/{self.max_hp}). Resting...')
            self.rest()

        self._deposit_non_equip_if_full()

        data = {}
        if participants:
            data['participants'] = participants

        return self._do_action('fight', data)

    def _get_gathering_skill_at_location(self):
        response = self._get(url=f'/maps/{self.layer}/{self.x}/{self.y}')
        if response.status_code != 200:
            return None

        map_data = response.json().get('data', {})
        content = map_data.get('interactions', {}).get('content', {})
        if content.get('type') != 'resource':
            return None

        resource_code = content.get('code', '')
        if not resource_code:
            return None

        resource_response = self._get(url=f'/resources/{resource_code}')
        if resource_response.status_code != 200:
            return None

        return resource_response.json().get('data', {}).get('skill')

    def _equip_best_gathering_weapon(self, skill_code):
        if not skill_code:
            return

        current_weapon = getattr(self, 'weapon_slot', None)
        best_code = None
        best_value = 0

        for slot in self.inventory or []:
            code = slot.get('code')
            if not code or code == current_weapon:
                continue

            item_response = self._get(url=f'/items/{code}')
            if item_response.status_code != 200:
                continue

            item = item_response.json().get('data', {})
            if item.get('type') != 'weapon':
                continue

            for effect in item.get('effects') or []:
                if effect.get('code') == skill_code:
                    value = abs(effect.get('value', 0))
                    if value > best_value:
                        best_value = value
                        best_code = code
                    break

        if best_code is None:
            return

        current_value = 0
        if current_weapon:
            item_response = self._get(url=f'/items/{current_weapon}')
            if item_response.status_code == 200:
                current_item = item_response.json().get('data', {})
                for effect in current_item.get('effects') or []:
                    if effect.get('code') == skill_code:
                        current_value = abs(effect.get('value', 0))
                        break

        if best_value > current_value:
            self.display.print(f'Equipping {best_code} (+{best_value} {skill_code})...')
            self.equip(best_code, 'weapon')

    def gathering(self):
        skill_code = self._get_gathering_skill_at_location()
        if skill_code:
            self._equip_best_gathering_weapon(skill_code)

        self._deposit_non_equip_if_full()
        return self._do_action('gathering')

    def _deposit_non_equip_if_full(self):
        inventory = getattr(self, 'inventory', None) or []
        max_items = getattr(self, 'inventory_max_items', 100)
        total_quantity = sum(s.get('quantity', 0) for s in inventory if s.get('code'))
        fill_ratio = total_quantity / max_items if max_items else 0

        if fill_ratio > 0.9:
            unique_codes = set()
            for entry in inventory:
                code = entry.get('code')
                if code:
                    unique_codes.add(code)

            equip_types = set(ItemTypesEnum.EQUIP_TYPES)
            codes_to_deposit = []

            for code in unique_codes:
                response = self._get(url=f'/items/{code}')
                if response.status_code == 200:
                    item_type = response.json().get('data', {}).get('type')
                    if item_type not in equip_types:
                        codes_to_deposit.append(code)

            if codes_to_deposit:
                origin_x, origin_y = self.x, self.y
                at_bank = False

                location = self._get(url=f'/maps/{self.layer}/{self.x}/{self.y}')
                if location.status_code == 200:
                    content_type = (location.json().get('data', {}).get('content') or {}).get('type')
                    at_bank = content_type == 'bank'

                if not at_bank:
                    banks = self._get(url='/maps', data={'content_type': 'bank', 'layer': self.layer, 'size': 100})
                    if banks.status_code == 200:
                        bank_list = banks.json().get('data', [])
                        if bank_list:
                            bank = bank_list[0]
                            self.display.print(f'Moving to bank ({bank["x"]}, {bank["y"]}) to deposit...')
                            self.move(bank['x'], bank['y'])

                inv_by_code = {}
                for entry in (getattr(self, 'inventory', None) or []):
                    c = entry.get('code')
                    if c:
                        inv_by_code[c] = inv_by_code.get(c, 0) + entry.get('quantity', 0)

                self.display.print(f'Inventory {total_quantity}/{max_items} (>90%). Depositing...')
                deposit_list = [(code, inv_by_code.get(code, 0)) for code in codes_to_deposit if inv_by_code.get(code, 0) > 0]
                if deposit_list:
                    self.deposit_items(deposit_list)

                if not at_bank and (self.x != origin_x or self.y != origin_y):
                    self.display.print('Moving back to original location...')
                    self.move(origin_x, origin_y)

    def crafting(self, code='', quantity=1):
        return self._do_action('crafting', {'code': code, 'quantity': quantity})

    def recycling(self, code='', quantity=1):
        return self._do_action('recycling', {'code': code, 'quantity': quantity})

    def equip(self, code='', slot='', quantity=None):
        data = {'code': code, 'slot': slot}
        if quantity is not None:
            data['quantity'] = quantity
        return self._do_action('equip', data)

    def unequip(self, slot='', quantity=None):
        data = {'slot': slot}
        if quantity is not None:
            data['quantity'] = quantity
        return self._do_action('unequip', data)

    def use_item(self, code='', quantity=1):
        return self._do_action('use', {'code': code, 'quantity': quantity})

    def delete_item(self, code='', quantity=1):
        return self._do_action('delete', {'code': code, 'quantity': quantity})

    def rest(self):
        return self._do_action('rest')

    def change_skin(self, skin=''):
        return self._do_action('change_skin', {'skin': skin})

    def get_task(self):
        return self._do_action('task/new')

    def complete_task(self):
        return self._do_action('task/complete')

    def cancel_task(self):
        return self._do_action('task/cancel')

    def exchange_task_coins(self):
        return self._do_action('task/exchange')

    def trade_task(self, code='', quantity=1):
        return self._do_action('task/trade', {'code': code, 'quantity': quantity})

    def deposit_item(self, code='', quantity=1):
        return self._do_action('bank/deposit/item', [{'code': code, 'quantity': quantity}])

    def deposit_items(self, items):
        max_batch = 20
        for index in range(0, len(items), max_batch):
            batch = items[index:index + max_batch]
            payload = [{'code': code, 'quantity': quantity} for code, quantity in batch]
            self._do_action('bank/deposit/item', payload)

    def deposit_gold(self, quantity=0):
        return self._do_action('bank/deposit/gold', {'quantity': quantity})

    def withdraw_item(self, code='', quantity=1):
        return self._do_action('bank/withdraw/item', [{'code': code, 'quantity': quantity}])

    def withdraw_items(self, items):
        max_batch = 20
        for index in range(0, len(items), max_batch):
            batch = items[index:index + max_batch]
            payload = [{'code': code, 'quantity': quantity} for code, quantity in batch]
            self._do_action('bank/withdraw/item', payload)

    def withdraw_gold(self, quantity=0):
        return self._do_action('bank/withdraw/gold', {'quantity': quantity})

    def buy_bank_expansion(self):
        return self._do_action('bank/buy_expansion')

    def give_gold(self, character='', quantity=0):
        return self._do_action('give/gold', {'character': character, 'quantity': quantity})

    def give_item(self, character='', code='', quantity=1):
        return self._do_action('give/item', {
            'character': character,
            'items': [{'code': code, 'quantity': quantity}],
        })

    def claim_pending_item(self, pending_id=''):
        return self._do_action(f'claim_item/{pending_id}')

    def ge_buy(self, order_id='', quantity=1):
        return self._do_action('grandexchange/buy', {'id': order_id, 'quantity': quantity})

    def ge_sell(self, code='', quantity=1, price=0):
        return self._do_action(
            'grandexchange/create-sell-order',
            {'code': code, 'quantity': quantity, 'price': price},
        )

    def ge_create_buy_order(self, code='', quantity=1, price=0):
        return self._do_action(
            'grandexchange/create-buy-order',
            {'code': code, 'quantity': quantity, 'price': price},
        )

    def ge_create_sell_order(self, code='', quantity=1, price=0):
        return self._do_action(
            'grandexchange/create-sell-order',
            {'code': code, 'quantity': quantity, 'price': price},
        )

    def ge_fill(self, order_id='', quantity=1):
        return self._do_action('grandexchange/fill', {'id': order_id, 'quantity': quantity})

    def ge_cancel(self, order_id=''):
        return self._do_action('grandexchange/cancel', {'id': order_id})

    def npc_buy(self, code='', quantity=1):
        return self._do_action('npc/buy', {'code': code, 'quantity': quantity})

    def npc_sell(self, code='', quantity=1):
        return self._do_action('npc/sell', {'code': code, 'quantity': quantity})
