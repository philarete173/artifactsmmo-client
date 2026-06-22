from base import BaseClient, BaseGameClient
from enums import MapTypesEnum


ITEMS_MAX_PAGE_SIZE = 10000

CRAFT_SKILL_LEVEL_ATTR = {
    'weaponcrafting': 'weaponcrafting_level',
    'gearcrafting': 'gearcrafting_level',
    'jewelrycrafting': 'jewelrycrafting_level',
    'cooking': 'cooking_level',
    'woodcutting': 'woodcutting_level',
    'mining': 'mining_level',
    'alchemy': 'alchemy_level',
}


def _prompt_int(prompt, min_val=None, max_val=None):
    """Read an integer from stdin. Empty input returns None (back signal)."""
    while True:
        try:
            raw = input(prompt).strip()

            if raw == '':
                return None

            value = int(raw)

            if min_val is not None and value < min_val:
                print(f'Please enter a number >= {min_val}.')

                continue

            if max_val is not None and value > max_val:
                print(f'Please enter a number <= {max_val}.')

                continue

            return value

        except ValueError:
            print('Please enter a whole number (or press Enter to go back).')


def _inventory_quantity(character, item_code):
    """Total quantity of item_code in the character's inventory."""
    for slot in character.inventory or []:
        if slot.get('code') == item_code:
            return slot.get('quantity', 0)

    return 0


def _fetch_item_details(character, item_code):
    """Fetch a single item's full details. Returns dict or None on failure."""
    response = character._get(url=f'/items/{item_code}')

    if response.status_code != 200:
        return None

    return response.json().get('data', {})


def _fetch_items_by_skill(character, craft_skill):
    """Fetch all craftable items for a skill, grouped by type.

    Single GET to ``/items?craft_skill=X&max_level=Y&size=10000`` (no type filter).
    Returns ``{item_type: [item, ...]}`` with only items that have a ``craft`` field.
    Returns ``{}`` on API error or no craftable items.
    """
    level_attr = CRAFT_SKILL_LEVEL_ATTR[craft_skill]
    max_level = getattr(character, level_attr, 0)

    response = character._get(
        url='/items',
        data={
            'craft_skill': craft_skill,
            'max_level': max_level,
            'size': ITEMS_MAX_PAGE_SIZE,
        },
    )

    if response.status_code != 200:
        error_block = response.json().get('error', {})
        print(f'Can\'t fetch items: {error_block.get("message", "Unknown error.")}.')

        return {}

    body = response.json()
    data = body.get('data', [])
    total = body.get('total')

    if total and total > len(data):
        print(f'Warning: {total} matching items exist but only {len(data)} returned.')

    items_by_type = {}

    for item in data:
        if not item.get('craft'):
            continue

        item_type = item.get('type', '')

        if not item_type:
            continue

        items_by_type.setdefault(item_type, []).append(item)

    return items_by_type


def _fetch_location_for_content(character, content_code='', content_type=''):
    """Find a map cell for given content. Returns (x, y, layer) or None."""
    params = {'size': 1}

    if content_code:
        params['content_code'] = content_code

    if content_type:
        params['content_type'] = content_type

    response = character._get(url='/maps', data=params)

    if response.status_code == 200:
        data = response.json().get('data', [])

        if data:
            location = data[0]

            return (location['x'], location['y'], location.get('layer', 'overworld'))

    return None


def _get_workshop_for_item_code(character, item_code):
    item = _fetch_item_details(character, item_code) or {}
    craft = item.get('craft') or {}
    skill = craft.get('skill', '')
    if skill:
        workshop = _fetch_location_for_content(character, content_code=skill)
        if workshop:
            return workshop
    return _fetch_location_for_content(character, content_type=MapTypesEnum.WORKSHOP)


def _gather_loop(character, item_code, quantity):
    """Gather at current location until we have at least `quantity` more of `item_code`."""
    target = _inventory_quantity(character, item_code) + quantity
    while _inventory_quantity(character, item_code) < target:
        character.gathering()


def _fight_loop(character, item_code, quantity):
    """Fight at current location until we have at least `quantity` more of `item_code`."""
    target = _inventory_quantity(character, item_code) + quantity
    while _inventory_quantity(character, item_code) < target:
        character.fight()


