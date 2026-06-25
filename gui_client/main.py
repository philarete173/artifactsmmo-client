"""GUI entry point for ArtifactsMMO client using CustomTkinter."""

from gui_client.api import App


if __name__ == '__main__':
    app = App()
    app.mainloop()
