#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OllamaPilot - Application de pilotage complet pour Ollama
Un seul fichier, bibliotheque standard uniquement

Usage: python ollama_pilot.py [OPTIONS]

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

DEFAULT_URL = "http://127.0.0.1:11434"
DEFAULT_TIMEOUT = 60
DEFAULT_LOG_FILE = "log_message.txt"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 2048


# ═══════════════════════════════════════════════════════════════════════════════
# CLASSE PRINCIPALE: PILOTE OLLAMA
# ═══════════════════════════════════════════════════════════════════════════════

class OllamaPilot:
    """Classe principale pour interagir avec Ollama via son API REST native."""

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
        """Effectue une requete HTTP vers Ollama.

        Retourne: (succes, donnees, message_erreur)
        """
        if is_openai:
            url = f"{self.base_url}{endpoint}"
        else:
            url = f"{self.base_url}/api{endpoint}"

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

    def load_model(self, model_name: str, keep_alive: str = "5m") -> Tuple[bool, str]:
        """Charge un modele dans Ollama (via /api/generate avec keep_alive)."""
        print(f"📥 Chargement du modele: {model_name}")

        # Ollama charge automatiquement au premier appel generate/chat
        # On fait un appel generate minimal pour forcer le chargement
        payload = {
            "model": model_name,
            "prompt": "",
            "stream": False,
            "keep_alive": keep_alive
        }

        success, data, error = self._request("POST", "/generate", payload)

        if success:
            msg = f"Modele '{model_name}' charge avec succes"
            print(f"  ✅ {msg}")
            self.operations_log.append({
                "time": datetime.now().isoformat(),
                "operation": "LOAD",
                "target": model_name,
                "success": True,
                "message": msg
            })
            return True, msg
        else:
            msg = f"Echec chargement '{model_name}': {error}"
            print(f"  ❌ {msg}")
            self.operations_log.append({
                "time": datetime.now().isoformat(),
                "operation": "LOAD",
                "target": model_name,
                "success": False,
                "message": msg
            })
            return False, msg

    def unload_model(self, model_name: str) -> Tuple[bool, str]:
        """Decharge un modele de la memoire (keep_alive: 0)."""
        print(f"📤 Dechargement du modele: {model_name}")

        # Pour decharger, on fait un appel avec keep_alive: 0
        payload = {
            "model": model_name,
            "prompt": "",
            "stream": False,
            "keep_alive": "0s"
        }

        success, data, error = self._request("POST", "/generate", payload)

        if success:
            msg = f"Modele '{model_name}' decharge de la memoire"
            print(f"  ✅ {msg}")
            self.operations_log.append({
                "time": datetime.now().isoformat(),
                "operation": "UNLOAD",
                "target": model_name,
                "success": True,
                "message": msg
            })
            return True, msg
        else:
            msg = f"Echec dechargement '{model_name}': {error}"
            print(f"  ❌ {msg}")
            self.operations_log.append({
                "time": datetime.now().isoformat(),
                "operation": "UNLOAD",
                "target": model_name,
                "success": False,
                "message": msg
            })
            return False, msg

    def download_model(self, model_name: str, stream: bool = False) -> Tuple[bool, str]:
        """Telecharge un modele depuis le registry Ollama (/api/pull)."""
        print(f"📥 Telechargement du modele: {model_name}")
        print(f"  ⏳ Cela peut prendre plusieurs minutes...")

        payload = {
            "model": model_name,
            "stream": stream
        }

        success, data, error = self._request("POST", "/pull", payload)

        if success:
            msg = f"Modele '{model_name}' telecharge avec succes"
            print(f"  ✅ {msg}")
            self.operations_log.append({
                "time": datetime.now().isoformat(),
                "operation": "DOWNLOAD",
                "target": model_name,
                "success": True,
                "message": msg
            })
            return True, msg
        else:
            msg = f"Echec telechargement '{model_name}': {error}"
            print(f"  ❌ {msg}")
            self.operations_log.append({
                "time": datetime.now().isoformat(),
                "operation": "DOWNLOAD",
                "target": model_name,
                "success": False,
                "message": msg
            })
            return False, msg

    def delete_model(self, model_name: str) -> Tuple[bool, str]:
        """Supprime un modele local (/api/delete)."""
        print(f"🗑️  Suppression du modele: {model_name}")

        payload = {"model": model_name}

        success, data, error = self._request("DELETE", "/delete", payload)

        if success:
            msg = f"Modele '{model_name}' supprime avec succes"
            print(f"  ✅ {msg}")
            self.operations_log.append({
                "time": datetime.now().isoformat(),
                "operation": "DELETE",
                "target": model_name,
                "success": True,
                "message": msg
            })
            return True, msg
        else:
            msg = f"Echec suppression '{model_name}': {error}"
            print(f"  ❌ {msg}")
            self.operations_log.append({
                "time": datetime.now().isoformat(),
                "operation": "DELETE",
                "target": model_name,
                "success": False,
                "message": msg
            })
            return False, msg

    def list_models(self) -> Tuple[bool, List[Dict], str]:
        """Liste les modeles disponibles localement (/api/tags)."""
        print("📋 Liste des modeles disponibles:")

        success, data, error = self._request("GET", "/tags")

        if success and isinstance(data, dict) and "models" in data:
            models = data["models"]
            print(f"  ✅ {len(models)} modele(s) trouve(s)")
            for m in models:
                name = m.get("name", "N/A")
                size = self._format_size(m.get("size", 0))
                params = m.get("details", {}).get("parameter_size", "?")
                quant = m.get("details", {}).get("quantization_level", "?")
                print(f"     • {name} ({params}, {quant}) - {size}")
            return True, models, ""
        else:
            msg = f"Echec listage: {error}"
            print(f"  ❌ {msg}")
            return False, [], msg

    def get_running_models(self) -> Tuple[bool, List[Dict], str]:
        """Recupere les modeles actuellement en memoire (/api/ps)."""
        print("📦 Modeles actuellement en memoire:")

        success, data, error = self._request("GET", "/ps")

        if success and isinstance(data, dict) and "models" in data:
            models = data["models"]
            if models:
                print(f"  ✅ {len(models)} modele(s) en memoire")
                for m in models:
                    name = m.get("name", "N/A")
                    vram = self._format_size(m.get("size_vram", 0))
                    expires = m.get("expires_at", "N/A")
                    print(f"     • {name} (VRAM: {vram}, expire: {expires})")
            else:
                print("  ⚠️  Aucun modele en memoire")
            return True, models, ""
        else:
            msg = f"Echec: {error}"
            print(f"  ❌ {msg}")
            return False, [], msg

    def get_model_info(self, model_name: str) -> Tuple[bool, Dict, str]:
        """Recupere les informations detaillees d un modele (/api/show)."""
        print(f"📊 Informations du modele: {model_name}")

        payload = {"model": model_name}
        success, data, error = self._request("POST", "/show", payload)

        if success and isinstance(data, dict):
            info = {
                "license": data.get("license", "N/A"),
                "modelfile": data.get("modelfile", "N/A"),
                "parameters": data.get("parameters", "N/A"),
                "template": data.get("template", "N/A"),
                "details": data.get("details", {})
            }
            print(f"  ✅ Modele: {model_name}")
            details = info["details"]
            print(f"     Format: {details.get('format', 'N/A')}")
            print(f"     Famille: {details.get('family', 'N/A')}")
            print(f"     Parametres: {details.get('parameter_size', 'N/A')}")
            print(f"     Quantization: {details.get('quantization_level', 'N/A')}")
            return True, info, ""
        else:
            msg = f"Echec recuperation infos: {error}"
            print(f"  ❌ {msg}")
            return False, {}, msg

    # ─── CHAT / GENERATION ──────────────────────────────────────────────────

    def send_message(self, model_name: str, message: str,
                     system_prompt: Optional[str] = None,
                     temperature: float = DEFAULT_TEMPERATURE,
                     max_tokens: int = DEFAULT_MAX_TOKENS,
                     stream: bool = False,
                     keep_alive: str = "5m") -> Tuple[bool, str, Dict]:
        """Envoie un message au LLM via /api/chat et retourne la reponse."""
        print(f"💬 Envoi du message: '{message[:60]}{'...' if len(message) > 60 else ''}'")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})

        payload = {
            "model": model_name,
            "messages": messages,
            "stream": stream,
            "keep_alive": keep_alive,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }

        success, data, error = self._request("POST", "/chat", payload)

        if success and data and "message" in data:
            content = data["message"].get("content", "")

            # Extraire les metriques
            prompt_eval_count = data.get("prompt_eval_count", 0)
            eval_count = data.get("eval_count", 0)
            total_duration = data.get("total_duration", 0)
            load_duration = data.get("load_duration", 0)

            msg = f"Reponse recue ({eval_count} tokens generes)"
            print(f"  ✅ {msg}")

            self.operations_log.append({
                "time": datetime.now().isoformat(),
                "operation": "SEND",
                "target": message[:50],
                "success": True,
                "message": msg,
                "response": content,
                "metrics": {
                    "prompt_tokens": prompt_eval_count,
                    "generated_tokens": eval_count,
                    "total_duration_ns": total_duration,
                    "load_duration_ns": load_duration
                }
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

    def generate_text(self, model_name: str, prompt: str,
                     temperature: float = DEFAULT_TEMPERATURE,
                     max_tokens: int = DEFAULT_MAX_TOKENS,
                     stream: bool = False) -> Tuple[bool, str, Dict]:
        """Generation simple via /api/generate."""
        print(f"📝 Generation avec: '{prompt[:60]}{'...' if len(prompt) > 60 else ''}'")

        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }

        success, data, error = self._request("POST", "/generate", payload)

        if success and data and "response" in data:
            content = data["response"]
            eval_count = data.get("eval_count", 0)

            msg = f"Generation recue ({eval_count} tokens)"
            print(f"  ✅ {msg}")

            self.operations_log.append({
                "time": datetime.now().isoformat(),
                "operation": "GENERATE",
                "target": prompt[:50],
                "success": True,
                "message": msg,
                "response": content
            })
            return True, content, data
        else:
            msg = f"Echec generation: {error}"
            print(f"  ❌ {msg}")
            self.operations_log.append({
                "time": datetime.now().isoformat(),
                "operation": "GENERATE",
                "target": prompt[:50],
                "success": False,
                "message": msg
            })
            return False, msg, {}

    # ─── INFORMATIONS & MONITORING ──────────────────────────────────────────

    def get_context_usage(self, model_name: str) -> Tuple[bool, Dict, str]:
        """Retourne l'utilisation du contexte via /api/ps et metriques."""
        print("📈 Utilisation du contexte:")

        # Recuperer les modeles en memoire
        success, models, error = self.get_running_models()

        if success and models:
            model = models[0]  # Premier modele en memoire
            name = model.get("name", "N/A")

            # Faire un appel chat minimal pour obtenir les metriques
            payload = {
                "model": model_name,
                "messages": [{"role": "user", "content": "_"}],
                "stream": False,
                "options": {"temperature": 0.0, "num_predict": 1}
            }
            s2, d2, e2 = self._request("POST", "/chat", payload)

            prompt_eval_count = d2.get("prompt_eval_count", 0) if d2 else 0
            eval_count = d2.get("eval_count", 0) if d2 else 0
            total_used = prompt_eval_count + eval_count

            # Estimation du contexte total (Ollama ne l expose pas directement)
            # On utilise les details du modele ou une valeur par defaut
            info_success, info_data, _ = self.get_model_info(model_name)
            ctx_length = 4096  # Valeur par defaut

            percentage = (total_used / ctx_length * 100) if ctx_length > 0 else 0

            usage_info = {
                "model": name,
                "used_tokens": total_used,
                "total_tokens": ctx_length,
                "percentage": round(percentage, 2),
                "remaining": ctx_length - total_used,
                "vram": self._format_size(model.get("size_vram", 0))
            }

            print(f"  ✅ Modele: {name}")
            print(f"     Utilise: {total_used} tokens estimes")
            print(f"     VRAM: {usage_info['vram']}")
            return True, usage_info, ""
        else:
            msg = f"Impossible d obtenir l utilisation: {error}"
            print(f"  ❌ {msg}")
            return False, {}, msg

    def get_server_status(self) -> Tuple[bool, Dict, str]:
        """Verifie si Ollama repond (/api/tags comme health check)."""
        success, data, error = self._request("GET", "/tags")

        if success:
            return True, data or {}, ""
        else:
            return False, {}, error

    def get_version(self) -> Tuple[bool, str, str]:
        """Recupere la version d Ollama (/api/version)."""
        print("🔢 Version d Ollama:")

        success, data, error = self._request("GET", "/version")

        if success and isinstance(data, dict) and "version" in data:
            version = data["version"]
            print(f"  ✅ {version}")
            return True, version, ""
        else:
            msg = f"Echec recuperation version: {error}"
            print(f"  ❌ {msg}")
            return False, "", msg

    # ─── UTILITAIRES ──────────────────────────────────────────────────────────

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Formate une taille en bytes en format lisible."""
        if size_bytes == 0:
            return "0 B"
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if abs(size_bytes) < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"


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
            "  OLLAMA PILOT - LOG",
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
        if response_data and "message" in response_data:
            content = response_data["message"].get("content", "")
            lines.extend([
                "",
                "-" * 70,
                "  REPONSE LLM",
                "-" * 70,
                content,
            ])
        elif response_data and "response" in response_data:
            lines.extend([
                "",
                "-" * 70,
                "  REPONSE GENERATION",
                "-" * 70,
                response_data["response"],
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
            "  OLLAMA PILOT - LOG (ERREUR)",
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
            prog="ollama_pilot.py",
            description="Pilotage complet d Ollama - Charge, decharge, chat, infos",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Exemples:
  # Verifier la connexion
  python ollama_pilot.py --status

  # Lister les modeles
  python ollama_pilot.py --list

  # Charger un modele
  python ollama_pilot.py --load llama3.2:3b

  # Decharger
  python ollama_pilot.py --unload llama3.2:3b

  # Envoyer un message
  python ollama_pilot.py --model llama3.2:3b --send "Explique la relativite"

  # Pipeline complet
  python ollama_pilot.py --model llama3.2:3b --load --send "Bonjour" --unload

  # Infos contexte
  python ollama_pilot.py --model llama3.2:3b --context-usage
            """
        )

        # ─── Gestion des modeles ──────────────────────────────────────────────
        model_group = parser.add_argument_group("📦 Gestion des modeles")
        model_group.add_argument("--model", "-m", metavar="MODEL",
                                 help="Nom du modele a utiliser (ex: llama3.2:3b)")
        model_group.add_argument("--load", action="store_true",
                                 help="Charger le modele specifie par --model")
        model_group.add_argument("--unload", action="store_true",
                                 help="Decharger le modele specifie par --model")
        model_group.add_argument("--download", action="store_true",
                                 help="Telecharger le modele specifie par --model")
        model_group.add_argument("--delete", action="store_true",
                                 help="Supprimer le modele specifie par --model")
        model_group.add_argument("--list", "-l", action="store_true",
                                 help="Lister les modeles disponibles localement")
        model_group.add_argument("--running", action="store_true",
                                 help="Afficher les modeles actuellement en memoire")
        model_group.add_argument("--info", "-i", action="store_true",
                                 help="Informations detaillees du modele (--model)")
        model_group.add_argument("--keep-alive", default="5m", metavar="DUREE",
                                 help="Duree de conservation en memoire (defaut: 5m)")

        # ─── Chat / Generation ────────────────────────────────────────────────
        chat_group = parser.add_argument_group("💬 Chat & Generation")
        chat_group.add_argument("--send", metavar="MESSAGE",
                                help="Message a envoyer au LLM (chat)")
        chat_group.add_argument("--generate", metavar="PROMPT",
                                help="Prompt pour generation simple")
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
        info_group.add_argument("--context-usage", action="store_true",
                                help="Afficher l'utilisation du contexte")
        info_group.add_argument("--status", action="store_true",
                                help="Verifier le statut du serveur Ollama")
        info_group.add_argument("--version", "-v", action="store_true",
                                help="Afficher la version d Ollama")

        # ─── Options generales ──────────────────────────────────────────────
        general_group = parser.add_argument_group("⚙️  Options generales")
        general_group.add_argument("--url", default=DEFAULT_URL, metavar="URL",
                                   help=f"URL d Ollama (defaut: {DEFAULT_URL})")
        general_group.add_argument("--token", metavar="TOKEN",
                                   help="Token API si authentification activee")
        general_group.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                                     metavar="N",
                                     help=f"Timeout en secondes (defaut: {DEFAULT_TIMEOUT})")
        general_group.add_argument("--verbose", action="store_true",
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
    def execute(pilot: OllamaPilot, args: argparse.Namespace) -> Tuple[bool, str, Optional[Dict]]:
        """Execute les commandes demandees et retourne le resultat global."""

        # Afficher les exemples si demande
        if args.examples:
            CLI._print_examples()
            return True, "Exemples affiches", None

        # Verifier qu au moins une action est demandee
        actions = [
            args.load, args.unload, args.download, args.delete, args.list,
            args.running, args.info, args.send, args.generate, args.context_usage,
            args.status, args.version
        ]
        if not any(actions):
            print("❌ Aucune action specifiee. Utilisez --help pour voir les options.")
            print("   ou --examples pour des exemples d utilisation.")
            return False, "Aucune action specifiee", None

        all_success = True
        final_message = "Toutes les operations ont reussi"
        response_data = None

        # ─── 1. LISTE DES MODELES ───────────────────────────────────────────
        if args.list:
            success, models, msg = pilot.list_models()
            if not success:
                all_success = False
                final_message = msg

        # ─── 2. MODELES EN MEMOIRE ────────────────────────────────────────────
        if args.running:
            success, models, msg = pilot.get_running_models()
            if not success:
                all_success = False
                final_message = msg

        # ─── 3. INFOS MODELE ──────────────────────────────────────────────────
        if args.info:
            if not args.model:
                print("❌ --info necessite --model")
                return False, "--info necessite --model", None
            success, info, msg = pilot.get_model_info(args.model)
            if not success:
                all_success = False
                final_message = msg

        # ─── 4. VERSION ──────────────────────────────────────────────────────
        if args.version:
            success, version, msg = pilot.get_version()
            if not success:
                all_success = False
                final_message = msg

        # ─── 5. STATUT ──────────────────────────────────────────────────────
        if args.status:
            success, status, msg = pilot.get_server_status()
            if success:
                print("✅ Ollama est en ligne et repond")
                if status and "models" in status:
                    print(f"   Modeles disponibles: {len(status['models'])}")
            else:
                all_success = False
                final_message = f"Ollama ne repond pas: {msg}"
                print(f"❌ {final_message}")

        # ─── 6. TELECHARGER ──────────────────────────────────────────────────
        if args.download:
            if not args.model:
                print("❌ --download necessite --model")
                return False, "--download necessite --model", None
            success, msg = pilot.download_model(args.model)
            if not success:
                all_success = False
                final_message = msg

        # ─── 7. CHARGER ──────────────────────────────────────────────────────
        if args.load:
            if not args.model:
                print("❌ --load necessite --model")
                return False, "--load necessite --model", None
            success, msg = pilot.load_model(args.model, args.keep_alive)
            if not success:
                all_success = False
                final_message = msg
                return False, msg, None

        # ─── 8. ENVOYER MESSAGE (CHAT) ──────────────────────────────────────
        if args.send:
            if not args.model:
                print("❌ --send necessite --model")
                return False, "--send necessite --model", None
            success, content, data = pilot.send_message(
                args.model, args.send, args.system,
                args.temperature, args.max_tokens, args.stream, args.keep_alive
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

        # ─── 9. GENERER (GENERATE) ───────────────────────────────────────────
        if args.generate:
            if not args.model:
                print("❌ --generate necessite --model")
                return False, "--generate necessite --model", None
            success, content, data = pilot.generate_text(
                args.model, args.generate,
                args.temperature, args.max_tokens, args.stream
            )
            if success:
                response_data = data
                print(f"\n📝 Generation:")
                print("-" * 60)
                print(content)
                print("-" * 60)
            else:
                all_success = False
                final_message = content

        # ─── 10. UTILISATION CONTEXTE ────────────────────────────────────────
        if args.context_usage:
            if not args.model:
                print("❌ --context-usage necessite --model")
                return False, "--context-usage necessite --model", None
            success, usage, msg = pilot.get_context_usage(args.model)
            if not success:
                all_success = False
                final_message = msg

        # ─── 11. DECHARGER ───────────────────────────────────────────────────
        if args.unload:
            if not args.model:
                print("❌ --unload necessite --model")
                return False, "--unload necessite --model", None
            success, msg = pilot.unload_model(args.model)
            if not success:
                all_success = False
                final_message = msg

        # ─── 12. SUPPRIMER ───────────────────────────────────────────────────
        if args.delete:
            if not args.model:
                print("❌ --delete necessite --model")
                return False, "--delete necessite --model", None
            success, msg = pilot.delete_model(args.model)
            if not success:
                all_success = False
                final_message = msg

        return all_success, final_message, response_data

    @staticmethod
    def _print_examples():
        """Affiche des exemples d utilisation."""
        examples = """
═══════════════════════════════════════════════════════════════════════════════
                              EXEMPLES D UTILISATION
═══════════════════════════════════════════════════════════════════════════════

🔌 VERIFIER LA CONNEXION
   python ollama_pilot.py --status

📋 LISTER LES MODELES DISPONIBLES
   python ollama_pilot.py --list

📥 CHARGER UN MODELE
   python ollama_pilot.py --model llama3.2:3b --load
   python ollama_pilot.py --model llama3.2:3b --load --keep-alive 30m

📤 DECHARGER UN MODELE
   python ollama_pilot.py --model llama3.2:3b --unload

💬 ENVOYER UN MESSAGE (CHAT)
   python ollama_pilot.py --model llama3.2:3b --send "Explique la relativite"
   python ollama_pilot.py --model llama3.2:3b --send "Bonjour" --system "Sois concis"

📝 GENERATION SIMPLE
   python ollama_pilot.py --model llama3.2:3b --generate "Ecris un poeme"

🔄 PIPELINE COMPLET (charger + envoyer + decharger)
   python ollama_pilot.py --model llama3.2:3b --load --send "Bonjour" --unload

📊 INFORMATIONS
   python ollama_pilot.py --model llama3.2:3b --info
   python ollama_pilot.py --model llama3.2:3b --context-usage
   python ollama_pilot.py --running
   python ollama_pilot.py --version

📥 TELECHARGER UN MODELE
   python ollama_pilot.py --model llama3.2:3b --download

🗑️  SUPPRIMER UN MODELE
   python ollama_pilot.py --model llama3.2:3b --delete

⚙️  OPTIONS AVANCEES
   python ollama_pilot.py --status --url http://192.168.1.10:11434
   python ollama_pilot.py --model llama3.2:3b --send "Test" --verbose --no-log
   python ollama_pilot.py --model llama3.2:3b --send "Test" --temperature 0.3 --max-tokens 500

═══════════════════════════════════════════════════════════════════════════════
        """
        print(examples)


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTION PRINCIPALE
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Point d entree principal de l application."""

    # Recuperer la ligne de commande complete pour le log
    command_line = " ".join(sys.argv)

    # Parser les arguments
    args = CLI.parse_args()

    # Afficher les exemples si demande
    if args.examples:
        CLI._print_examples()
        sys.exit(0)

    # Initialiser le pilote
    pilot = OllamaPilot(
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

    print(f"🔗 Connexion a Ollama: {args.url}")

    # Verifier la connexion (sauf si --examples)
    connected, status, error = pilot.get_server_status()

    if not connected:
        error_msg = f"Ollama ne repond pas sur {args.url}\n"
        error_msg += f"Erreur: {error}\n"
        error_msg += "Verifiez qu Ollama est demarre (ollama serve)."

        print(f"\n❌ {error_msg}")
        logger.log_error(error_msg, command_line, args.url)
        sys.exit(1)

    print("✅ Connexion etablie avec Ollama\n")

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
