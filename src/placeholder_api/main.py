import os
import importlib
import urllib.request
import urllib.error
import json
from typing import Dict, List, Optional, Any

from endstone.plugin import Plugin
from endstone.command import Command, CommandSender
from endstone.event import event_handler, EventPriority, PlayerQuitEvent
from endstone import Player

from placeholder_api.expansion import PlaceholderExpansion
from placeholder_api.replacer import replace_placeholders, contains_delimiters
from placeholder_api.builtin.player_expansion import PlayerExpansion
from placeholder_api.builtin.server_expansion import ServerExpansion

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
                "/papi parse <player: string> <text: message>",
                "/papi ecloud list",
                "/papi ecloud download <name: string>",
                "/papi ecloud refresh"
            ],
            "permissions": ["papi.admin"],
        }
    }

    permissions = {
        "papi.admin": {
            "description": "Access to /papi commands.",
            "default": "op",
        }
    }

    def on_load(self) -> None:
        self.expansions: Dict[str, PlaceholderExpansion] = {}
        self.ecloud_cache: Dict[str, dict] = {}
        
        # We simulate the ecloud by using a dummy manifest or python equivalents
        self.kCloudManifestUrl = "https://raw.githubusercontent.com/EndstoneMC/PlaceholderAPI-python/main/manifest.json" 
        # (This URL may not exist but mimics the C++ behavior)
        
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
        self.logger.info("PlaceholderAPI v1.0.0 (Python) enabled.")

    def on_disable(self) -> None:
        ids = list(self.expansions.keys())
        for identifier in ids:
            self.unregister_expansion(identifier)
        self.expansions.clear()
        self.logger.info("PlaceholderAPI disabled.")

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

        if sub == "ecloud":
            self._handle_ecloud_command(sender, args)
            return True

        sender.send_message("§6PlaceholderAPI v1.0.0")
        sender.send_message("§7  /papi list")
        sender.send_message("§7  /papi info <id>")
        sender.send_message("§7  /papi parse <player> <text...>")
        sender.send_message("§7  /papi ecloud <list|download <name>|refresh>")
        return True

    def _handle_ecloud_command(self, sender: CommandSender, args: list[str]) -> None:
        sub = args[1].lower() if len(args) >= 2 else "list"

        if sub == "refresh":
            sender.send_message("§7Fetching cloud manifest...")
            self.server.scheduler.run_task_asynchronously(self, self._fetch_manifest)
            return

        if sub == "list":
            if not self.ecloud_cache:
                sender.send_message("§7No cloud expansions cached. Run §e/papi ecloud refresh§7 first.")
                return

            sender.send_message(f"§6Cloud expansions §7({len(self.ecloud_cache)}§7):")
            for name, info in self.ecloud_cache.items():
                status = "§e[update]" if info.get('hasUpdate') else "§a[installed]" if info.get('installed') else "§7[not installed]"
                sender.send_message(f"  §e{name}  §7v{info.get('latest_version')}  {status}  §8by {info.get('author')}")
            return

        if sub == "download":
            if len(args) < 3:
                sender.send_error_message("§cUsage: /papi ecloud download <name>")
                return

            name = args[2]
            sender.send_message(f"§7Downloading §e{name}§7...")
            self.server.scheduler.run_task_asynchronously(self, lambda: self._download_expansion(name, sender))
            return

        sender.send_message("§7  /papi ecloud list")
        sender.send_message("§7  /papi ecloud download <name>")
        sender.send_message("§7  /papi ecloud refresh")

    def _fetch_manifest(self) -> None:
        try:
            with urllib.request.urlopen(self.kCloudManifestUrl, timeout=15) as response:
                body = response.read().decode('utf-8')
                
            parsed = json.loads(body)
            self.ecloud_cache.clear()
            for name, obj in parsed.items():
                self.ecloud_cache[name] = {
                    "name": name,
                    "author": obj.get("author", "Unknown"),
                    "description": obj.get("description", ""),
                    "latest_version": obj.get("latest_version", ""),
                    "versions": obj.get("versions", [])
                }
            self._refresh_installed()
            
            def notify_success():
                self.logger.info(f"eCloud: {len(self.ecloud_cache)} expansions available.")
            self.server.scheduler.run_task(self, notify_success)
            
        except Exception as e:
            def notify_fail():
                self.logger.warning(f"eCloud: failed to fetch or parse manifest. {e}")
            self.server.scheduler.run_task(self, notify_fail)

    def _refresh_installed(self) -> None:
        for name, info in self.ecloud_cache.items():
            path = os.path.join(self.expansions_dir, f"{name}.py")
            info["installed"] = os.path.exists(path)
            loaded = self.get_expansion(name)
            info["hasUpdate"] = bool(loaded and loaded.get_version() != info.get("latest_version"))

    def _download_expansion(self, name: str, sender: CommandSender) -> None:
        info = self.ecloud_cache.get(name)
        if not info:
            self.server.scheduler.run_task(self, lambda: sender.send_error_message(f"§cExpansion '{name}' not found in cloud."))
            return

        url = next((v.get("url") for v in info.get("versions", []) if v.get("version") == info.get("latest_version")), None)
        
        if not url:
            self.server.scheduler.run_task(self, lambda: sender.send_error_message(f"§cNo download URL available for '{name}'."))
            return

        out_path = os.path.join(self.expansions_dir, f"{name}.py")
        
        try:
            with urllib.request.urlopen(url, timeout=60) as response, open(out_path, 'wb') as out_file:
                out_file.write(response.read())
                
            def on_success():
                err = self._load_expansion(name, out_path)
                if err:
                    sender.send_error_message(f"§c{err}")
                else:
                    self._refresh_installed()
                    sender.send_message(f"§a{name} downloaded and loaded successfully.")
                    
            self.server.scheduler.run_task(self, on_success)
            
        except Exception as e:
            self.server.scheduler.run_task(self, lambda: sender.send_error_message(f"§cFailed to download {name}: {e}"))

    def _load_expansion(self, name: str, py_path: str) -> Optional[str]:
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(f"papi.expansions.{name}", py_path)
            if spec is None or spec.loader is None:
                return f"Failed to create spec for {py_path}"
                
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            if not hasattr(module, 'papi_create_expansion'):
                return f"Missing papi_create_expansion in {py_path}"
                
            expansion = module.papi_create_expansion()
            if not isinstance(expansion, PlaceholderExpansion):
                return "papi_create_expansion did not return a PlaceholderExpansion"
                
            if not self.register_expansion(expansion):
                return "Failed to register expansion (already registered?)."
                
            return None
        except Exception as e:
            return f"Error loading {py_path}: {e}"
