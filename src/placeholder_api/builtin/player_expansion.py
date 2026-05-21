from typing import Optional
from endstone import Player, GameMode
from placeholder_api.expansion import PlaceholderExpansion

class PlayerExpansion(PlaceholderExpansion):
    def get_identifier(self) -> str:
        return "player"

    def get_author(self) -> str:
        return "harryitz"

    def get_version(self) -> str:
        return "1.0"

    def on_request(self, player: Optional[Player], params: str) -> Optional[str]:
        if not player:
            return None

        if params == "name":        return player.name
        if params == "xuid":        return player.xuid
        if params == "uuid":        return str(player.unique_id)
        if params == "health":      return str(player.health)
        if params == "max_health":  return str(player.max_health)
        if params == "level":       return str(player.exp_level)
        if params == "exp":         return str(player.total_exp)
        if params == "ping":        return str(player.ping)
        if params == "world":       return player.location.dimension.name # level not exposed directly in the same way, we use dimension.name or level.name depending on api
        # Endstone python api: player.location.dimension.name might be the world name, let's use dimension.name 
        # Actually endstone has player.location.dimension.type ... wait. Let's look up how to get world/dimension.
        # we can just try player.dimension.name if that exists or player.location.dimension.name
        
        if params == "dimension":   return str(player.location.dimension.type.name)
        if params == "gamemode":    return self._gamemode_string(player.game_mode)
        if params == "x":           return str(player.location.block_x)
        if params == "y":           return str(player.location.block_y)
        if params == "z":           return str(player.location.block_z)
        if params == "is_flying":   return "true" if player.is_flying else "false"
        if params == "is_sneaking": return "true" if player.is_sneaking else "false"
        if params == "is_op":       return "true" if player.is_op else "false"

        return None

    def _gamemode_string(self, gm: GameMode) -> str:
        if gm == GameMode.SURVIVAL:  return "Survival"
        if gm == GameMode.CREATIVE:  return "Creative"
        if gm == GameMode.ADVENTURE: return "Adventure"
        if gm == GameMode.SPECTATOR: return "Spectator"
        return "Unknown"
