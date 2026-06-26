import re
from abc import ABC, abstractmethod

from base.enums import (
    CraftSkillEnum,
    EquipmentSlotsEnum,
    GatheringSkillEnum,
)


class Display(ABC):
    """Abstract base for output/input."""

    # ── Abstract output helpers (implemented by subclasses) ──────

    @abstractmethod
    def _output(self, text: str):
        ...

    @abstractmethod
    def _show_window(self, title: str, text: str):
        ...

    @abstractmethod
    def _update_char_info(self, text: str):
        ...

    @abstractmethod
    def _update_location_text(self, text: str):
        ...

    # ── Abstract I/O (implemented by subclasses) ─────────────────

    @abstractmethod
    def print(self, *args, **kwargs):
        ...

    @abstractmethod
    def input(self, prompt=''):
        ...

    @abstractmethod
    def prompt_int(self, prompt, min_val=None, max_val=None):
        ...

    @abstractmethod
    def prompt_str(self, prompt, allow_empty=True):
        ...

    @abstractmethod
    def prompt_yes_no(self, prompt):
        ...

    @abstractmethod
    def show_image(self, category, key):
        ...

    @abstractmethod
    def show_basic_actions(self, location_type):
        ...

    @abstractmethod
    def show_advanced_actions(self):
        ...

    @abstractmethod
    def show_character_actions(self):
        ...

    # ── Shared logic moved from subclasses ───────────────────────

    def prepare_menu(self, iterable):
        items_map = {idx: item for idx, item in enumerate(iterable, 1)}
        items_map_str = '\n'.join(
            f'{idx} - {self._menu_label(name)}'
            for idx, name in items_map.items()
        )
        return items_map, items_map_str

    @staticmethod
    def _menu_label(item):
        if isinstance(item, dict):
            return item.get('name', item.get('code', str(item)))
        return str(item).replace('_', ' ').capitalize()

    def show_location(self, location_data):
        name = location_data.get('name', 'Unknown')
        x = location_data.get('x', '?')
        y = location_data.get('y', '?')
        layer = location_data.get('layer', '?')
        self._update_location_text(f'{name} ({x}, {y}) [{layer}]')

    def show_character_info_panel(self, character):
        level = getattr(character, 'level', 0)
        hp = getattr(character, 'hp', 0)
        max_hp = getattr(character, 'max_hp', 0)
        xp = getattr(character, 'xp', 0)
        max_xp = getattr(character, 'max_xp', 0)
        gold = getattr(character, 'gold', 0)
        name = getattr(character, 'name', '?')
        self._update_char_info(
            f'{name}  Lv.{level}  HP: {hp}/{max_hp}  XP: {xp}/{max_xp}  Gold: {gold}'
        )

    def show_skills(self, character):
        seen = set()
        skill_attrs = []
        for e in [*GatheringSkillEnum, *CraftSkillEnum]:
            if e not in seen:
                seen.add(e)
                skill_attrs.append((e.replace('_', ' ').title(), e))
        lines = []
        for skill_name, skill_code in skill_attrs:
            level = getattr(character, f'{skill_code}_level', 0)
            xp = getattr(character, f'{skill_code}_xp', 0)
            mx = getattr(character, f'{skill_code}_max_xp', 0)
            lines.append(f'{skill_name}: Lv.{level} ({xp}/{mx})')
        self._show_window('Skills', '\n'.join(lines))

    def show_inventory(self, character, item_names):
        inventory = getattr(character, 'inventory', None) or []
        total = sum(s.get('quantity', 0) for s in inventory if s.get('code'))
        slots = sum(1 for s in inventory if s.get('code'))
        max_items = getattr(character, 'inventory_max_items', 0)
        lines = [f'Fill: {total}/{max_items} (slots: {slots})']
        for slot in inventory:
            code = slot.get('code')
            if not code:
                continue
            lines.append(f'  {item_names.get(code, code)} x{slot.get("quantity", 1)}')
        self._show_window('Inventory', '\n'.join(lines))

    def show_equipment(self, character, effect_names, items_data):
        lines = []
        for slot_name in EquipmentSlotsEnum:
            label = re.sub(r'(\d)', r' \1', slot_name.replace('_', ' ')).capitalize()
            code = getattr(character, f'{slot_name}_slot', None)
            if code:
                item = items_data.get(code, {})
                name = item.get('name', code)
                lines.append(f'{label}: {name}')
                for ef in item.get('effects', []) or []:
                    ename = effect_names.get(ef.get('code', ''), ef.get('code', ''))
                    lines.append(f'  {ename}: {ef.get("value", 0)}')
            else:
                lines.append(f'{label}: (empty)')
        self._show_window('Equipment', '\n'.join(lines))

    def show_action_details(self, source):
        details = self._format_action_details(source)
        if details:
            self._output('  ' + '\n  '.join(details))

    def _format_action_details(self, source):
        details = []
        xp = gold = None
        items = None
        if 'xp' in source or 'gold' in source or 'items' in source:
            xp = source.get('xp')
            gold = source.get('gold')
            items = source.get('items')
        elif 'details' in source:
            det = source.get('details', {})
            xp = det.get('xp')
            items = det.get('items')
        elif 'fight' in source:
            fight = source.get('fight', {})
            chars = fight.get('characters', [])
            if chars:
                main = chars[0]
                xp = main.get('xp')
                gold = main.get('gold')
                items = main.get('drops')
        if xp is not None:
            details.append(f'XP: {xp}')
        if gold is not None:
            details.append(f'Gold: {gold}')
        if items:
            items_data = []
            for item in items:
                code = item.get('code', '?')
                qty = item.get('quantity', 1)
                items_data.append(f'{code} x{qty}')
            details.append(f"Items: {', '.join(items_data)}")
        return details

    def show_action_log(self, description):
        self._output(description)

    def show_action_in_progress(self, reason, total_seconds):
        self._output(f'Performing action {reason} ({total_seconds}s)')

    def show_action_countdown(self, seconds_left):
        pass

    def clear_action_countdown(self):
        pass

    def show_action_error(self, message):
        self._output(f'ERROR: {message}')

    def start_batch(self, total_count):
        pass

    def end_batch(self):
        pass

    def show_loading(self):
        pass

    def hide_loading(self):
        pass

    # ── Stats formatting helpers ──────────────────────────────────

    def _format_stats_core(self, character):
        return [
            f'HP: {character.hp} / {character.max_hp}',
            f'Haste: {character.haste}',
            f'Critical Strike: {character.critical_strike}',
            f'Initiative: {character.initiative}',
            f'Threat: {character.threat}',
            f'Prospecting: {character.prospecting}',
            f'Wisdom: {character.wisdom}',
            f'Damage: {character.dmg}%',
        ]

    def _format_stats_attack(self, character):
        return [
            f'Fire: {character.attack_fire}',
            f'Earth: {character.attack_earth}',
            f'Water: {character.attack_water}',
            f'Air: {character.attack_air}',
        ]

    def _format_stats_elemental_damage(self, character):
        return [
            f'Fire: {character.dmg_fire}%',
            f'Earth: {character.dmg_earth}%',
            f'Water: {character.dmg_water}%',
            f'Air: {character.dmg_air}%',
        ]

    def _format_stats_resistance(self, character):
        return [
            f'Fire: {character.res_fire}%',
            f'Earth: {character.res_earth}%',
            f'Water: {character.res_water}%',
            f'Air: {character.res_air}%',
        ]

    def _format_stats_effects(self, character):
        effects = getattr(character, 'effects', None) or []
        if effects:
            return [f'{e.get("code", "?")}: {e.get("value", 0)}' for e in effects]
        return ['(none)']

    def show_stats(self, character):
        lines = [
            f'Level {character.level} ({character.xp} / {character.max_xp})',
            'Core Stats:',
        ]
        for l in self._format_stats_core(character):
            lines.append(f'  {l}')
        lines.append('Attack:')
        for l in self._format_stats_attack(character):
            lines.append(f'  {l}')
        lines.append('Elemental Damage:')
        for l in self._format_stats_elemental_damage(character):
            lines.append(f'  {l}')
        lines.append('Resistance:')
        for l in self._format_stats_resistance(character):
            lines.append(f'  {l}')
        lines.append('Effects:')
        for l in self._format_stats_effects(character):
            lines.append(f'  {l}')
        self._show_window('Stats', '\n'.join(lines))

    def show_account_actions(self):
        pass
