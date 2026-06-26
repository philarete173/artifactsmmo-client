from base.client import GameClient


class GUIClient(GameClient):
    """GUI front-end for the ArtifactsMMO client.

    Inherits the shared API layer from GameClient and adds GUI-specific
    overrides where terminal I/O (prompts, sys.exit, print) must be
    replaced with widget-based equivalents handled by GUIDisplay.
    """

    def _build_character(self, name):
        """Create a Character object without console-specific output."""
        from base.character import Character
        return Character(name, parent=self, display=self.display)

    def show_current_season(self):
        """Show season info without sys.exit on failure."""
        response = self._get()

        if response.status_code != 200:
            self.display.print('Can\'t reach the server. Please try again later.')
            return

        data = response.json().get('data', {})
        self.display.print(f'Game version: {data.get("version", "?")}.')

        season = data.get('season') or {}
        name = season.get('name', '?')
        number = season.get('number', '?')
        start = season.get('start_date', '?')
        self.display.print(f'Current season: {name} (#{number}), started {start}.')
