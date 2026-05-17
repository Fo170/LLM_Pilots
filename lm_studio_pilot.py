#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LM Studio Pilot - Application de pilotage complet pour LM Studio
Un seul fichier, bibliotheque standard uniquement

Usage: python lm_studio_pilot.py [OPTIONS]

Auteur: Genere automatiquement
Date: 2026-05-17
"""

import sys
import json
import urllib.request
import urllib.error
import os
import argparse
from datetime import datetime
from typing import Optional, Dict, List, Any, Tuple


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION PAR DEFAUT
# ═══════════════════════════════════════════════════════════════════════════════

DEFAULT_URL = "http://127.0.0.1:1234"
DEFAULT_TIMEOUT = 60
DEFAULT_LOG_FILE = "log_message.txt"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 2048


# ═══════════════════════════════════════════════════════════════════════════════
# CLASSE PRINCIPALE: PILOTE LM STUDIO
# ═══════════════════════════════════════════════════════════════════════════════

class LMStudioPilot:
    """Classe principale pour interagir avec LM Studio via son API REST."""

    def __init__(self, base_url: str = DEFAULT_URL, token: Optional[str] = None,
                 timeout: int = DEFAULT_TIMEOUT, verbose: bool = False):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout
        self.verbose = verbose
        self.operations_log: List[Dict[str, Any]] = []

    # ─── API HTTP ─────────────────────────────────────────────────────────────

    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None,
                 is_openai: bool = False) -> Tuple[bool, Any, str]:
        """Effectue une requete HTTP vers LM Studio.

        Retourne: (succes, donnees, message_erreur)
        """
        if is_openai:
            url = f"{self.base_url}{endpoint}"
        else:
            url = f"{self.base_url}/api/v1{endpoint}"

        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        body = json.dumps(data, ensure_ascii=False).encode("utf-8") if data else None

        if self.verbose:
            print(f"  [HTTP] {method} {url}")
            if data:
                print(f"  [BODY] {json.dumps(data, ensure_ascii=False)[:200]}...")

        req = urllib.request.Request(url, data=body, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                response_body = response.read().decode("utf-8")
                if response_body:
                    return True, json.loads(response_body), ""
                return True, {}, ""

        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else "N/A"
            return False, None, f"HTTP {e.code}: {e.reason} | {error_body}"

        except urllib.error.URLError as e:
            return False, None, f"Connexion refusee: {e.reason}"

        except TimeoutError:
            return False, None, "Timeout - le serveur ne repond pas a temps"

        except Exception as e:
            return False, None, f"Erreur: {str(e)}"

    # ─── GESTION DES MODELES ──────────────────────────────────────────────────

    def load_model(self, model_path: str, context_length: Optional[int] = None,
                   gpu: str = "max") -> Tuple[bool, str]:
        """Charge un modele dans LM Studio."""
        print(f"📥 Chargement du modele: {model_path}")

        payload = {"model": model_path}
        if context_length:
            payload["context_length"] = context_length
        if gpu:
            payload["gpu"] = gpu

        success, data, error = self._request("POST", "/models/load", payload)

        if success:
            msg = f"Modele '{model_path}' charge avec succes"
            print(f"  ✅ {msg}")
            self.operations_log.append({
                "time": datetime.now().isoformat(),
                "operation": "LOAD",
                "target": model_path,
                "success": True,
                "message": msg
            })
            return True, msg
        else:
            msg = f"Echec chargement '{model_path}': {error}"
            print(f"  ❌ {msg}")
            self.operations_log.append({
                "time": datetime.now().isoformat(),
                "operation": "LOAD",
                "target": model_path,
                "success": False,
                "message": msg
            })
            return False, msg

    def unload_model(self, model_path: Optional[str] = None) -> Tuple[bool, str]:
        """Decharge un modele (ou tous les modeles si model_path est None)."""
        target = model_path if model_path else "tous les modeles"
        print(f"📤 Dechargement: {target}")

        payload = {}
        if model_path:
            payload["model"] = model_path

        success, data, error = self._request("POST", "/models/unload", payload)

        if success:
            msg = f"Modele(s) decharge(s): {target}"
            print(f"  ✅ {msg}")
            self.operations_log.append({
                "time": datetime.now().isoformat(),
                "operation": "UNLOAD",
                "target": target,
                "success": True,
                "message": msg
            })
            return True, msg
        else:
            msg = f"Echec dechargement '{target}': {error}"
            print(f"  ❌ {msg}")
            self.operations_log.append({
                "time": datetime.now().isoformat(),
                "operation": "UNLOAD",
                "target": target,
                "success": False,
                "message": msg
            })
            return False, msg

    def download_model(self, model_path: str) -> Tuple[bool, str]:
        """Telecharge un modele depuis HuggingFace."""
        print(f"📥 Telechargement du modele: {model_path}")
        print(f"  ⏳ Cela peut prendre plusieurs minutes...")

        payload = {"model": model_path}
        success, data, error = self._request("POST", "/models/download", payload)

        if success:
            msg = f"Modele '{model_path}' telecharge avec succes"
            print(f"  ✅ {msg}")
            self.operations_log.append({
                "time": datetime.now().isoformat(),
                "operation": "DOWNLOAD",
                "target": model_path,
                "success": True,
                "message": msg
            })
            return True, msg
        else:
            msg = f"Echec telechargement '{model_path}': {error}"
            print(f"  ❌ {msg}")
            self.operations_log.append({
                "time": datetime.now().isoformat(),
                "operation": "DOWNLOAD",
                "target": model_path,
                "success": False,
                "message": msg
            })
            return False, msg

    def list_models(self) -> Tuple[bool, List[Dict], str]:
        """Liste les modeles disponibles localement."""
        print("📋 Liste des modeles disponibles:")

        success, data, error = self._request("GET", "/models")

        if success and isinstance(data, dict) and "data" in data:
            models = data["data"]
            print(f"  ✅ {len(models)} modele(s) trouve(s)")
            for m in models:
                name = m.get("id", "N/A")
                size = m.get("size", "?")
                print(f"     • {name} ({size})")
            return True, models, ""
        else:
            msg = f"Echec listage: {error}"
            print(f"  ❌ {msg}")
            return False, [], msg

    def get_loaded_models(self) -> Tuple[bool, List[Dict], str]:
        """Recupere les modeles actuellement charges."""
        print("📦 Modeles actuellement charges:")

        success, data, error = self._request("GET", "/models/loaded")

        if success and isinstance(data, dict) and "data" in data:
            models = data["data"]
            if models:
                print(f"  ✅ {len(models)} modele(s) charge(s)")
                for m in models:
                    name = m.get("id", "N/A")
                    ctx = m.get("context_length", "?")
                    print(f"     • {name} (contexte: {ctx})")
            else:
                print("  ⚠️  Aucun modele charge")
            return True, models, ""
        else:
            msg = f"Echec: {error}"
            print(f"  ❌ {msg}")
            return False, [], msg

    # ─── CHAT / COMPLETION ──────────────────────────────────────────────────

    def send_message(self, message: str, system_prompt: Optional[str] = None,
                     temperature: float = DEFAULT_TEMPERATURE,
                     max_tokens: int = DEFAULT_MAX_TOKENS,
                     stream: bool = False) -> Tuple[bool, str, Dict]:
        """Envoie un message au LLM et retourne la reponse."""
        print(f"💬 Envoi du message: '{message[:60]}{'...' if len(message) > 60 else ''}'")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})

        payload = {
            "model": "local-model",
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }

        success, data, error = self._request("POST", "/chat/completions", payload, is_openai=True)

        if success and data and "choices" in data and len(data["choices"]) > 0:
            content = data["choices"][0].get("message", {}).get("content", "")
            usage = data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)

            msg = f"Reponse recue ({completion_tokens} tokens de reponse, {total_tokens} total)"
            print(f"  ✅ {msg}")

            self.operations_log.append({
                "time": datetime.now().isoformat(),
                "operation": "SEND",
                "target": message[:50],
                "success": True,
                "message": msg,
                "response": content,
                "tokens": {"prompt": prompt_tokens, "completion": completion_tokens, "total": total_tokens}
            })
            return True, content, data
        else:
            msg = f"Echec envoi message: {error}"
            print(f"  ❌ {msg}")
            self.operations_log.append({
                "time": datetime.now().isoformat(),
                "operation": "SEND",
                "target": message[:50],
                "success": False,
                "message": msg
            })
            return False, msg, {}

    # ─── INFORMATIONS ───────────────────────────────────────────────────────

    def get_model_info(self) -> Tuple[bool, Dict, str]:
        """Recupere les informations du modele charge."""
        print("📊 Informations du modele charge:")

        success, data, error = self._request("GET", "/models/loaded")

        if success and isinstance(data, dict) and "data" in data and data["data"]:
            model = data["data"][0]  # Premier modele charge
            info = {
                "id": model.get("id", "N/A"),
                "context_length": model.get("context_length", "N/A"),
                "gpu": model.get("gpu", "N/A"),
                "format": model.get("format", "N/A"),
                "size": model.get("size", "N/A"),
                "architecture": model.get("architecture", "N/A")
            }
            print(f"  ✅ Modele: {info['id']}")
            print(f"     Contexte: {info['context_length']} tokens")
            print(f"     GPU: {info['gpu']}")
            print(f"     Format: {info['format']}")
            return True, info, ""
        else:
            msg = f"Aucun modele charge ou erreur: {error}"
            print(f"  ❌ {msg}")
            return False, {}, msg

    def get_context_usage(self) -> Tuple[bool, Dict, str]:
        """Retourne l'utilisation du contexte en pourcentage."""
        print("📈 Utilisation du contexte:")

        # On utilise l'endpoint chat/completions avec un message vide pour obtenir les infos
        # ou on regarde dans les modeles charges
        success, data, error = self._request("GET", "/models/loaded")

        if success and isinstance(data, dict) and "data" in data and data["data"]:
            model = data["data"][0]
            total_ctx = model.get("context_length", 0)

            # Essayer d'obtenir l'utilisation via un appel chat
            payload = {
                "model": "local-model",
                "messages": [{"role": "user", "content": "_"}],
                "temperature": 0.0,
                "max_tokens": 1
            }
            s2, d2, e2 = self._request("POST", "/chat/completions", payload, is_openai=True)

            used_tokens = 0
            if s2 and d2 and "usage" in d2:
                used_tokens = d2["usage"].get("prompt_tokens", 0)

            percentage = (used_tokens / total_ctx * 100) if total_ctx > 0 else 0

            info = {
                "used_tokens": used_tokens,
                "total_tokens": total_ctx,
                "percentage": round(percentage, 2),
                "remaining": total_ctx - used_tokens
            }

            print(f"  ✅ Utilise: {used_tokens} / {total_ctx} tokens ({percentage:.1f}%)")
            print(f"     Restant: {info['remaining']} tokens")
            return True, info, ""
        else:
            msg = f"Impossible d'obtenir l'utilisation: {error}"
            print(f"  ❌ {msg}")
            return False, {}, msg

    def get_context_length(self) -> Tuple[bool, int, str]:
        """Retourne la longueur totale du contexte."""
        print("📏 Longueur totale du contexte:")

        success, data, error = self._request("GET", "/models/loaded")

        if success and isinstance(data, dict) and "data" in data and data["data"]:
            length = data["data"][0].get("context_length", 0)
            print(f"  ✅ {length} tokens")
            return True, length, ""
        else:
            msg = f"Impossible d'obtenir la longueur: {error}"
            print(f"  ❌ {msg}")
            return False, 0, msg

    def get_server_status(self) -> Tuple[bool, Dict, str]:
        """Verifie si LM Studio repond."""
        success, data, error = self._request("GET", "/system/status")

        if success:
            return True, data or {}, ""
        else:
            return False, {}, error

    def get_system_info(self) -> Tuple[bool, Dict, str]:
        """Recupere les infos systeme (RAM, GPU, etc.)."""
        print("🖥️  Informations systeme:")

        success, data, error = self._request("GET", "/system")

        if success and isinstance(data, dict):
            info = {
                "cpu": data.get("cpu", "N/A"),
                "ram": data.get("ram", "N/A"),
                "gpu": data.get("gpu", "N/A"),
                "os": data.get("os", "N/A"),
                "version": data.get("version", "N/A")
            }
            print(f"  ✅ OS: {info['os']}")
            print(f"     CPU: {info['cpu']}")
            print(f"     RAM: {info['ram']}")
            print(f"     GPU: {info['gpu']}")
            print(f"     Version LM Studio: {info['version']}")
            return True, info, ""
        else:
            msg = f"Echec recuperation infos: {error}"
            print(f"  ❌ {msg}")
            return False, {}, msg


