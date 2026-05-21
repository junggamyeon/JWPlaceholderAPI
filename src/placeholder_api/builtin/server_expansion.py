from typing import Optional
from endstone import Player, Server
from placeholder_api.expansion import PlaceholderExpansion

class ServerExpansion(PlaceholderExpansion):
    def __init__(self, server: Server):
        super().__init__()
        self.server = server

    def get_identifier(self) -> str:
        return "server"

    def get_author(self) -> str:
        return "harryitz"

    def get_version(self) -> str:
        return "1.0"

    def on_request(self, player: Optional[Player], params: str) -> Optional[str]:
        if params == "name":        return self.server.name
        if params == "version":     return self.server.version
        if params == "mc_version":  return self.server.minecraft_version
        if params == "online":      return str(len(self.server.online_players))
        if params == "max_players": return str(self.server.max_players)
        if params == "port":        return str(self.server.port)

        return None
