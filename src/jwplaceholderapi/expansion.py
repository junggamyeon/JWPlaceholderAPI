from typing import Optional
from endstone import Player

class PlaceholderExpansion:
    def __init__(self):
        self.registered = False

    def get_identifier(self) -> str:
        raise NotImplementedError()

    def get_author(self) -> str:
        raise NotImplementedError()

    def get_version(self) -> str:
        raise NotImplementedError()

    def on_request(self, player: Optional[Player], params: str) -> Optional[str]:
        raise NotImplementedError()

    def on_register(self) -> None:
        pass

    def on_unregister(self) -> None:
        pass

    def on_player_quit(self, player: Player) -> None:
        pass

    def is_registered(self) -> bool:
        return self.registered
