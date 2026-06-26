"""GUI interface classes for ArtifactsMMO client."""

import base64
import io
import re
import threading

import customtkinter as ctk
import requests
from PIL import Image as PILImage, ImageTk

from gui_client.client import GUIClient as GameClient
from base.display import Display
from base.enums import ActionTypeEnum, CharacterSexEnum, ImageCategoryEnum, MapTypesEnum
from base.images import IMAGE_URL_TEMPLATE
from scripts import ScenariosStorage


class GUIDisplay(Display):
    """Routes display output to CustomTkinter widgets."""

    def __init__(self, app):
        self.app = app

    def _output(self, text):
        self.app.log(text)

    def _show_window(self, title, text):
        self.app.show_info_panel(title, text)

    def _update_char_info(self, text):
        self.app.update_character_info(text)

    def _update_location_text(self, text):
        self.app.update_location(text)

    def show_location(self, location_data):
        self.app.current_location_data = location_data
        super().show_location(location_data)
        self.app.after(0, self.app._refresh_action_buttons)
        self.app._load_map_image(location_data.get('skin', ''))
        self.app.update_location_interactions(location_data)

    def show_character_info_panel(self, character):
        self.app.update_character_panel(character)

    def print(self, *args, **kwargs):
        text = ' '.join(str(a) for a in args)
        self.app.log(text)

    def input(self, prompt=''):
        raise NotImplementedError('Use prompt_int / prompt_str instead of raw input()')

    def prompt_int(self, prompt, min_val=None, max_val=None):
        options = self._parse_numbered_options(prompt)
        if options is not None:
            return self._blocking_choice_dialog(prompt, options)
        return self._blocking_input_dialog(prompt, int, min_val, max_val)

    def prompt_str(self, prompt, allow_empty=True):
        return self._blocking_input_dialog(prompt, str, allow_empty=allow_empty)

    def prompt_yes_no(self, prompt):
        return self._blocking_input_dialog(prompt, 'yesno')

    def show_image(self, category, key):
        pass

    def show_action_in_progress(self, reason, total_seconds):
        super().show_action_in_progress(reason, total_seconds)
        self.app.after(0, lambda: self.app._start_action_progress(total_seconds))

    def start_batch(self, total_count):
        self.app.after(0, lambda: self.app._start_batch(total_count))

    def end_batch(self):
        self.app.after(0, self.app._end_batch)

    def show_loading(self):
        self.app.after(0, self.app._show_loading)

    def hide_loading(self):
        self.app.after(0, self.app._hide_loading)

    def show_action_details(self, source):
        self._pending_details = self._format_action_details(source)
        character_data = source.get('character', {}) or {}
        if character_data:
            char = getattr(self.app, 'character', None)
            if char is not None:
                for key in char.CHARACTER_INFO_FIELDS:
                    if key in character_data:
                        setattr(char, key, character_data[key])
                self.show_character_info_panel(char)
            pos = {}
            if 'x' in character_data:
                pos['x'] = character_data['x']
            if 'y' in character_data:
                pos['y'] = character_data['y']
            if 'layer' in character_data:
                pos['layer'] = character_data['layer']
            self.app._on_action_completed(pos)

    def show_action_log(self, description):
        if getattr(self, '_pending_details', None) is not None:
            self._output_combined_log(description)
            self._pending_details = None
            return

        def _deferred():
            self._log_deferred = None
            if getattr(self, '_pending_details', None) is not None:
                self._output_combined_log(description)
                self._pending_details = None
            else:
                self._output(description)

        self._log_deferred = _deferred
        self.app.after(50, _deferred)

    def _output_combined_log(self, description):
        parts = []
        if getattr(self.app, '_batch_mode', False):
            done = self.app._batch_done + 1
            parts.append(f'[{done}/{self.app._batch_count}]')
        parts.append(description)
        d = getattr(self, '_pending_details', None)
        if d:
            parts.append('  ' + '; '.join(d))
        self._output(' '.join(parts))

    @staticmethod
    def _parse_numbered_options(prompt):
        lines = prompt.split('\n')
        options = []
        for line in lines:
            line = line.strip()
            m = re.match(r'^(\d+)\s*[-–—]\s*(.+)$', line)
            if m:
                options.append((int(m.group(1)), m.group(2)))
        if options:
            return options
        return None

    def _blocking_choice_dialog(self, prompt, options):
        event = threading.Event()
        result = [None]

        def on_choice(idx, label):
            result[0] = idx
            event.set()

        def on_cancel():
            result[0] = None
            event.set()

        self.app.after(0, lambda: self.app._show_options_buttons(
            prompt, options, on_choice, on_cancel))
        event.wait()
        return result[0]

    def _blocking_input_dialog(self, prompt, expected_type, min_val=None, max_val=None, allow_empty=True):
        event = threading.Event()
        result = [None]

        def on_choice(idx, label):
            result[0] = idx
            event.set()

        def on_int(value):
            if min_val is not None and value < min_val:
                self.app.log(f'Value must be >= {min_val}')
                return
            if max_val is not None and value > max_val:
                self.app.log(f'Value must be <= {max_val}')
                return
            result[0] = value
            event.set()

        def on_yesno(value):
            result[0] = value
            event.set()

        def on_str(value):
            if value is not None and not value.strip():
                if not allow_empty:
                    self.app.log('Input cannot be empty.')
                    return
                value = None
            result[0] = value.strip() if value else None
            event.set()

        def on_cancel():
            result[0] = None
            event.set()

        if expected_type is int:
            options = self._parse_numbered_options(prompt)
            if options:
                self.app.after(0, lambda: self.app._show_options_buttons(
                    prompt, options, on_choice, on_cancel))
            else:
                self.app.after(0, lambda: self.app._show_count_buttons(
                    prompt, min_val or 1, max_val or 99, on_int, on_cancel))
        elif expected_type is bool or expected_type == 'yesno':
            self.app.after(0, lambda: self.app._show_yes_no_buttons(
                prompt, on_yesno, on_cancel))
        else:
            self.app.after(0, lambda: self.app._show_text_input(
                prompt, on_str, on_cancel))

        event.wait()
        return result[0]

    def show_basic_actions(self, location_type):
        pass

    def show_advanced_actions(self):
        pass

    def show_character_actions(self):
        pass

    def show_account_actions(self):
        pass