# ═══════════════════════════════════════════════════════════════════════════════
# CLASSE LOGGER
# ═══════════════════════════════════════════════════════════════════════════════

class Logger:
    """Gere le fichier log_message.txt."""

    def __init__(self, log_file: str = DEFAULT_LOG_FILE, enabled: bool = True):
        self.log_file = log_file
        self.enabled = enabled

    def log(self, operations: List[Dict], command_line: str, url: str,
            final_success: bool, final_message: str, response_data: Optional[Dict] = None):
        """Ecrit le log complet dans le fichier."""
        if not self.enabled:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        lines = [
            "=" * 70,
            "  LM STUDIO PILOT - LOG",
            "=" * 70,
            f"Date: {timestamp}",
            f"Commande: {command_line}",
            f"URL: {url}",
            "",
            "-" * 70,
            "  OPERATIONS",
            "-" * 70,
        ]

        for op in operations:
            status = "SUCCES" if op.get("success") else "ECHEC"
            time_str = op.get("time", "?")[11:19] if "time" in op else "?"
            lines.append(f"[{time_str}] [{op.get('operation', '?')}] {op.get('target', '?')} -> {status}")
            if "message" in op:
                lines.append(f"           {op['message']}")

        lines.extend([
            "",
            "-" * 70,
            "  STATUT FINAL",
            "-" * 70,
            f"{'SUCCES' if final_success else 'ECHEC'}: {final_message}",
            f"Code de sortie: {0 if final_success else 1}",
        ])

        # Ajouter la reponse LLM si presente
        if response_data and "choices" in response_data:
            content = response_data["choices"][0].get("message", {}).get("content", "")
            lines.extend([
                "",
                "-" * 70,
                "  REPONSE LLM",
                "-" * 70,
                content,
            ])

        lines.extend([
            "",
            "=" * 70,
        ])

        try:
            with open(self.log_file, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            print(f"\n📝 Log enregistre: {os.path.abspath(self.log_file)}")
        except Exception as e:
            print(f"\n⚠️  Erreur ecriture log: {e}")

    def log_error(self, error_message: str, command_line: str = "", url: str = ""):
        """Log une erreur de connexion ou autre."""
        if not self.enabled:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        lines = [
            "=" * 70,
            "  LM STUDIO PILOT - LOG (ERREUR)",
            "=" * 70,
            f"Date: {timestamp}",
            f"Commande: {command_line}",
            f"URL: {url}",
            "",
            "-" * 70,
            "  ERREUR",
            "-" * 70,
            error_message,
            "",
            "=" * 70,
        ]

        try:
            with open(self.log_file, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            print(f"\n📝 Log d'erreur enregistre: {os.path.abspath(self.log_file)}")
        except Exception as e:
            print(f"\n⚠️  Erreur ecriture log: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# CLASSE CLI (PARSING ARGUMENTS)
# ═══════════════════════════════════════════════════════════════════════════════

class CLI:
    """Parse les arguments de ligne de commande."""

    @staticmethod
    def parse_args() -> argparse.Namespace:
        parser = argparse.ArgumentParser(
            prog="lm_studio_pilot.py",
            description="Pilotage complet de LM Studio - Charge, decharge, chat, infos",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Exemples:
  # Verifier la connexion
  python lm_studio_pilot.py --status

  # Lister les modeles
  python lm_studio_pilot.py --list

  # Charger un modele
  python lm_studio_pilot.py --load qwen/qwen3-4b-2507 --context-length 4096

  # Decharger
  python lm_studio_pilot.py --unload

  # Envoyer un message
  python lm_studio_pilot.py --send "Explique la relativite" --system "Sois concis"

  # Pipeline complet
  python lm_studio_pilot.py --load qwen/qwen3-4b-2507 --send "Bonjour" --unload

  # Infos contexte
  python lm_studio_pilot.py --context-usage
            """
        )

        # ─── Gestion des modeles ──────────────────────────────────────────────
        model_group = parser.add_argument_group("📦 Gestion des modeles")
        model_group.add_argument("--load", metavar="MODEL",
                                 help="Charger un modele (ex: qwen/qwen3-4b-2507)")
        model_group.add_argument("--unload", nargs="?", const="__ALL__", default=None,
                                 metavar="MODEL",
                                 help="Decharger un modele (sans argument = tous)")
        model_group.add_argument("--download", metavar="MODEL",
                                 help="Telecharger un modele depuis HuggingFace")
        model_group.add_argument("--list", "-l", action="store_true",
                                 help="Lister les modeles disponibles localement")
        model_group.add_argument("--loaded", action="store_true",
                                 help="Afficher les modeles actuellement charges")
        model_group.add_argument("--context-length", type=int, metavar="N",
                                 help="Longueur du contexte (avec --load)")
        model_group.add_argument("--gpu", default="max", metavar="MODE",
                                 help="Utilisation GPU: max, off, ou nombre (defaut: max)")

        # ─── Chat / Message ─────────────────────────────────────────────────
        chat_group = parser.add_argument_group("💬 Envoi de message")
        chat_group.add_argument("--send", metavar="MESSAGE",
                                help="Message a envoyer au LLM")
        chat_group.add_argument("--system", metavar="PROMPT",
                                help="Prompt systeme (avec --send)")
        chat_group.add_argument("--temperature", type=float, default=DEFAULT_TEMPERATURE,
                                metavar="FLOAT",
                                help=f"Temperature (0.0-2.0, defaut: {DEFAULT_TEMPERATURE})")
        chat_group.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS,
                                metavar="N",
                                help=f"Tokens max (defaut: {DEFAULT_MAX_TOKENS})")
        chat_group.add_argument("--stream", action="store_true",
                                help="Activer le streaming (affichage temps reel)")

        # ─── Informations ────────────────────────────────────────────────────
        info_group = parser.add_argument_group("📊 Informations & Monitoring")
        info_group.add_argument("--info", "-i", action="store_true",
                                help="Informations sur le modele charge")
        info_group.add_argument("--context-usage", action="store_true",
                                help="Afficher l'utilisation du contexte (%)")
        info_group.add_argument("--context-length-info", action="store_true",
                                help="Afficher la longueur totale du contexte")
        info_group.add_argument("--status", action="store_true",
                                help="Verifier le statut du serveur LM Studio")
        info_group.add_argument("--system-info", action="store_true",
                                help="Informations systeme (RAM, GPU, etc.)")

        # ─── Options generales ──────────────────────────────────────────────
        general_group = parser.add_argument_group("⚙️  Options generales")
        general_group.add_argument("--url", default=DEFAULT_URL, metavar="URL",
                                   help=f"URL de LM Studio (defaut: {DEFAULT_URL})")
        general_group.add_argument("--token", metavar="TOKEN",
                                   help="Token API si authentification activee")
        general_group.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                                     metavar="N",
                                     help=f"Timeout en secondes (defaut: {DEFAULT_TIMEOUT})")
        general_group.add_argument("--verbose", "-v", action="store_true",
                                   help="Mode verbeux (afficher les requetes HTTP)")
        general_group.add_argument("--no-log", action="store_true",
                                   help="Ne pas creer le fichier log")
        general_group.add_argument("--log-file", default=DEFAULT_LOG_FILE,
                                   metavar="FILE",
                                   help=f"Nom du fichier log (defaut: {DEFAULT_LOG_FILE})")

        # ─── Aide ────────────────────────────────────────────────────────────
        help_group = parser.add_argument_group("❓ Aide")
        help_group.add_argument("--examples", action="store_true",
                                help="Afficher des exemples d'utilisation")

        return parser.parse_args()

    @staticmethod
    def execute(pilot: LMStudioPilot, args: argparse.Namespace) -> Tuple[bool, str, Optional[Dict]]:
        """Execute les commandes demandees et retourne le resultat global."""

        # Afficher les exemples si demande
        if args.examples:
            CLI._print_examples()
            return True, "Exemples affiches", None

        # Verifier qu'au moins une action est demandee
        actions = [
            args.load, args.unload, args.download, args.list, args.loaded,
            args.send, args.info, args.context_usage, args.context_length_info,
            args.status, args.system_info
        ]
        if not any(actions):
            print("❌ Aucune action specifiee. Utilisez --help pour voir les options.")
            print("   ou --examples pour des exemples d'utilisation.")
            return False, "Aucune action specifiee", None

        all_success = True
        final_message = "Toutes les operations ont reussi"
        response_data = None

        # ─── 1. CHARGER ─────────────────────────────────────────────────────
        if args.load:
            success, msg = pilot.load_model(args.load, args.context_length, args.gpu)
            if not success:
                all_success = False
                final_message = msg
                return False, msg, None

        # ─── 2. TELECHARGER ────────────────────────────────────────────────
        if args.download:
            success, msg = pilot.download_model(args.download)
            if not success:
                all_success = False
                final_message = msg

        # ─── 3. LISTER ─────────────────────────────────────────────────────
        if args.list:
            success, models, msg = pilot.list_models()
            if not success:
                all_success = False
                final_message = msg

        # ─── 4. MODELES CHARGES ────────────────────────────────────────────
        if args.loaded:
            success, models, msg = pilot.get_loaded_models()
            if not success:
                all_success = False
                final_message = msg

        # ─── 5. INFOS MODELE ───────────────────────────────────────────────
        if args.info:
            success, info, msg = pilot.get_model_info()
            if not success:
                all_success = False
                final_message = msg

        # ─── 6. UTILISATION CONTEXTE ───────────────────────────────────────
        if args.context_usage:
            success, usage, msg = pilot.get_context_usage()
            if not success:
                all_success = False
                final_message = msg

        # ─── 7. LONGUEUR CONTEXTE ──────────────────────────────────────────
        if args.context_length_info:
            success, length, msg = pilot.get_context_length()
            if not success:
                all_success = False
                final_message = msg

        # ─── 8. STATUT ─────────────────────────────────────────────────────
        if args.status:
            success, status, msg = pilot.get_server_status()
            if success:
                print("✅ LM Studio est en ligne et repond")
                if status:
                    print(f"   Version: {status.get('version', 'N/A')}")
                    print(f"   Statut: {status.get('status', 'N/A')}")
            else:
                all_success = False
                final_message = f"LM Studio ne repond pas: {msg}"
                print(f"❌ {final_message}")

        # ─── 9. INFOS SYSTEME ──────────────────────────────────────────────
        if args.system_info:
            success, info, msg = pilot.get_system_info()
            if not success:
                all_success = False
                final_message = msg

        # ─── 10. ENVOYER MESSAGE ─────────────────────────────────────────────
        if args.send:
            success, content, data = pilot.send_message(
                args.send, args.system, args.temperature, args.max_tokens, args.stream
            )
            if success:
                response_data = data
                print(f"\n🤖 Reponse du LLM:")
                print("-" * 60)
                print(content)
                print("-" * 60)
            else:
                all_success = False
                final_message = content

        # ─── 11. DECHARGER ──────────────────────────────────────────────────
        if args.unload:
            model_to_unload = None if args.unload == "__ALL__" else args.unload
            success, msg = pilot.unload_model(model_to_unload)
            if not success:
                all_success = False
                final_message = msg

        return all_success, final_message, response_data

    @staticmethod
    def _print_examples():
        """Affiche des exemples d'utilisation."""
        examples = """
═══════════════════════════════════════════════════════════════════════════════
                              EXEMPLES D'UTILISATION
═══════════════════════════════════════════════════════════════════════════════

🔌 VERIFIER LA CONNEXION
   python lm_studio_pilot.py --status

📋 LISTER LES MODELES DISPONIBLES
   python lm_studio_pilot.py --list

📥 CHARGER UN MODELE
   python lm_studio_pilot.py --load qwen/qwen3-4b-2507
   python lm_studio_pilot.py --load qwen/qwen3-4b-2507 --context-length 8192 --gpu max

📤 DECHARGER UN MODELE
   python lm_studio_pilot.py --unload                    # Tous les modeles
   python lm_studio_pilot.py --unload qwen/qwen3-4b-2507  # Modele specifique

💬 ENVOYER UN MESSAGE
   python lm_studio_pilot.py --send "Explique la relativite restreinte"
   python lm_studio_pilot.py --send "Explique la relativite" --system "Sois concis" --temperature 0.3

🔄 PIPELINE COMPLET (charger + envoyer + decharger)
   python lm_studio_pilot.py --load qwen/qwen3-4b-2507 --send "Bonjour" --unload

📊 INFORMATIONS
   python lm_studio_pilot.py --info              # Infos du modele charge
   python lm_studio_pilot.py --context-usage      # % utilisation contexte
   python lm_studio_pilot.py --context-length-info # Longueur totale
   python lm_studio_pilot.py --system-info        # RAM, GPU, etc.

📥 TELECHARGER UN MODELE
   python lm_studio_pilot.py --download microsoft/Phi-4-mini-instruct

⚙️  OPTIONS AVANCEES
   python lm_studio_pilot.py --status --url http://192.168.1.10:1234
   python lm_studio_pilot.py --send "Test" --verbose --no-log
   python lm_studio_pilot.py --load model --token "votre_token_api"

═══════════════════════════════════════════════════════════════════════════════
        """
        print(examples)


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTION PRINCIPALE
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Point d'entree principal de l'application."""

    # Recuperer la ligne de commande complete pour le log
    command_line = " ".join(sys.argv)

    # Parser les arguments
    args = CLI.parse_args()

    # Afficher les exemples si demande
    if args.examples:
        CLI._print_examples()
        sys.exit(0)

    # Initialiser le pilote
    pilot = LMStudioPilot(
        base_url=args.url,
        token=args.token,
        timeout=args.timeout,
        verbose=args.verbose
    )

    # Initialiser le logger
    logger = Logger(
        log_file=args.log_file,
        enabled=not args.no_log
    )

    print(f"🔗 Connexion a LM Studio: {args.url}")

    # Verifier la connexion (sauf si --examples)
    connected, status, error = pilot.get_server_status()

    if not connected:
        error_msg = f"LM Studio ne repond pas sur {args.url}\n"
        error_msg += f"Erreur: {error}\n"
        error_msg += "Verifiez que LM Studio est demarre et que le serveur API est active."

        print(f"\n❌ {error_msg}")
        logger.log_error(error_msg, command_line, args.url)
        sys.exit(1)

    print("✅ Connexion etablie avec LM Studio\n")

    # Executer les commandes
    success, message, response_data = CLI.execute(pilot, args)

    # Logger le resultat
    logger.log(
        operations=pilot.operations_log,
        command_line=command_line,
        url=args.url,
        final_success=success,
        final_message=message,
        response_data=response_data
    )

    # Afficher le resume
    print(f"\n{'='*70}")
    if success:
        print(f"✅ {message}")
        sys.exit(0)
    else:
        print(f"❌ {message}")
        sys.exit(1)


if __name__ == "__main__":
    main()
