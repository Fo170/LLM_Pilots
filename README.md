# 🚀 LLM_Pilots
LM_Studio_Pilot & Ollama_Pilot & envoyer_message

Applications de pilotage complet pour LLMs locaux via **LM Studio** et **Ollama**.  
Un seul fichier Python chacune, **aucune dépendance externe** (bibliothèque standard uniquement).

---

## 📑 Table des matières

- [Auteur et Licence](#auteur-et-licence)
- [Aperçu](#aperçu)
- [Comparaison rapide](#comparaison-rapide)
- [envoyer_message.py](#envoyer_messagepy)
  - [Utilisation](#utilisation-envoyer)
  - [Détection automatique](#détection-automatique)
  - [Comment ça marche ?](#comment-ça-marche)
  - [Limite de taille de réponse](#limite-de-taille-de-réponse)
  - [Référence CLI](#référence-cli-envoyer)
- [LM_Studio_Pilot.py](#lm-studio-pilot)
  - [Installation](#installation-lm-studio)
  - [Configuration LM Studio](#configuration-lm-studio)
  - [Utilisation](#utilisation-lm-studio)
  - [Référence CLI](#référence-cli-lm-studio)
- [Ollama_Pilot.py](#ollamapilot)
  - [Installation](#installation-ollama)
  - [Configuration Ollama](#configuration-ollama)
  - [Utilisation](#utilisation-ollama)
  - [Référence CLI](#référence-cli-ollama)
- [Format du log](#format-du-log)
- [Architecture](#architecture)
- [Dépannage](#dépannage)
- [Licence](#licence)

---

## 👤 Auteur et Licence

| | |
|---|---|
| **Auteur** | FOURNET Olivier |
| **Email** | olivier.fournet@free.fr |
| **Licence** | GPL-3.0 license |
| **Repository** | https://github.com/Fo170/LLM_Pilots |
| **Date** | 2026-05-17 |

---

## 🎯 Aperçu

| | **envoyer_message.py** | **LM_Studio_Pilot.py** | **Ollama_Pilot.py** |
|---|---|---|---|
| **Complexité** | Simple | Avancée | Avancée |
| **Cible** | LM Studio + Ollama | LM Studio | Ollama |
| **Détection auto** | ✅ Oui (les deux) | ❌ Non | ❌ Non |
| **Port par défaut** | `1234` / `11434` | `1234` | `11434` |
| **API** | OpenAI + Native | OpenAI-compatible + Native | Native REST |
| **Fichier** | `envoyer_message.py` | `lm_studio_pilot.py` | `ollama_pilot.py` |
| **Lignes** | ~367 | ~865 | ~1016 |
| **Classes** | 1 | 3 | 3 |
| **Fonctions** | Envoi message uniquement | Gestion complète | Gestion complète |
| **Dépendances** | Aucune | Aucune | Aucune |

---

## 📊 Comparaison rapide

### Quand utiliser quel fichier ?

| Besoin | Fichier recommandé |
|---|---|
| Envoyer rapidement un message | `envoyer_message.py` |
| Détection auto du serveur | `envoyer_message.py` |
| Gérer les modèles (charger/décharger) | `lm_studio_pilot.py` ou `ollama_pilot.py` |
| Voir l'utilisation du contexte | `lm_studio_pilot.py` ou `ollama_pilot.py` |
| Télécharger un nouveau modèle | `lm_studio_pilot.py` ou `ollama_pilot.py` |
| Pipeline complet (load → chat → unload) | `lm_studio_pilot.py` ou `ollama_pilot.py` |

### Fonctionnalités communes aux trois applications

| Fonctionnalité | envoyer_message.py | LM_Studio_Pilot.py | Ollama_Pilot.py |
|---|---|---|---|
| ✅ Connexion auto | Oui (détecte les deux) | Oui | Oui |
| ✅ Envoyer message | Oui | Oui | Oui |
| ✅ Prompt système | Oui | Oui | Oui |
| ✅ Température | Oui | Oui | Oui |
| ✅ Max tokens | Oui | Oui | Oui |
| ✅ Fichier log | Oui | Oui | Oui |
| ✅ Mode verbeux | Oui | Oui | Oui |
| ✅ Lister modèles | Non | Oui | Oui |
| ✅ Charger modèle | Non | Oui | Oui |
| ✅ Décharger modèle | Non | Oui | Oui |
| ✅ Télécharger modèle | Non | Oui | Oui |
| ✅ Infos contexte | Non | Oui | Oui |
| ✅ Statut serveur | Non | Oui | Oui |
| ✅ Infos système | Non | Oui | Oui |

---

## 💬 envoyer_message.py

Application **simple et universelle** pour envoyer des messages à un LLM local.  
Détecte automatiquement **LM Studio** (port 1234) ou **Ollama** (port 11434).

### Utilisation envoyer_message

```bash
# 🔍 Détection automatique (LM Studio prioritaire, puis Ollama)
python envoyer_message.py "Explique la relativité restreinte"

# 🎯 Forcer LM Studio
python envoyer_message.py "Bonjour" --lmstudio

# 🎯 Forcer Ollama
python envoyer_message.py "Bonjour" --ollama

# 🎯 Avec prompt système
python envoyer_message.py "Explique la relativité" --system "Sois très concis"

# 🎯 Paramètres avancés
python envoyer_message.py "Test" --temperature 0.3 --max-tokens 500

# 🎯 Mode verbeux
python envoyer_message.py "Test" --verbose
```

### Détection automatique

Le script tente la connexion dans cet ordre :

1. **LM Studio** sur `http://127.0.0.1:1234`
   - Test via `/api/v1/system/status`
   - Si succès → utilise l'API OpenAI-compatible

2. **Ollama** sur `http://127.0.0.1:11434`
   - Test via `/api/tags`
   - Si succès → utilise l'API native Ollama
   - Récupère automatiquement le premier modèle disponible

3. **Échec** si aucun serveur ne répond

### Comment ça marche ?

Quand vous envoyez un message, voici ce qui se passe en coulisses :

#### 1. Envoi du message

Votre message est encapsulé dans un objet JSON et envoyé au serveur LLM :

**Pour LM Studio (API OpenAI-compatible) :**
```json
{
  "model": "local-model",
  "messages": [
    {"role": "system", "content": "Tu es un assistant utile"},
    {"role": "user", "content": "Explique la relativité"}
  ],
  "temperature": 0.7,
  "max_tokens": 2048,
  "stream": false
}
```

**Pour Ollama (API native) :**
```json
{
  "model": "llama3.2:3b",
  "messages": [
    {"role": "system", "content": "Tu es un assistant utile"},
    {"role": "user", "content": "Explique la relativité"}
  ],
  "stream": false,
  "options": {
    "temperature": 0.7,
    "num_predict": 2048
  }
}
```

#### 2. Réception de la réponse

Le serveur LLM génère une réponse textuelle et la renvoie :

**Réponse de LM Studio :**
```json
{
  "choices": [{
    "message": {
      "role": "assistant",
      "content": "La relativité restreinte, formulée par Einstein en 1905, établit que..."
    }
  }],
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 150,
    "total_tokens": 165
  }
}
```

**Réponse d'Ollama :**
```json
{
  "message": {
    "role": "assistant",
    "content": "La relativité restreinte, formulée par Einstein en 1905, établit que..."
  },
  "done": true,
  "eval_count": 150,
  "total_duration": 2500000000
}
```

#### 3. Extraction du contenu

Le script extrait le texte généré par le LLM :

| Backend | Champ extrait | Description |
|---|---|---|
| **LM Studio** | `choices[0].message.content` | Texte généré par l'assistant |
| **Ollama** | `message.content` | Texte généré par l'assistant |

#### 4. Affichage et log

Le texte est affiché dans le terminal et sauvegardé dans `log_message.txt` :

```
🤖 Reponse du LLM:
------------------------------------------------------------
La relativité restreinte, formulée par Einstein en 1905, 
établit que la vitesse de la lumière dans le vide est 
constante pour tous les observateurs...
------------------------------------------------------------
```

> **⚠️ Important** : La réponse affichée et loguée est bien **le contenu textuel généré par le LLM** en réponse à votre question, pas un simple statut technique. Le statut (succès/échec) est utilisé en interne pour vérifier que l'appel HTTP a fonctionné, mais ce qui vous est présenté est le `content` — la réponse intellectuelle du modèle.

### Limite de taille de réponse

La taille de la réponse est **limitée** mais **configurable** via `--max-tokens` :

| Application | Paramètre | Défaut | Description |
|---|---|---|---|
| `envoyer_message.py` | `--max-tokens` | **2048** | Tokens max dans la réponse |
| `lm_studio_pilot.py` | `--max-tokens` | **2048** | Tokens max dans la réponse |
| `ollama_pilot.py` | `--max-tokens` | **2048** | Tokens max dans la réponse |

#### Comment ça fonctionne dans le code

**Pour LM Studio :**
```python
payload = {
    "max_tokens": 2048,  # ← Limite de la réponse
    # ... autres paramètres
}
```

**Pour Ollama :**
```python
payload = {
    "options": {
        "num_predict": 2048,  # ← Limite de la réponse
    }
}
```

#### Points importants

| Aspect | Détail |
|---|---|
| **Token ≠ Mot** | 1 token ≈ 0.75 mot en anglais, ≈ 0.5 mot en français |
| **Limite serveur** | Le serveur LLM peut aussi imposer sa propre limite |
| **Contexte total** | `max_tokens` + tokens du message d'entrée ≤ contexte total du modèle |
| **Valeur 0** | `max_tokens: 0` ou `-1` = illimité (selon le backend) |

#### Estimation rapide

| `max_tokens` | Taille approximative réponse |
|---|---|
| 100 | ~75 mots anglais / ~50 mots français |
| 512 | ~380 mots anglais / ~250 mots français |
| 2048 (défaut) | ~1500 mots anglais / ~1000 mots français |
| 4096 | ~3000 mots anglais / ~2000 mots français |

#### Exemples pratiques

```bash
# Réponse très courte (1 phrase)
python envoyer_message.py "Définis 'relativité' en une phrase" --max-tokens 50

# Réponse moyenne (paragraphe)
python envoyer_message.py "Explique la relativité" --max-tokens 500

# Réponse longue (article complet)
python envoyer_message.py "Explique la relativité en détail" --max-tokens 4096
```

> **💡 Astuce** : Si la réponse semble coupée ou incomplète, augmentez `--max-tokens` !

### Référence CLI envoyer_message.py

| Option | Description |
|---|---|
| `--lmstudio` | Forcer l'utilisation de LM Studio |
| `--ollama` | Forcer l'utilisation d'Ollama |
| `--system "PROMPT"` | Définir un prompt système |
| `--temperature N` | Température (0.0-2.0, défaut: 0.7) |
| `--max-tokens N` | Nombre max de tokens (défaut: 2048) |
| `--verbose` | Mode verbeux (affiche les requêtes HTTP) |
| `--help` | Afficher l'aide |

---

## 🔷 LM_Studio_Pilot.py

### Installation LM Studio

```bash
# 1. Télécharger LM Studio depuis https://lmstudio.ai
# 2. Lancer l'application
# 3. Charger un modèle dans l'interface
# 4. Activer le serveur API (icône 🌐 → "Start Server")
```

### Configuration LM Studio

| Paramètre | Valeur par défaut | Description |
|---|---|---|
| URL | `http://127.0.0.1:1234` | Endpoint API |
| Authentification | Désactivée | Token optionnel |
| Port | `1234` | Configurable dans LM Studio |

### Utilisation LM_Studio_Pilot.py

```bash
# 🔌 Vérifier la connexion
python lm_studio_pilot.py --status

# 📋 Lister les modèles disponibles
python lm_studio_pilot.py --list

# 📥 Charger un modèle
python lm_studio_pilot.py --load qwen/qwen3-4b-2507 --context-length 4096

# 📤 Décharger un modèle
python lm_studio_pilot.py --unload qwen/qwen3-4b-2507

# 💬 Envoyer un message
python lm_studio_pilot.py --send "Explique la relativité" --system "Sois concis"

# 🔄 Pipeline complet
python lm_studio_pilot.py --load qwen/qwen3-4b-2507 --send "Bonjour" --unload

# 📊 Infos contexte
python lm_studio_pilot.py --context-usage
python lm_studio_pilot.py --context-length-info

# 📥 Télécharger un modèle
python lm_studio_pilot.py --download microsoft/Phi-4-mini-instruct
```

### Référence CLI LM_Studio_Pilot.py

| Groupe | Option | Description |
|---|---|---|
| **📦 Modèles** | `--load MODEL` | Charger un modèle |
| | `--unload [MODEL]` | Décharger (sans arg = tous) |
| | `--download MODEL` | Télécharger depuis HuggingFace |
| | `--list, -l` | Lister modèles locaux |
| | `--loaded` | Voir modèles chargés |
| | `--context-length N` | Longueur contexte (avec `--load`) |
| | `--gpu [max\|off\|N]` | Config GPU |
| **💬 Chat** | `--send "MSG"` | Envoyer message |
| | `--system "PROMPT"` | Prompt système |
| | `--temperature FLOAT` | Température (0.0-2.0) |
| | `--max-tokens N` | Tokens max |
| | `--stream` | Streaming temps réel |
| **📊 Infos** | `--info, -i` | Infos modèle chargé |
| | `--context-usage` | % utilisation contexte |
| | `--context-length-info` | Longueur totale contexte |
| | `--status` | Statut serveur |
| | `--system-info` | RAM, GPU, OS |
| **⚙️ Options** | `--url URL` | URL LM Studio |
| | `--token TOKEN` | Token API |
| | `--timeout N` | Timeout (s) |
| | `--verbose, -v` | Mode verbeux |
| | `--no-log` | Pas de fichier log |
| | `--log-file FILE` | Nom du log |
| **❓ Aide** | `--help, -h` | Aide |
| | `--examples` | Exemples d'usage |

---

## 🟢 Ollama_Pilot.py

### Installation Ollama

```bash
# macOS / Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows
# Télécharger depuis https://ollama.com/download

# Démarrer le serveur
ollama serve
```

### Configuration Ollama

| Paramètre | Valeur par défaut | Description |
|---|---|---|
| URL | `http://127.0.0.1:11434` | Endpoint API |
| Authentification | Désactivée | Token optionnel |
| Port | `11434` | Configurable via env |

### Utilisation Ollama_Pilot.py

```bash
# 🔌 Vérifier la connexion
python ollama_pilot.py --status

# 📋 Lister les modèles disponibles
python ollama_pilot.py --list

# 📥 Charger un modèle
python ollama_pilot.py --model llama3.2:3b --load
python ollama_pilot.py --model llama3.2:3b --load --keep-alive 30m

# 📤 Décharger un modèle
python ollama_pilot.py --model llama3.2:3b --unload

# 💬 Envoyer un message (chat)
python ollama_pilot.py --model llama3.2:3b --send "Explique la relativité"
python ollama_pilot.py --model llama3.2:3b --send "Bonjour" --system "Sois concis"

# 📝 Génération simple
python ollama_pilot.py --model llama3.2:3b --generate "Écris un poème"

# 🔄 Pipeline complet
python ollama_pilot.py --model llama3.2:3b --load --send "Bonjour" --unload

# 📊 Infos
python ollama_pilot.py --model llama3.2:3b --info
python ollama_pilot.py --model llama3.2:3b --context-usage
python ollama_pilot.py --running
python ollama_pilot.py --version

# 📥 Télécharger un modèle
python ollama_pilot.py --model llama3.2:3b --download

# 🗑️ Supprimer un modèle
python ollama_pilot.py --model llama3.2:3b --delete
```

### Référence CLI Ollama_Pilot.py

| Groupe | Option | Description |
|---|---|---|
| **📦 Modèles** | `--model, -m MODEL` | Spécifier le modèle |
| | `--load` | Charger en mémoire |
| | `--unload` | Décharger de la mémoire |
| | `--download` | Télécharger depuis le registry |
| | `--delete` | Supprimer le modèle local |
| | `--list, -l` | Lister modèles locaux |
| | `--running` | Voir modèles en VRAM |
| | `--info, -i` | Infos détaillées |
| | `--keep-alive DUREE` | Durée conservation mémoire |
| **💬 Chat** | `--send "MSG"` | Envoyer message (chat) |
| | `--generate "PROMPT"` | Génération simple |
| | `--system "PROMPT"` | Prompt système |
| | `--temperature FLOAT` | Température (0.0-2.0) |
| | `--max-tokens N` | Tokens max |
| | `--stream` | Streaming temps réel |
| **📊 Infos** | `--context-usage` | Utilisation contexte |
| | `--status` | Statut serveur |
| | `--version, -v` | Version Ollama |
| **⚙️ Options** | `--url URL` | URL Ollama |
| | `--token TOKEN` | Token API |
| | `--timeout N` | Timeout (s) |
| | `--verbose` | Mode verbeux |
| | `--no-log` | Pas de fichier log |
| | `--log-file FILE` | Nom du log |
| **❓ Aide** | `--help, -h` | Aide |
| | `--examples` | Exemples d'usage |

---

## 📄 Format du log

Les trois applications génèrent un fichier `log_message.txt` (configurable) :

### envoyer_message.py

```
======================================================================
  ENVOYER_MESSAGE - LOG
======================================================================
Date: 2026-05-17 22:33:00
Backend: LM STUDIO
Statut: SUCCES

----------------------------------------------------------------------
  MESSAGE ENVOYE
----------------------------------------------------------------------
Explique la relativité

----------------------------------------------------------------------
  REPONSE LLM
----------------------------------------------------------------------
La relativité restreinte, formulée par Einstein en 1905...

======================================================================
```

### LM_Studio_Pilot.py / Ollama_Pilot.py

```
======================================================================
  [LM_STUDIO_PILOT.py / OLLAMA_PILOT.py] - LOG
======================================================================
Date: 2026-05-17 22:05:30
Commande: --load qwen/qwen3-4b-2507 --send "Bonjour" --unload
URL: http://127.0.0.1:1234

----------------------------------------------------------------------
  OPERATIONS
----------------------------------------------------------------------
[22:05:30] [LOAD] qwen/qwen3-4b-2507 -> SUCCES
           Modele charge avec succes
[22:05:32] [SEND] Bonjour -> SUCCES
           Reponse recue (15 tokens)
[22:05:35] [UNLOAD] qwen/qwen3-4b-2507 -> SUCCES
           Modele decharge

----------------------------------------------------------------------
  STATUT FINAL
----------------------------------------------------------------------
SUCCES: Toutes les operations ont reussi
Code de sortie: 0

----------------------------------------------------------------------
  REPONSE LLM
----------------------------------------------------------------------
Bonjour ! Comment puis-je vous aider aujourd'hui ?

======================================================================
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    [APPLICATIONS PYTHON - 1 FICHIER CHACUNE]         │
│                                                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐   │
│  │ envoyer_message.py │  │ LM_Studio_Pilot.py   │  │ Ollama_Pilot.py     │   │
│  │                 │  │                   │  │                 │   │
│  │ • Detection auto│  │ • [Pilot]         │  │ • [Pilot]       │   │
│  │ • Envoi simple  │  │   HTTP/API        │  │   HTTP/API      │   │
│  │ • Log resultat  │  │ • [Logger]        │  │ • [Logger]      │   │
│  │                 │  │   log_message.txt │  │   log_message   │   │
│  │                 │  │ • [CLI]           │  │ • [CLI]         │   │
│  │                 │  │   argparse        │  │   argparse      │   │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘   │
│         │                      │                      │            │
│         └──────────────────────┼──────────────────────┘            │
│                                │                                   │
│                         ┌──────────────┐                         │
│                         │  LLM Local   │                         │
│                         │  LM Studio   │                         │
│                         │  ou Ollama   │                         │
│                         └──────────────┘                         │
└─────────────────────────────────────────────────────────────────────┘
```

### Classes par application

| Application | Classes | Rôle |
|---|---|---|
| **envoyer_message.py** | `LLMClient` | Détection backend, requêtes HTTP, envoi message |
| **lm_studio_pilot.py** | `LMStudioPilot` | Requêtes HTTP, gestion modèles, chat, monitoring |
| | `Logger` | Écriture du fichier `log_message.txt` |
| | `CLI` | Parsing arguments, exécution commandes |
| **ollama_pilot.py** | `OllamaPilot` | Requêtes HTTP, gestion modèles, chat, monitoring |
| | `Logger` | Écriture du fichier `log_message.txt` |
| | `CLI` | Parsing arguments, exécution commandes |

---

## 🔧 Dépannage

### Problème commun : Connexion refusée

**envoyer_message.py :**
```bash
❌ Aucun backend LLM detecte.
```
→ **Solution** : Vérifier que LM Studio (port 1234) ou Ollama (port 11434) est démarré

**LM Studio :**
```bash
❌ LM Studio ne repond pas sur http://127.0.0.1:1234
```
→ **Solution** : Activer le serveur API dans LM Studio (icône 🌐 → "Start Server")

**Ollama :**
```bash
❌ Ollama ne repond pas sur http://127.0.0.1:11434
```
→ **Solution** : Démarrer le serveur avec `ollama serve`

### Vérifier les endpoints

**LM Studio :**
```bash
curl http://localhost:1234/api/v1/models
curl http://localhost:1234/api/v1/system/status
```

**Ollama :**
```bash
curl http://localhost:11434/api/tags
curl http://localhost:11434/api/version
```

### Mode verbeux

Ajouter `--verbose` (ou `-v` pour LM Studio) pour voir les requêtes HTTP :

```bash
python envoyer_message.py "Test" --verbose
python lm_studio_pilot.py --status --verbose
python ollama_pilot.py --status --verbose
```

---

## 📜 Licence

Ces applications sont distribuées sous la licence **GPL-3.0**.

| | |
|---|---|
| **Auteur** | FOURNET Olivier |
| **Email** | olivier.fournet@free.fr |
| **Licence** | GPL-3.0 license |
| **Repository** | https://github.com/Fo170/LLM_Pilots |
| **Date** | 2026-05-17 |

Cette licence garantit votre liberté d'utiliser, d'étudier, de modifier et de redistribuer ces applications, à condition que toute œuvre dérivée reste également sous GPL-3.0.

Pour plus de détails, consultez le fichier [LICENSE](https://www.gnu.org/licenses/gpl-3.0.html) ou visitez le repository GitHub.

---

**Généré le :** 2026-05-17  
**Auteur :** FOURNET Olivier  
**Contact :** olivier.fournet@free.fr
