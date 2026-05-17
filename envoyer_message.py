#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
envoyer_message.py - Application universelle pour envoyer des messages a un LLM local
Compatible avec LM Studio (port 1234) et Ollama (port 11434)

Usage:
    python envoyer_message.py "votre message" [--lmstudio | --ollama]

Connexion automatique au premier serveur disponible (LM Studio prioritaire)
"""

import sys
import json
import urllib.request
import urllib.error
import os
from datetime import datetime
from typing import Optional, Dict, Tuple, Any


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

LM_STUDIO_URL = "http://127.0.0.1:1234"
OLLAMA_URL = "http://127.0.0.1:11434"
DEFAULT_TIMEOUT = 60
LOG_FILE = "log_message.txt"


class LLMClient:
    """Client universel pour LM Studio et Ollama."""

    def __init__(self, timeout: int = DEFAULT_TIMEOUT, verbose: bool = False):
        self.timeout = timeout
        self.verbose = verbose
        self.backend: Optional[str] = None  # 'lmstudio' ou 'ollama'
        self.base_url: Optional[str] = None
        self.model_name: Optional[str] = None

    def _request(self, url: str, method: str = "GET", data: Optional[Dict] = None,
                 headers: Optional[Dict] = None) -> Tuple[bool, Any, str]:
        """Effectue une requete HTTP."""
        req_headers = headers or {"Content-Type": "application/json"}
        body = json.dumps(data, ensure_ascii=False).encode("utf-8") if data else None

        if self.verbose:
            print(f"  [HTTP] {method} {url}")

        req = urllib.request.Request(url, data=body, headers=req_headers, method=method)

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
            return False, None, "Timeout"
        except Exception as e:
            return False, None, f"Erreur: {str(e)}"

    def detect_backend(self, force_lmstudio: bool = False, 
                       force_ollama: bool = False) -> Tuple[bool, str]:
        """Detecte automatiquement le backend disponible."""

        if force_lmstudio:
            print("🔍 Mode force: LM Studio")
            success, _, error = self._request(f"{LM_STUDIO_URL}/api/v1/system/status")
            if success:
                self.backend = "lmstudio"
                self.base_url = LM_STUDIO_URL
                return True, "LM Studio detecte"
            return False, f"LM Studio non disponible: {error}"

        if force_ollama:
            print("🔍 Mode force: Ollama")
            success, _, error = self._request(f"{OLLAMA_URL}/api/tags")
            if success:
                self.backend = "ollama"
                self.base_url = OLLAMA_URL
                # Recuperer le premier modele disponible
                s2, data2, _ = self._request(f"{OLLAMA_URL}/api/tags")
                if s2 and data2 and "models" in data2 and data2["models"]:
                    self.model_name = data2["models"][0].get("name", "")
                return True, "Ollama detecte"
            return False, f"Ollama non disponible: {error}"

        # Detection automatique: LM Studio en priorite
        print("🔍 Detection automatique du backend...")

        # Tester LM Studio
        success, _, error = self._request(f"{LM_STUDIO_URL}/api/v1/system/status")
        if success:
            self.backend = "lmstudio"
            self.base_url = LM_STUDIO_URL
            print(f"  ✅ LM Studio detecte sur {LM_STUDIO_URL}")
            return True, "LM Studio detecte"

        # Tester Ollama
        success, data, error = self._request(f"{OLLAMA_URL}/api/tags")
        if success:
            self.backend = "ollama"
            self.base_url = OLLAMA_URL
            if data and "models" in data and data["models"]:
                self.model_name = data["models"][0].get("name", "")
            print(f"  ✅ Ollama detecte sur {OLLAMA_URL}")
            if self.model_name:
                print(f"     Modele par defaut: {self.model_name}")
            return True, "Ollama detecte"

        return False, (
            "Aucun backend LLM detecte.\n"
            "Verifiez que LM Studio (port 1234) ou Ollama (port 11434) est demarre."
        )

    def send_message(self, message: str, system_prompt: Optional[str] = None,
                     temperature: float = 0.7, max_tokens: int = 2048) -> Tuple[bool, str, Dict]:
        """Envoie un message au LLM detecte."""

        if self.backend == "lmstudio":
            return self._send_lmstudio(message, system_prompt, temperature, max_tokens)
        elif self.backend == "ollama":
            return self._send_ollama(message, system_prompt, temperature, max_tokens)
        else:
            return False, "Aucun backend detecte", {}

    def _send_lmstudio(self, message: str, system_prompt: Optional[str],
                       temperature: float, max_tokens: int) -> Tuple[bool, str, Dict]:
        """Envoie un message via l API LM Studio (OpenAI-compatible)."""
        print(f"💬 Envoi a LM Studio...")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})

        payload = {
            "model": "local-model",
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }

        url = f"{self.base_url}/v1/chat/completions"
        success, data, error = self._request(url, "POST", payload)

        if success and data and "choices" in data and len(data["choices"]) > 0:
            content = data["choices"][0].get("message", {}).get("content", "")
            usage = data.get("usage", {})
            msg = f"Reponse recue ({usage.get('completion_tokens', 0)} tokens)"
            print(f"  ✅ {msg}")
            return True, content, data
        else:
            msg = f"Echec: {error}"
            print(f"  ❌ {msg}")
            return False, msg, {}

    def _send_ollama(self, message: str, system_prompt: Optional[str],
                     temperature: float, max_tokens: int) -> Tuple[bool, str, Dict]:
        """Envoie un message via l API Ollama."""
        print(f"💬 Envoi a Ollama (modele: {self.model_name})...")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})

        payload = {
            "model": self.model_name or "llama3.2:3b",
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }

        url = f"{self.base_url}/api/chat"
        success, data, error = self._request(url, "POST", payload)

        if success and data and "message" in data:
            content = data["message"].get("content", "")
            eval_count = data.get("eval_count", 0)
            msg = f"Reponse recue ({eval_count} tokens generes)"
            print(f"  ✅ {msg}")
            return True, content, data
        else:
            msg = f"Echec: {error}"
            print(f"  ❌ {msg}")
            return False, msg, {}


def write_log(success: bool, backend: str, message: str, response: str,
              error: str = ""):
    """Ecrit le resultat dans le fichier log."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "=" * 70,
        "  ENVOYER_MESSAGE - LOG",
        "=" * 70,
        f"Date: {timestamp}",
        f"Backend: {backend.upper() if backend else 'NON DETECTE'}",
        f"Statut: {'SUCCES' if success else 'ECHEC'}",
        "",
        "-" * 70,
        "  MESSAGE ENVOYE",
        "-" * 70,
        message,
        "",
    ]

    if success:
        lines.extend([
            "-" * 70,
            "  REPONSE LLM",
            "-" * 70,
            response,
        ])
    else:
        lines.extend([
            "-" * 70,
            "  ERREUR",
            "-" * 70,
            error if error else "Erreur inconnue",
        ])

    lines.extend([
        "",
        "=" * 70,
    ])

    try:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"\n📝 Log enregistre: {os.path.abspath(LOG_FILE)}")
    except Exception as e:
        print(f"\n⚠️  Erreur ecriture log: {e}")