def _gather_base_item(character, item_code, quantity):
    """Move to and gather a base resource that has no recipe of its own."""
    resource_response = character._get(url='/resources', data={'drop': item_code, 'size': 1})
    resource = None

    if resource_response.status_code == 200:
        data = resource_response.json().get('data', [])
        resource = data[0] if data else None

    if resource:
        location = _fetch_location_for_content(character, content_code=resource['code'])

        if location:
            character.move(*location[:2])

        _gather_loop(character, item_code, quantity)

        return

    monster_response = character._get(url='/monsters', data={'drop': item_code, 'size': 1})
    monster = None

    if monster_response.status_code == 200:
        data = monster_response.json().get('data', [])
        monster = data[0] if data else None

    if monster:
        location = _fetch_location_for_content(character, content_code=monster['code'])

        if location:
            character.move(*location[:2])

        _fight_loop(character, item_code, quantity)

        return

    print(f'Warning: don\'t know where to get {item_code}.')


def _fetch_bank_quantity(character, item_code):
    """Check how many of ``item_code`` are in the character's bank."""
    response = character._get(url='/my/bank/items', data={'item_code': item_code})
    if response.status_code == 200:
        for slot in response.json().get('data', []):
            if slot.get('code') == item_code:
                return slot.get('quantity', 0)
    return 0


def _withdraw_from_bank(character, item_code, needed):
    """Move to the bank and withdraw up to ``needed`` of ``item_code``.

    Returns the amount actually withdrawn (may be less than needed if the
    bank doesn't have enough).
    """
    bank = _fetch_location_for_content(character, content_type=MapTypesEnum.BANK)
    if not bank:
        return 0

    bank_qty = _fetch_bank_quantity(character, item_code)
    if bank_qty == 0:
        return 0

    character.move(*bank[:2])
    withdraw_qty = min(bank_qty, needed)
    character.withdraw_item(item_code, withdraw_qty)
    return withdraw_qty


def _craft_at_workshop(character, item_code, craft_skill, executions):
    """Move to the workshop and craft `item_code` `executions` times."""
    workshop = _fetch_location_for_content(character, content_code=craft_skill)

    if workshop:
        character.move(*workshop[:2])

    character.crafting(item_code, executions)


