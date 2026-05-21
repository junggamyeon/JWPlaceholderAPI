import os
from typing import Dict, List, Optional, Any

from endstone.plugin import Plugin
from endstone.command import Command, CommandSender
from endstone.event import event_handler, EventPriority, PlayerQuitEvent
from endstone import Player

from jwplaceholderapi.expansion import PlaceholderExpansion
from jwplaceholderapi.replacer import replace_placeholders, contains_delimiters
from jwplaceholderapi.builtin.player_expansion import PlayerExpansion
from jwplaceholderapi.builtin.server_expansion import ServerExpansion

class PlaceholderAPIPlugin(Plugin):
    api_version = "0.11"
    prefix = "PAPI"
    version = "1.0.0"
    description = "Unified placeholder framework for Endstone plugins (Python version)."
    authors = ["harryitz"]
    
    commands = {
        "papi": {
            "description": "PlaceholderAPI management.",
            "usages": [
                "/papi list",
                "/papi info <id: string>",
                "/papi parse <player: string> <text: message>"
            ],
            "permissions": ["jwplaceholderapi.admin"],
        }
    }

    permissions = {
        "jwplaceholderapi.admin": {
            "description": "Access to /papi commands.",
            "default": "op",
        }
    }

    def on_load(self) -> None:
        self.expansions: Dict[str, PlaceholderExpansion] = {}
        
        self.expansions_dir = os.path.join(self.data_folder, "expansions")
        if not os.path.exists(self.expansions_dir):
            os.makedirs(self.expansions_dir, exist_ok=True)
            
    def on_enable(self) -> None:
        self.register_expansion(PlayerExpansion())
        self.register_expansion(ServerExpansion(self.server))
        
        # Note: We can't strictly register a C++ service from python in the same way,
        # but other python plugins can access this via:
        # server.plugin_manager.get_plugin("PlaceholderAPI-python")
        
        self.register_events(self)

    def on_disable(self) -> None:
        ids = list(self.expansions.keys())
        for identifier in ids:
            self.unregister_expansion(identifier)
        self.expansions.clear()

    def register_expansion(self, expansion: PlaceholderExpansion) -> bool:
        if not expansion:
            return False

        identifier = expansion.get_identifier().lower()
        if not identifier or identifier in self.expansions:
            return False

        expansion.registered = True
        expansion.on_register()
        self.expansions[identifier] = expansion
        return True

    def unregister_expansion(self, identifier: str) -> bool:
        identifier = identifier.lower()
        if identifier not in self.expansions:
            return False

        exp = self.expansions.pop(identifier)
        exp.registered = False
        exp.on_unregister()
        return True

    def is_registered(self, identifier: str) -> bool:
        return identifier.lower() in self.expansions

    def get_expansion(self, identifier: str) -> Optional[PlaceholderExpansion]:
        return self.expansions.get(identifier.lower())

    def get_registered_identifiers(self) -> List[str]:
        return list(self.expansions.keys())

    def set_placeholders(self, player: Optional[Player], text: str) -> str:
        return replace_placeholders(self, player, text, '%', '%')

    def set_bracket_placeholders(self, player: Optional[Player], text: str) -> str:
        return replace_placeholders(self, player, text, '{', '}')

    def contains_placeholders(self, text: str) -> bool:
        return contains_delimiters(text, '%', '%')

    @event_handler(priority=EventPriority.MONITOR)
    def on_player_quit(self, event: PlayerQuitEvent) -> None:
        player = event.player
        for exp in self.expansions.values():
            exp.on_player_quit(player)

    def on_command(self, sender: CommandSender, command: Command, args: list[str]) -> bool:
        if not args:
            sub = "help"
        else:
            sub = args[0].lower()

        if sub == "list":
            ids = sorted(self.get_registered_identifiers())
            if not ids:
                sender.send_message("§7No expansions registered.")
                return True

            sender.send_message(f"§6Registered expansions §7({len(ids)}§7):")
            for identifier in ids:
                exp = self.get_expansion(identifier)
                sender.send_message(f"  §e%{identifier}_...%  §7v{exp.get_version()} by {exp.get_author()}")
            return True

        if sub == "info":
            if len(args) < 2:
                sender.send_error_message("§cUsage: /papi info <identifier>")
                return True

            exp = self.get_expansion(args[1])
            if not exp:
                sender.send_error_message(f"§cExpansion '{args[1]}' not found.")
                return True

            sender.send_message(f"§6--- {exp.get_identifier()} ---")
            sender.send_message(f"  §7Author:  §e{exp.get_author()}")
            sender.send_message(f"  §7Version: §e{exp.get_version()}")
            return True

        if sub == "parse":
            if len(args) < 3:
                sender.send_error_message("§cUsage: /papi parse <player> <text...>")
                return True

            target = next((p for p in self.server.online_players if p.name == args[1]), None)

            if not target:
                sender.send_error_message(f"§cPlayer '{args[1]}' not found or offline.")
                return True

            text = " ".join(args[2:])
            sender.send_message(f"§7Result: §r{self.set_placeholders(target, text)}")
            return True

        sender.send_message("§6PlaceholderAPI v1.0.0")
        sender.send_message("§7  /papi list")
        sender.send_message("§7  /papi info <id>")
        sender.send_message("§7  /papi parse <player> <text...>")
        return True