def main():
    """Point d entree principal."""

    # Analyse manuelle des arguments (pas d argparse pour garder la simplicite)
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help", "help"):
        print("""
╔══════════════════════════════════════════════════════════════════════╗
║              ENVOYER_MESSAGE - Client LLM Universel                  ║
╠══════════════════════════════════════════════════════════════════════╣
║  Envoie un message texte a un LLM local (LM Studio ou Ollama)       ║
║  Connexion automatique au premier serveur disponible                 ║
╠══════════════════════════════════════════════════════════════════════╣
║  USAGE:                                                              ║
║    python envoyer_message.py "votre message" [OPTIONS]               ║
║                                                                      ║
║  OPTIONS:                                                            ║
║    --lmstudio          Forcer l utilisation de LM Studio            ║
║    --ollama            Forcer l utilisation d Ollama                  ║
║    --system "PROMPT"   Definir un prompt systeme                      ║
║    --temperature N     Temperature (0.0-2.0, defaut: 0.7)            ║
║    --max-tokens N      Nombre max de tokens (defaut: 2048)           ║
║    --verbose           Mode verbeux                                   ║
║    --help              Afficher cette aide                            ║
╠══════════════════════════════════════════════════════════════════════╣
║  EXEMPLES:                                                           ║
║    python envoyer_message.py "Explique la relativite"                ║
║    python envoyer_message.py "Bonjour" --system "Sois concis"        ║
║    python envoyer_message.py "Test" --ollama                          ║
║    python envoyer_message.py "Test" --lmstudio --temperature 0.3      ║
╚══════════════════════════════════════════════════════════════════════╝
        """)
        sys.exit(0)

    # Extraire le message et les options
    message_parts = []
    force_lmstudio = False
    force_ollama = False
    system_prompt = None
    temperature = 0.7
    max_tokens = 2048
    verbose = False

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--lmstudio":
            force_lmstudio = True
        elif arg == "--ollama":
            force_ollama = True
        elif arg == "--system" and i + 1 < len(args):
            system_prompt = args[i + 1]
            i += 1
        elif arg == "--temperature" and i + 1 < len(args):
            try:
                temperature = float(args[i + 1])
            except ValueError:
                print(f"⚠️  Temperature invalide: {args[i + 1]}")
            i += 1
        elif arg == "--max-tokens" and i + 1 < len(args):
            try:
                max_tokens = int(args[i + 1])
            except ValueError:
                print(f"⚠️  Max tokens invalide: {args[i + 1]}")
            i += 1
        elif arg == "--verbose":
            verbose = True
        elif not arg.startswith("--"):
            message_parts.append(arg)
        i += 1

    if not message_parts:
        print("❌ Aucun message specifie. Utilisez --help pour l aide.")
        sys.exit(1)

    message = " ".join(message_parts)

    print(f"📝 Message: {message}")
    if system_prompt:
        print(f"🎯 Prompt systeme: {system_prompt}")
    print(f"🌡️  Temperature: {temperature}")
    print(f"📏 Max tokens: {max_tokens}")
    print()

    # Initialiser le client
    client = LLMClient(timeout=DEFAULT_TIMEOUT, verbose=verbose)

    # Detecter le backend
    success, detect_msg = client.detect_backend(force_lmstudio, force_ollama)

    if not success:
        print(f"\n❌ {detect_msg}")
        write_log(False, "", message, "", detect_msg)
        sys.exit(1)

    print(f"✅ {detect_msg}\n")

    # Envoyer le message
    success, response, data = client.send_message(
        message, system_prompt, temperature, max_tokens
    )

    # Afficher la reponse
    if success:
        print(f"\n🤖 Reponse du LLM:")
        print("-" * 60)
        print(response)
        print("-" * 60)
        write_log(True, client.backend or "", message, response)
        sys.exit(0)
    else:
        print(f"\n❌ Erreur: {response}")
        write_log(False, client.backend or "", message, "", response)
        sys.exit(1)


if __name__ == "__main__":
    main()