class ItemsScenarios(BaseGameClient):
    """Generic crafting scenarios driven by the /items API.

    A single ``craft_any_item`` scenario replaces all per-item ``craft_X``
    methods from the old scenario collections.
    """

    CATEGORY = 'Craft item'

    CRAFT_SKILL_LEVEL_ATTR = CRAFT_SKILL_LEVEL_ATTR

    MAX_RECIPE_DEPTH = 10

    def __init__(self, character):
        super().__init__()

        self.character = character

    @staticmethod
    def get_scenarios(character):
        return [ItemsScenarios.craft_any_item]

    @classmethod
    def craft_any_item(cls, character):
        craft_skill = cls._prompt_craft_skill(character)

        if craft_skill is None:
            return

        items_by_type = _fetch_items_by_skill(character, craft_skill)

        if not items_by_type:
            level = getattr(character, cls.CRAFT_SKILL_LEVEL_ATTR[craft_skill], 0)
            print(f'No craftable items for {craft_skill} at level {level}.')

            return

        item_type = cls._prompt_item_type(items_by_type)

        if item_type is None:
            return

        items = items_by_type[item_type]
        item = cls._prompt_item(items)

        if item is None:
            return

        quantity = _prompt_int('How many do you want to craft? [default: 1]: ', min_val=1)

        if quantity is None:
            quantity = 1

        post_craft = cls._prompt_post_craft()
        cls._execute_craft(character, item, quantity, post_craft)

    @classmethod
    def _prompt_post_craft(cls):
        choice = input('After crafting: [s]ell, [r]ecycle, [n]othing? ').strip().lower()
        if choice in ('s', 'r'):
            return choice
        return 'n'

    @classmethod
    def _prompt_craft_skill(cls, character):
        skills = list(cls.CRAFT_SKILL_LEVEL_ATTR.keys())
        print('Which craft skill do you want to use?')

        for idx, skill in enumerate(skills, 1):
            level = getattr(character, cls.CRAFT_SKILL_LEVEL_ATTR[skill], 0)
            print(f'  {idx} - {skill} (your level: {level})')

        choice = _prompt_int('Please type a number: ', min_val=1, max_val=len(skills))

        if choice is None:
            return None

        return skills[choice - 1]

    @classmethod
    def _prompt_item_type(cls, items_by_type):
        types = sorted(items_by_type.keys())
        print('What type of item do you want to craft?')

        for idx, item_type in enumerate(types, 1):
            count = len(items_by_type[item_type])
            print(f'  {idx} - {item_type} ({count} item{"s" if count != 1 else ""})')

        choice = _prompt_int('Please type a number: ', min_val=1, max_val=len(types))

        if choice is None:
            return None

        return types[choice - 1]

    @classmethod
    def _prompt_item(cls, items):
        print('Which item do you want to craft?')

        for idx, item in enumerate(items, 1):
            craft = item.get('craft', {})
            craft_skill = craft.get('skill', '?')
            craft_level = craft.get('level', '?')
            print(f'  {idx} - {item["name"]} (item level {item.get("level", "?")}, '
                  f'requires {craft_skill} level {craft_level})')

        choice = _prompt_int('Please type a number: ', min_val=1, max_val=len(items))

        if choice is None:
            return None

        return items[choice - 1]

    @classmethod
    def _execute_craft(cls, character, item, quantity, post_craft):
        remaining = quantity
        while remaining > 0:
            batch = cls._calc_batch_size(character, item, remaining)
            if batch == 0:
                print(f'Inventory full. Cannot craft {item["code"]}.')
                break
            if batch < remaining:
                print(f'Inventory space limited: crafting {batch} instead of {remaining} (batch).')
            craft_per_exec = (item.get('craft') or {}).get('quantity', 1)
            actual = ((batch + craft_per_exec - 1) // craft_per_exec) * craft_per_exec
            if actual != batch:
                print(f'Recipe produces {craft_per_exec} per batch: crafting {actual} instead of {batch}.')
            cls._craft_recursive(character, item, actual, depth=0)
            remaining -= actual

        crafted = quantity - remaining
        if post_craft != 'n' and crafted > 0:
            cls._handle_post_craft(character, item['code'], crafted, post_craft)

    _peak_cache = {}

    @classmethod
    def _peak_items_per_craft(cls, character, item_code, depth=0):
        if depth > 5:
            return 1
        if item_code in cls._peak_cache:
            return cls._peak_cache[item_code]
        item = _fetch_item_details(character, item_code)
        if not item:
            return 1
        craft = item.get('craft') or {}
        if not craft.get('items'):
            cls._peak_cache[item_code] = 1
            return 1
        peak = 1
        for req in craft.get('items', []):
            sub_peak = cls._peak_items_per_craft(character, req['code'], depth + 1)
            total = req['quantity'] * sub_peak
            if total > peak:
                peak = total
        cls._peak_cache[item_code] = peak
        return peak

    @classmethod
    def _calc_batch_size(cls, character, item, quantity):
        max_total = getattr(character, 'inventory_max_items', 100)
        current = sum(s.get('quantity', 0) for s in (character.inventory or []) if s.get('code'))
        available = int(max_total * 0.9) - current
        if available <= 0:
            return 0
        per_item = cls._peak_items_per_craft(character, item['code'])
        if per_item <= 0:
            return quantity
        limit = max(1, available // per_item)
        return min(quantity, limit)

    @classmethod
    def _handle_post_craft(cls, character, item_code, quantity, action):
        if action == 's':
            cls._sell_crafted(character, item_code, quantity)
        elif action == 'r':
            ws = _get_workshop_for_item_code(character, item_code)
            if ws:
                character.move(*ws[:2])
                character.recycling(item_code, quantity)
            else:
                print('No workshop found for recycling.')

    @classmethod
    def _craft_recursive(cls, character, item, quantity, depth):
        craft = item.get('craft')

        if not craft:
            _gather_base_item(character, item['code'], quantity)

            return

        if depth >= cls.MAX_RECIPE_DEPTH:
            print(f'Warning: recipe depth limit ({cls.MAX_RECIPE_DEPTH}) reached for {item["code"]}.')

            return

        craft_quantity_per_exec = craft.get('quantity', 1)
        executions = (quantity + craft_quantity_per_exec - 1) // craft_quantity_per_exec

        for required in craft.get('items', []):
            req_code = required['code']
            req_qty = required['quantity'] * executions
            req_item = _fetch_item_details(character, req_code)

            if req_item is None:
                print(f'Warning: can\'t find details for required item {req_code}, skipping.')

                continue

            # Check how many we already have in inventory
            inv_qty = _inventory_quantity(character, req_code)
            if inv_qty >= req_qty:
                print(f'  Already have {inv_qty}x {req_code} in inventory, skipping.')
                continue

            needed = req_qty - inv_qty

            # Try to withdraw the deficit from bank
            withdrawn = _withdraw_from_bank(character, req_code, needed)
            if withdrawn:
                print(f'  Withdrew {withdrawn}x {req_code} from bank.')
                needed -= withdrawn

            if needed <= 0:
                continue

            cls._craft_recursive(character, req_item, needed, depth + 1)

        _craft_at_workshop(character, item['code'], craft['skill'], executions)

    @classmethod
    def _sell_crafted(cls, character, item_code, quantity):
        ge = _fetch_location_for_content(character, content_type=MapTypesEnum.GRAND_EXCHANGE)

        if ge:
            character.move(*ge[:2])

        character.ge_create_sell_order(item_code, quantity, price=0)