class App(ctk.CTk):
    """Main CustomTkinter application window."""

    def __init__(self):
        super().__init__(className='ArtifactsMMO')

        self.title('ArtifactsMMO Client')
        self.geometry('1280x720')
        self.minsize(1280, 720)

        ctk.set_appearance_mode('dark')
        ctk.set_default_color_theme('green')

        self.display = GUIDisplay(self)
        self.client = GameClient(display=self.display)
        self.character = None
        self.current_location_data = None

        self.container = ctk.CTkFrame(self)
        self.container.pack(fill='both', expand=True)

        self._set_window_icon()

        threading.Thread(target=self._init_flow, daemon=True).start()

    def _set_window_icon(self):
        try:
            r = requests.get('https://play.artifactsmmo.com/favicon.png', timeout=5)
            img = PILImage.open(io.BytesIO(r.content))
            photo = ImageTk.PhotoImage(img)
            self.iconphoto(True, photo)
            self._icon_photo = photo
        except Exception:
            pass

    # ─────────────────────────── flow ───────────────────────────

    def _init_flow(self):
        self.log('Starting client...')
        try:
            self.client.show_current_season()
        except SystemExit:
            self.log('Server unreachable. Check your connection.')
            return

        characters = self.client.get_my_characters()
        if characters:
            self._show_account_menu(characters)
        else:
            self._check_token_and_login()

    def _check_token_and_login(self):
        token = self.client.config.get(
            self.client.CONFIG_SECTION,
            self.client.CONFIG_TOKEN_KEY,
            fallback=''
        )
        if token:
            self.log('Token present but no characters — trying login.')
        self._show_login_form()

    # ────────────────────── login screen ────────────────────────

    def _show_login_form(self):
        self.after(0, self._build_login_ui)

    def _build_login_ui(self):
        self._clear_container()

        frame = ctk.CTkFrame(self.container)
        frame.place(relx=0.5, rely=0.4, anchor='center')

        ctk.CTkLabel(frame, text='Login', font=('', 20, 'bold')).grid(
            row=0, column=0, columnspan=2, pady=(10, 20)
        )

        ctk.CTkLabel(frame, text='Email / Username:').grid(row=1, column=0, padx=10, pady=5, sticky='e')
        email_entry = ctk.CTkEntry(frame, width=200)
        email_entry.grid(row=1, column=1, padx=10, pady=5)

        ctk.CTkLabel(frame, text='Password:').grid(row=2, column=0, padx=10, pady=5, sticky='e')
        pwd_entry = ctk.CTkEntry(frame, width=200, show='*')
        pwd_entry.grid(row=2, column=1, padx=10, pady=5)

        save_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(frame, text='Save token to config', variable=save_var).grid(
            row=3, column=0, columnspan=2, pady=10
        )

        status = ctk.CTkLabel(frame, text='', text_color='red')
        status.grid(row=4, column=0, columnspan=2, pady=2)

        def do_login():
            email = email_entry.get().strip()
            password = pwd_entry.get()
            if not email or not password:
                status.configure(text='Please fill in both fields.')
                return
            threading.Thread(
                target=lambda: self._perform_login(email, password, save_var.get(), status),
                daemon=True
            ).start()

        ctk.CTkButton(frame, text='Login', command=do_login).grid(
            row=5, column=0, columnspan=2, pady=(10, 5)
        )
        ctk.CTkButton(frame, text='Quit', command=self.destroy).grid(
            row=6, column=0, columnspan=2, pady=5
        )

        email_entry.focus()

    def _perform_login(self, email, password, save, status_label):
        credentials = base64.b64encode(
            f'{email}:{password}'.encode('utf-8')
        ).decode('ascii')

        response = self.client._do_request(
            method='post', url='/token',
            extra_headers={'Authorization': f'Basic {credentials}'},
        )

        def ok():
            if save:
                self.client.set_token(token)
            else:
                self.client._apply_token(token)
            self.log('Login successful.')
            self._after_login()

        def fail(msg):
            self.after(0, lambda: status_label.configure(text=msg))

        if response.status_code == 200:
            token = response.json().get('token')
            if not token:
                fail('Server returned empty token.')
                return
            self.after(0, ok)
        else:
            msg, code = self.client._extract_error(response)
            fail(f'Login failed: {msg} ({code})')

    def _after_login(self):
        characters = self.client.get_my_characters()
        if characters:
            self._show_account_menu(characters)
        else:
            self._show_account_menu([])

    # ───────────────────── account menu ─────────────────────────

    def _show_account_menu(self, characters):
        self.after(0, lambda: self._build_account_menu(characters))

    def _build_account_menu(self, characters):
        self._clear_container()

        frame = ctk.CTkFrame(self.container)
        frame.place(relx=0.5, rely=0.5, anchor='center')

        ctk.CTkLabel(frame, text='Account', font=('', 20, 'bold')).grid(
            row=0, column=0, columnspan=2, pady=(10, 15)
        )

        if characters:
            ctk.CTkLabel(frame, text='Select character:', font=('', 14)).grid(
                row=1, column=0, columnspan=2, pady=5
            )
            for i, ch in enumerate(characters):
                name = ch.get('name', '?')
                btn = ctk.CTkButton(
                    frame, text=name, width=250,
                    command=lambda n=name: self._select_character(n)
                )
                btn.grid(row=2 + i, column=0, columnspan=2, padx=20, pady=3)
            offset = 2 + len(characters)
        else:
            ctk.CTkLabel(frame, text='(no characters on this account)', text_color='gray').grid(
                row=1, column=0, columnspan=2, pady=5
            )
            offset = 2

        ctk.CTkButton(frame, text='Show account details', width=250,
                       command=self._show_account_details).grid(
            row=offset, column=0, columnspan=2, pady=(15, 3))
        ctk.CTkButton(frame, text='Create character', width=250,
                       command=self._show_create_character_dialog).grid(
            row=offset + 1, column=0, columnspan=2, pady=3)
        ctk.CTkButton(frame, text='Login with different account', width=250,
                       command=self._show_login_form).grid(
            row=offset + 2, column=0, columnspan=2, pady=3)
        ctk.CTkButton(frame, text='Quit', width=250,
                       command=self.destroy).grid(
            row=offset + 3, column=0, columnspan=2, pady=3)

    def _select_character(self, name):
        self.log(f'Loading character {name}...')

        def load():
            self.client.character = self.client._build_character(name)
            self.client.scenarios_storage = ScenariosStorage(self.client.character)
            if not self.client.character:
                self.log('Failed to load character.')
                return
            self.character = self.client.character
            self.after(0, self._build_game_ui)
            self._load_char_image(getattr(self.character, 'skin', ''))
            self.client.display.show_character_info_panel(self.character)
            loc = self.client.get_location_data(
                self.character.layer, self.character.x, self.character.y
            )
            self.client.display.show_location(loc)
            self.after(0, self._refresh_all_tabs)
            self.log(f'Character {self.character.name} ready.')

        threading.Thread(target=load, daemon=True).start()

    def _show_account_details(self):
        def fetch():
            data = self.client.get_account_details()
            if not data:
                self.log('Failed to get account details.')
                return
            lines = [f'{k}: {v}' for k, v in data.items()]
            self.show_info_panel('Account details', '\n'.join(lines))
        threading.Thread(target=fetch, daemon=True).start()

    def _show_create_character_dialog(self):
        def _show():
            win = ctk.CTkToplevel(self)
            win.title('Create character')
            win.geometry('350x200')
            win.resizable(False, False)

            ctk.CTkLabel(win, text='New character name:', font=('', 13)).pack(pady=(15, 5))
            name_entry = ctk.CTkEntry(win, width=200)
            name_entry.pack(pady=5)

            sex_var = ctk.StringVar(value=CharacterSexEnum.MALE)
            sex_frame = ctk.CTkFrame(win)
            sex_frame.pack(pady=10)
            ctk.CTkLabel(sex_frame, text='Sex:').pack(side='left', padx=5)
            for label, val in [
                ('Male', CharacterSexEnum.MALE),
                ('Female', CharacterSexEnum.FEMALE),
                ('Random', CharacterSexEnum.RANDOM),
            ]:
                ctk.CTkRadioButton(sex_frame, text=label, variable=sex_var, value=val).pack(side='left', padx=5)

            status = ctk.CTkLabel(win, text='', text_color='red')
            status.pack()

            def do_create():
                name = name_entry.get().strip()
                if not re.match(r'^[a-zA-Z0-9_-]{3,12}$', name):
                    status.configure(text='Name: 3-12 chars, a-z, 0-9, _, -')
                    return
                sex = sex_var.get()
                threading.Thread(target=lambda: self._create_and_refresh(name, sex, win), daemon=True).start()

            ctk.CTkButton(win, text='Create', command=do_create).pack(pady=10)
            name_entry.focus()

        self.after(0, _show)

    def _create_and_refresh(self, name, sex, dialog):
        ok = self.client.create_character(name, sex)
        if ok:
            self.log(f'Character {name} created.')
            dialog.after(0, dialog.destroy)
            chars = self.client.get_my_characters()
            self._show_account_menu(chars)
        else:
            self.log('Failed to create character.')

    # ──────────────────── game interface ────────────────────────

    def _build_game_ui(self):
        self._clear_container()

        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_columnconfigure(1, weight=2)
        self.container.grid_rowconfigure(1, weight=1)

        # Left panel: character info + info display + character buttons
        self.char_frame = ctk.CTkFrame(self.container)
        self.char_frame.grid(row=0, column=0, rowspan=3, sticky='nsew', padx=5, pady=5)
        self.char_frame.grid_propagate(False)
        self.char_frame.pack_propagate(False)

        # Top row: character skin + name/level + bars
        top_row = ctk.CTkFrame(self.char_frame)
        top_row.pack(fill='x', padx=5, pady=(10, 5))

        self.char_image_label = ctk.CTkLabel(top_row, text='')
        self.char_image_label.pack(side='left', padx=(0, 10))

        self.char_stats_col = ctk.CTkFrame(top_row)
        self.char_stats_col.pack(side='left', fill='both', expand=True)
        self.char_stats_col.bind('<Configure>', lambda e: self._resize_char_image())

        name_frame = ctk.CTkFrame(self.char_stats_col)
        name_frame.pack(fill='x', pady=(0, 5))
        self.char_name_label = ctk.CTkLabel(name_frame, text='', font=('', 16, 'bold'))
        self.char_name_label.pack(side='left')
        self.char_level_label = ctk.CTkLabel(name_frame, text='', font=('', 13))
        self.char_level_label.pack(side='right')

        hp_frame = ctk.CTkFrame(self.char_stats_col)
        hp_frame.pack(fill='x', pady=2)
        self.hp_progress = ctk.CTkProgressBar(
            hp_frame, orientation='horizontal',
            fg_color='#442222', progress_color='#e74c3c', height=18,
        )
        self.hp_progress.pack(fill='x')
        self.hp_label = ctk.CTkLabel(
            hp_frame, text='', font=('', 9, 'bold'),
            text_color='white',
        )
        self.hp_label.pack(anchor='center')

        xp_frame = ctk.CTkFrame(self.char_stats_col)
        xp_frame.pack(fill='x', pady=2)
        self.xp_progress = ctk.CTkProgressBar(
            xp_frame, orientation='horizontal',
            fg_color='#224422', progress_color='#2ecc71', height=18,
        )
        self.xp_progress.pack(fill='x')
        self.xp_label = ctk.CTkLabel(
            xp_frame, text='', font=('', 9, 'bold'),
            text_color='white',
        )
        self.xp_label.pack(anchor='center')

        # Location
        ctk.CTkLabel(self.char_frame, text='Location', font=('', 12, 'bold')).pack(
            anchor='sw', padx=5, pady=(10, 2)
        )
        self.loc_row = ctk.CTkFrame(self.char_frame, fg_color='transparent')
        self.loc_row.pack(fill='x', padx=5, pady=2)
        self.loc_row.bind('<Configure>', lambda e: self._resize_location_image())

        self.map_image_label = ctk.CTkLabel(self.loc_row, text='')
        self.map_image_label.pack(side='left')

        self.loc_info_frame = ctk.CTkFrame(self.loc_row, fg_color='transparent')
        self.loc_info_frame.pack(side='left', fill='x', expand=True, padx=(8, 0))

        self.loc_name_label = ctk.CTkLabel(
            self.loc_info_frame, text='', font=('', 12, 'bold'), justify='left', anchor='w',
        )
        self.loc_name_label.pack(fill='x')
        self.loc_interactions_label = ctk.CTkLabel(
            self.loc_info_frame, text='', font=('', 10), justify='left', anchor='w',
        )
        self.loc_interactions_label.pack(fill='x')

        # Tabbed info panel (stats, skills, inventory, equipment)
        self.info_tabview = ctk.CTkTabview(self.char_frame)
        self.info_tabview.pack(fill='both', expand=True, padx=5, pady=5)

        self.tab_textboxes = {}
        for name in ('Stats', 'Skills', 'Inventory', 'Equipment'):
            tab = self.info_tabview.add(name)
            textbox = ctk.CTkTextbox(tab, wrap='word', state='disabled')
            textbox.pack(fill='both', expand=True)
            textbox.grid_propagate(False)
            self.tab_textboxes[name] = textbox
        self.info_tabview.set('Stats')

        # Back to account button
        ctk.CTkButton(
            self.char_frame, text='← Back to account', command=self._back_to_account
        ).pack(side='bottom', fill='x', padx=5, pady=5)

        # Log area (right side)
        self.log_frame = ctk.CTkFrame(self.container)
        self.log_frame.grid(row=0, column=1, rowspan=2, sticky='nsew', padx=5, pady=(5, 0))
        self.log_frame.grid_rowconfigure(0, weight=1)
        self.log_frame.grid_columnconfigure(0, weight=1)

        self.log_text = ctk.CTkTextbox(self.log_frame, wrap='word', state='disabled')
        self.log_text.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)

        ctk.CTkLabel(self.log_frame, text='Action Log', font=('', 10)).grid(
            row=1, column=0, pady=(0, 5)
        )

        # Action buttons (right side, bottom)
        self.action_container = ctk.CTkFrame(self.container)
        self.action_container.grid(row=2, column=1, sticky='ew', padx=5, pady=(5, 5))
        self.action_container.grid_columnconfigure(0, weight=1)

        self.loading_label = ctk.CTkLabel(
            self.action_container, text='Waiting for response...',
            font=('', 13, 'italic'), text_color='gray',
        )
        self.loading_label.grid(row=0, column=0, sticky='ew')
        self.loading_label.grid_remove()

        self.button_frame = ctk.CTkFrame(self.action_container)
        self.button_frame.grid(row=0, column=0, sticky='ew')
        self._refresh_action_buttons()

        self.action_progress = ctk.CTkProgressBar(
            self.action_container, orientation='horizontal',
            height=28, mode='determinate',
            progress_color='#3498db',
        )
        self.action_progress.grid(row=0, column=0, sticky='ew')
        self.action_progress.grid_remove()

    # ──────────────── tab refresh methods ────────────────────────

    def _set_tab_text(self, tab_name, text):
        textbox = self.tab_textboxes.get(tab_name)
        if textbox is None:
            return
        textbox.configure(state='normal')
        textbox.delete('0.0', 'end')
        textbox.insert('0.0', text)
        textbox.configure(state='disabled')

    def _refresh_all_tabs(self):
        if not self.character:
            return
        self._refresh_stats_tab()
        self._refresh_skills_tab()
        threading.Thread(target=self._refresh_inventory_tab, daemon=True).start()
        threading.Thread(target=self._refresh_equipment_tab, daemon=True).start()

    def _refresh_stats_tab(self):
        c = self.character
        lines = [
            f'Level {c.level} ({c.xp} / {c.max_xp})',
            '',
            'Core Stats:',
            f'  HP: {c.hp} / {c.max_hp}',
            f'  Haste: {c.haste}',
            f'  Critical Strike: {c.critical_strike}',
            f'  Initiative: {c.initiative}',
            f'  Threat: {c.threat}',
            f'  Prospecting: {c.prospecting}',
            f'  Wisdom: {c.wisdom}',
            f'  Damage: {c.dmg}%',
            '',
            'Attack:',
            f'  Fire: {c.attack_fire}',
            f'  Earth: {c.attack_earth}',
            f'  Water: {c.attack_water}',
            f'  Air: {c.attack_air}',
            '',
            'Elemental Damage:',
            f'  Fire: {c.dmg_fire}%',
            f'  Earth: {c.dmg_earth}%',
            f'  Water: {c.dmg_water}%',
            f'  Air: {c.dmg_air}%',
            '',
            'Resistance:',
            f'  Fire: {c.res_fire}%',
            f'  Earth: {c.res_earth}%',
            f'  Water: {c.res_water}%',
            f'  Air: {c.res_air}%',
            '',
            'Effects:',
        ]
        effects = getattr(c, 'effects', None) or []
        if effects:
            for e in effects:
                lines.append(f'  {e.get("code", "?")}: {e.get("value", 0)}')
        else:
            lines.append('  (none)')
        self.after(0, lambda: self._set_tab_text('Stats', '\n'.join(lines)))

    def _refresh_skills_tab(self):
        c = self.character
        from base.enums import GatheringSkillEnum, CraftSkillEnum
        lines = []
        for skill_list, label in [(GatheringSkillEnum, 'Gathering'), (CraftSkillEnum, 'Crafting')]:
            lines.append(f'{label}:')
            for skill_code in skill_list:
                level = getattr(c, f'{skill_code}_level', 0)
                xp = getattr(c, f'{skill_code}_xp', 0)
                mx = getattr(c, f'{skill_code}_max_xp', 0)
                name = skill_code.replace('_', ' ').title()
                lines.append(f'  {name}: Lv.{level} ({xp}/{mx})')
            lines.append('')
        self.after(0, lambda: self._set_tab_text('Skills', '\n'.join(lines)))

    def _refresh_inventory_tab(self):
        if not self.character:
            return
        inventory = getattr(self.character, 'inventory', None) or []
        total = sum(s.get('quantity', 0) for s in inventory if s.get('code'))
        slots = sum(1 for s in inventory if s.get('code'))
        max_items = getattr(self.character, 'inventory_max_items', 0)
        unique_codes = set(s['code'] for s in inventory if s.get('code'))

        item_names = {}
        for code in unique_codes:
            item = self.client.get_item(code)
            item_names[code] = (item or {}).get('name', code)

        lines = [f'Fill: {total}/{max_items} (slots: {slots})']
        for slot in inventory:
            code = slot.get('code')
            if not code:
                continue
            lines.append(f'  {item_names.get(code, code)} x{slot.get("quantity", 1)}')
        self.after(0, lambda: self._set_tab_text('Inventory', '\n'.join(lines)))

    def _refresh_equipment_tab(self):
        if not self.character:
            return
        effects_data = self.client.get_effects()
        effect_names = {e['code']: e['name'] for e in effects_data if 'code' in e}

        unique_codes = set()
        for slot_name in ('weapon', 'shield', 'helmet', 'body_armor', 'leg_armor', 'boots',
                          'ring1', 'ring2', 'amulet', 'artifact1', 'artifact2', 'artifact3',
                          'rune', 'utility1', 'utility2', 'bag'):
            item_code = getattr(self.character, f'{slot_name}_slot', None)
            if item_code:
                unique_codes.add(item_code)

        from base.enums import EquipmentSlotsEnum
        items_data = {}
        for code in unique_codes:
            items_data[code] = self.client.get_item(code)

        lines = []
        for slot_name in EquipmentSlotsEnum:
            label = re.sub(r'(\d)', r' \1', slot_name.replace('_', ' ')).capitalize()
            code = getattr(self.character, f'{slot_name}_slot', None)
            if code:
                item = items_data.get(code, {})
                name = item.get('name', code)
                lines.append(f'{label}: {name}')
                for ef in item.get('effects', []) or []:
                    ename = effect_names.get(ef.get('code', ''), ef.get('code', ''))
                    lines.append(f'  {ename}: {ef.get("value", 0)}')
            else:
                lines.append(f'{label}: (empty)')
        self.after(0, lambda: self._set_tab_text('Equipment', '\n'.join(lines)))

    # ──────────────────── choice button helpers ─────────────────

    def _build_buttons(self, choices):
        """choices: list of (label, callback) tuples."""
        for w in self.button_frame.winfo_children():
            w.destroy()
        if not choices:
            return
        cols = min(5, len(choices))
        for i, (label, callback) in enumerate(choices):
            btn = ctk.CTkButton(
                self.button_frame, text=label,
                command=callback
            )
            btn.grid(row=i // cols, column=i % cols, padx=2, pady=2, sticky='ew')
        for col_n in range(cols):
            self.button_frame.grid_columnconfigure(col_n, weight=1)

    def _show_count_buttons(self, prompt, min_val, max_val, on_confirm, on_cancel):
        self.log(f'{prompt} (choose a number)')
        presets = []
        for v in [1, 2, 5, 10, 20, 50]:
            if min_val <= v <= max_val:
                presets.append((str(v), lambda v=v: on_confirm(v)))
        if presets:
            presets.append(('Custom', lambda: self._show_custom_count(
                prompt, min_val, max_val, on_confirm, on_cancel)))
        presets.append(('Cancel', on_cancel))
        self._build_buttons(presets)

    def _show_options_buttons(self, prompt, options, on_choice, on_cancel):
        """options: list of (index, label) tuples."""
        self.log(prompt.split('\n')[0] if prompt else '')
        choices = [(label, lambda idx=idx: on_choice(idx, label))
                   for idx, label in options]
        choices.append(('← Back', on_cancel))
        self._build_buttons(choices)

    def _show_custom_count(self, prompt, min_val, max_val, on_confirm, on_cancel):
        self._build_buttons([])
        entry = ctk.CTkEntry(self.button_frame, width=100)
        entry.grid(row=0, column=0, padx=5, pady=5)
        entry.insert(0, str(min_val or 1))

        def submit():
            try:
                v = int(entry.get().strip())
                if v < min_val:
                    self.log(f'Value must be >= {min_val}')
                    return
                if v > max_val:
                    self.log(f'Value must be <= {max_val}')
                    return
                on_confirm(v)
            except ValueError:
                self.log('Please enter a whole number.')

        submit_btn = ctk.CTkButton(self.button_frame, text='OK', command=submit)
        submit_btn.grid(row=0, column=1, padx=5, pady=5)
        ctk.CTkButton(self.button_frame, text='Cancel', command=on_cancel).grid(
            row=0, column=2, padx=5, pady=5)
        entry.focus()
        entry.bind('<Return>', lambda e: submit())

    def _show_yes_no_buttons(self, prompt, on_confirm, on_cancel):
        self.log(prompt)
        self._build_buttons([
            ('Yes', lambda: on_confirm(True)),
            ('No', lambda: on_confirm(False)),
            ('Cancel', on_cancel),
        ])

    def _show_text_input(self, prompt, on_confirm, on_cancel):
        self.log(prompt)
        self._build_buttons([])
        entry = ctk.CTkEntry(self.button_frame, width=200)
        entry.grid(row=0, column=0, padx=5, pady=5)

        def submit():
            on_confirm(entry.get())

        ctk.CTkButton(self.button_frame, text='OK', command=submit).grid(
            row=0, column=1, padx=5, pady=5)
        ctk.CTkButton(self.button_frame, text='Cancel', command=on_cancel).grid(
            row=0, column=2, padx=5, pady=5)
        entry.focus()
        entry.bind('<Return>', lambda e: submit())

    # ──────────────────── default action buttons ─────────────────

    def _get_location_actions(self):
        data = self.current_location_data
        if not data:
            return []
        content = (
            (data.get('interactions') or {}).get('content')
            or data.get('content')
            or {}
        )
        location_type = content.get('type', None)
        actions = list(ActionTypeEnum.LOCATION_ACTIONS_MAP.get(location_type, []))
        if (data.get('interactions') or {}).get('transition'):
            actions.append(ActionTypeEnum.TRANSITION)
        seen = set()
        result = []
        for a in actions + list(ActionTypeEnum.ADVANCED_ACTIONS):
            if a not in seen:
                seen.add(a)
                result.append(a)
        return result

    def _on_action(self, action):
        if not self.character:
            self.log('No character selected.')
            return

        if action == ActionTypeEnum.MOVE:
            self._enter_move_location_type()
            return

        method = self.client.main_menu_map.get(action)
        if method:
            threading.Thread(target=method, daemon=True).start()
        else:
            self.log(f'Action {action} not implemented yet.')

    def _refresh_action_buttons(self):
        actions = self._get_location_actions()
        choices = []
        for a in actions:
            label = a.replace('_', ' ').title()
            choices.append((label, lambda a=a: self._on_action(a)))
        self._build_buttons(choices)

    def _show_loading(self):
        if not hasattr(self, 'loading_label') or not self.loading_label.winfo_exists():
            return
        self.button_frame.grid_remove()
        self.action_progress.grid_remove()
        self.loading_label.grid()

    def _hide_loading(self):
        if not hasattr(self, 'loading_label') or not self.loading_label.winfo_exists():
            return
        self.loading_label.grid_remove()
        if not getattr(self, '_batch_mode', False):
            self.button_frame.grid()

    def _start_action_progress(self, total_seconds):
        if not hasattr(self, 'action_progress') or not self.action_progress.winfo_exists():
            return
        if not getattr(self, '_batch_mode', False):
            self.button_frame.grid_remove()
        self._action_total = total_seconds
        self.action_progress.set(0)
        self.action_progress.grid()
        self._start_action_timer()

    def _tick_action_progress(self):
        if not hasattr(self, 'action_progress') or not self.action_progress.winfo_exists():
            return
        self._action_elapsed += 1
        pct = min(1.0, self._action_elapsed / max(1, self._action_total))
        self.action_progress.set(pct)
        if pct < 1.0:
            self.after(1000, self._tick_action_progress)

    def _finish_action_progress(self):
        if not hasattr(self, 'action_progress') or not self.action_progress.winfo_exists():
            return
        self.action_progress.set(1.0)
        self.action_progress.grid_remove()
        if getattr(self, '_batch_mode', False):
            self._batch_done += 1
            if self._batch_done >= self._batch_count:
                return
            self.action_progress.grid()
            self.action_progress.set(0)
            self._start_action_timer()
            return
        self.button_frame.grid()
        self._refresh_action_buttons()

    def _on_action_completed(self, new_position=None):
        self.after(0, self._finish_action_progress)
        self.after(0, self._refresh_all_tabs)
        if new_position and not getattr(self, '_batch_mode', False):
            threading.Thread(
                target=self._refresh_location_data,
                args=(new_position,),
                daemon=True,
            ).start()

    def _start_batch(self, total_count):
        self._batch_mode = True
        self._batch_count = total_count
        self._batch_done = 0
        self.button_frame.grid_remove()
        self.log(f'Starting {total_count} iterations...')

    def _end_batch(self):
        self._batch_mode = False
        self.action_progress.grid_remove()
        self.button_frame.grid()
        self._refresh_action_buttons()
        self.after(0, self._refresh_all_tabs)
        if hasattr(self, 'character') and self.character:
            threading.Thread(target=self._refresh_location_data, args=({},), daemon=True).start()

    def _start_action_timer(self):
        if not hasattr(self, 'action_progress') or not self.action_progress.winfo_exists():
            return
        self._action_elapsed = 0
        self.action_progress.set(0)
        self.action_progress.grid()
        self._tick_action_progress()

    def _refresh_location_data(self, new_position):
        layer = new_position.get('layer', '')
        x = new_position.get('x', 0)
        y = new_position.get('y', 0)
        loc = self.client.get_location_data(layer, x, y)
        self.client.display.show_location(loc)

    # ──────────────────── move flow ─────────────────────────────

    def _enter_move_location_type(self):
        layer = getattr(self.character, 'layer', '')
        maps = self.client.get_maps_data(layer=layer)
        available_types = sorted(set(
            ((m.get('interactions') or {}).get('content') or {}).get('type', '')
            for m in maps
        ))
        available_types = [t for t in available_types if t]
        choices = [(t.replace('_', ' ').title(), lambda t=t: self._enter_move_location(t))
                   for t in available_types]
        choices.append(('Cancel', self._refresh_action_buttons))
        self._build_buttons(choices)

    def _enter_move_location(self, location_type):
        layer = getattr(self.character, 'layer', '')
        maps = self.client.get_maps_data(content_type=location_type, layer=layer)
        if not maps:
            self.log(f'No {location_type} locations found.')
            self._refresh_action_buttons()
            return
        choices = []
        for m in maps:
            code = ((m.get('interactions') or {}).get('content') or {}).get('code', '')
            map_name = m.get('name', code)
            resource_name = code.replace('_', ' ').title() if code else ''
            label = f'{map_name} ({resource_name}) ({m["x"]}, {m["y"]})'
            choices.append((label, lambda x=m['x'], y=m['y']: self._execute_move(x, y)))
        choices.append(('← Back', self._enter_move_location_type))
        self._build_buttons(choices)

    def _execute_move(self, x, y):
        self.log(f'Moving to ({x}, {y})...')
        self._refresh_action_buttons()
        threading.Thread(target=lambda: self.character.move(x=x, y=y), daemon=True).start()

    # ────────────────────── back to account ─────────────────────

    def _back_to_account(self):
        self.character = None
        self.client.character = None

        def load():
            chars = self.client.get_my_characters()
            self._show_account_menu(chars)

        threading.Thread(target=load, daemon=True).start()

    # ────────────────────── helpers ─────────────────────────────

    def _clear_container(self):
        for w in self.container.winfo_children():
            w.destroy()

    def update_character_info(self, text):
        def _set():
            if hasattr(self, 'char_info') and self.char_info.winfo_exists():
                self.char_info.configure(text=text)
        self.after(0, _set)

    def update_character_panel(self, character):
        def _set():
            if not hasattr(self, 'char_name_label') or not self.char_name_label.winfo_exists():
                return
            name = getattr(character, 'name', '?')
            level = getattr(character, 'level', 0)
            self.char_name_label.configure(text=name)
            self.char_level_label.configure(text=f'Lv.{level}')

            hp = getattr(character, 'hp', 0)
            max_hp = getattr(character, 'max_hp', 1)
            hp_ratio = max(0, min(1, hp / max_hp))
            self.hp_progress.set(hp_ratio)
            self.hp_label.configure(text=f'{hp}/{max_hp}')

            xp = getattr(character, 'xp', 0)
            max_xp = getattr(character, 'max_xp', 1)
            xp_ratio = max(0, min(1, xp / max_xp))
            self.xp_progress.set(xp_ratio)
            self.xp_label.configure(text=f'{xp}/{max_xp}')

        self.after(0, _set)

    def update_location(self, text):
        def _set():
            if hasattr(self, 'loc_name_label') and self.loc_name_label.winfo_exists():
                self.loc_name_label.configure(text=text)
        self.after(0, _set)

    def update_location_interactions(self, location_data):
        def _set():
            if not hasattr(self, 'loc_interactions_label') or not self.loc_interactions_label.winfo_exists():
                return
            content = (
                (location_data.get('interactions') or {}).get('content')
                or location_data.get('content')
                or {}
            )
            lines = []
            if content.get('type'):
                ctype = content['type'].replace('_', ' ').title()
                lines.append(f'Type: {ctype}')
            if content.get('code'):
                cname = content['code'].replace('_', ' ').title()
                lines.append(f'{cname}')
            self.loc_interactions_label.configure(text='\n'.join(lines))
        self.after(0, _set)

    def show_info_panel(self, title, text):
        self.log(f'--- {title} ---\n{text}')

    def log(self, text):
        def _append():
            if not hasattr(self, 'log_text') or not self.log_text.winfo_exists():
                return
            self.log_text.configure(state='normal')
            self.log_text.insert('end', text + '\n')
            self.log_text.see('end')
            self.log_text.configure(state='disabled')
        self.after(0, _append)

    # ────────────────────── image helpers ────────────────────────

    def _load_ctk_image(self, category, key, size):
        try:
            url = IMAGE_URL_TEMPLATE.format(category=category, key=key)
            r = requests.get(url, timeout=5)
            r.raise_for_status()
            pil = PILImage.open(io.BytesIO(r.content))
            return ctk.CTkImage(light_image=pil, dark_image=pil, size=size)
        except Exception:
            return None

    def _load_char_image(self, skin):
        if not skin:
            return

        def load():
            img = self._load_ctk_image(ImageCategoryEnum.CHARACTERS, skin, (1, 1))
            if img is None:
                return

            def set_img():
                if hasattr(self, 'char_image_label') and self.char_image_label.winfo_exists():
                    self.char_ctk_image = img
                    self._resize_char_image()
            self.after(0, set_img)

        threading.Thread(target=load, daemon=True).start()

    def _resize_char_image(self):
        if hasattr(self, '_char_resize_after'):
            self.after_cancel(self._char_resize_after)
        self._char_resize_after = self.after(50, self._do_resize_char_image)

    def _do_resize_char_image(self):
        if not hasattr(self, 'char_ctk_image') or self.char_ctk_image is None:
            return
        if not hasattr(self, 'char_stats_col') or not self.char_stats_col.winfo_exists():
            return
        h = self.char_stats_col.winfo_height()
        if h < 10:
            return
        w = int(h * 0.8)
        self.char_ctk_image.configure(size=(w, h))
        self.char_image_label.configure(image=self.char_ctk_image)

    def _load_map_image(self, skin):
        if not skin:
            return

        def load():
            img = self._load_ctk_image(ImageCategoryEnum.MAPS, skin, (1, 1))
            if img is None:
                return

            def set_img():
                if hasattr(self, 'map_image_label') and self.map_image_label.winfo_exists():
                    self.map_ctk_image = img
                    self._resize_location_image()
            self.after(0, set_img)

        threading.Thread(target=load, daemon=True).start()

    def _resize_location_image(self):
        if hasattr(self, '_loc_resize_after'):
            self.after_cancel(self._loc_resize_after)
        self._loc_resize_after = self.after(50, self._do_resize_location_image)

    def _do_resize_location_image(self):
        if not hasattr(self, 'map_ctk_image') or self.map_ctk_image is None:
            return
        if not hasattr(self, 'loc_row') or not self.loc_row.winfo_exists():
            return
        w = int(self.loc_row.winfo_width() / 2)
        if w < 20:
            return
        h = int(w * 0.75)
        self.map_ctk_image.configure(size=(w, h))
        self.map_image_label.configure(image=self.map_ctk_image)
