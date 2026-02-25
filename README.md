# Simulateur de procédés de traitement des eaux

Simulateur modulaire de procédés de traitement des eaux usées permettant d'évaluer l'efficacité d'épuration (DCO, azote, phosphore), la consommation énergétique et les performances de différentes chaînes de traitement.

---

## Table des matières

- [Prérequis](#prérequis)
- [Installation](#installation)
- [Utilisation rapide](#utilisation-rapide)
- [Architecture](#architecture)
- [Modèles disponibles](#modèles-disponibles)
- [Procédés disponibles](#procédés-disponibles)
- [Configuration](#configuration)
- [Connexions entre procédés](#connexions-entre-procédés)
- [Sorties](#sorties)
- [Tests](#tests)
- [Limitations connues](#limitations-connues)
- [Étendre le simulateur](#étendre-le-simulateur)

---

## Prérequis

- Python **3.10+**
- pip

Dépendances principales : `numpy`, `scipy`, `pandas`, `plotly`, `scikit-learn`, `tensorflow` (voir `requirements.txt` pour les versions exactes).

---

## Installation

```bash
git clone https://github.com/neesegit/simulation.git
cd simulation
python3 -m venv venv
source venv/bin/activate  # Windows : venv\Scripts\activate
pip install -r requirements.txt
```

---

## Utilisation rapide

```bash
# Mode interactif
python main.py -i

# Lancer une simulation avec un fichier de configuration
python main.py config/ma_config.json

# Sans générer les graphiques (plus rapide)
python main.py config/ma_config.json --no-plots

# Mode debug
python main.py config/ma_config.json --log-level DEBUG

# Aide
python main.py --help
```

### Exemple de sortie console

```
============================================================
Simulation en cours ...
============================================================
2026-02-23 13:59:24,740 - INFO - Simulation : 240 pas de temps
2026-02-23 13:59:24,784 - INFO - 41.7% complété
2026-02-23 13:59:24,819 - INFO - 83.3% complété

============================================================
Simulation terminée
============================================================
Export des métriques de performance ...
        - Métriques JSON : performance_metrics_20260223_135925.json
        - Métriques CSV : 1 fichier(s)
        - Rapport : performance_report.txt
        - Répertoire : output\results\simulation_20251208_115818

Génération des graphiques ...

============================================================
Résumé des résultats
============================================================

Période simulée :
        De : 2025-12-08 00:00:00
        A : 2025-12-09 00:00:00
        Pas de temps : 0.1 heures
        Total : 240 pas

Statistiques par procédé :

        influent :
                Debit moyen :   1000.0 m^3/h
                DCO moyenne :     500.0 mg/L

        bassin_1 :
                Debit moyen :   1000.0 m^3/h
                DCO moyenne :    1717.5 mg/L
                Échantillons :      240

============================================================
```

---

## Architecture

Le simulateur est organisé autour de quatre concepts clés :

```
Influent (FlowData)
     │
     ▼
┌─────────────────────────────────────────────────┐
│              SimulationOrchestrator             │
│                                                 │
│  ConnectionManager   ──►  ordre d'exécution     │
│                                                 │
│  ProcessNode #1  ──►  ProcessNode #2  ──►  ...  │
│  (boues activées)     (décanteur)               │
│       │                    │                    │
│   DataBus  ◄───────────────┘                    │
└─────────────────────────────────────────────────┘
     │
     ▼
SimulationFlow (historique) ──► Résultats / Graphiques
```

**`ProcessNode`** — unité de traitement (boues activées, décanteur…). Chaque nœud reçoit un `FlowData` en entrée, exécute son modèle, et écrit ses sorties dans le `DataBus`.

**`ModelRegistry`** — registre singleton qui charge dynamiquement les modèles depuis les fichiers JSON de `core/model/config/`. Il instancie la bonne classe Python selon le champ `module` / `class`.

**`ConnectionManager`** — gère le graphe de connexions entre nœuds. Calcule l'ordre d'exécution via un tri topologique (algorithme de Kahn), en ignorant les arcs de recyclage pour éviter les cycles bloquants.

**`DataBus`** — bus de communication partagé. Chaque nœud y écrit son `FlowData` de sortie ; le nœud suivant le lit pour construire ses entrées.

### Structure des fichiers

```
.
├── config/              # Fichiers de configuration JSON
├── core/
│   ├── connection/      # Graphe de connexions (ConnectionManager)
│   ├── data/            # FlowData, DataBus, SimulationFlow
│   ├── model/           # ModelRegistry + fichiers JSON des modèles
│   ├── orchestrator/    # SimulationOrchestrator
│   ├── process/         # ProcessRegistry + fichiers JSON des procédés
│   ├── registries/
│   │   ├── metrics/
│   │   │   ├── calculators/   # HRT, SRT, SVI, énergie, composite…
│   │   │   ├── config/        # model_metrics.json, calculators.json
│   │   │   └── registry.py    # MetricsRegistry
│   │   ├── fractionation/
│   │   │   ├── strategies/    # ASM1, ASM2D, ASM3, NoFractionation
│   │   │   ├── config/        # model_strategies.json
│   │   │   └── registry.py    # FractionationRegistry
│   │   └── export/
│   │       ├── strategies/    # CSV, JSON, Excel, Parquet
│   │       ├── config/        # default_formats.json
│   │       └── registry.py    # ExportRegistry
│   └── solver/          # Solveurs ODE (Euler, RK4), CSTR, settler
├── models/
│   ├── empyrical/       # ASM1, ASM2d, ASM3, Takacs
│   └── ml/              # LinearModel, RandomForest
├── models/trained/      # Modèles ML entraînés (fichiers .pkl)
├── processes/
│   ├── sludge_process/  # UnifiedActivatedSludgeProcess
│   └── settler_process/ # SecondarySettlerProcess
├── interfaces/
│   ├── cli/             # Interface interactive
│   ├── config/          # Chargement et validation des configs
│   └── visualisation/   # Dashboards Plotly par modèle
├── data/
│   ├── raw/             # Données brutes (non modifiées)
│   └── processed/       # Données prêtes à l'entraînement (CSV générés)
├── tools/
│   ├── generate_training_data.py  # Génère un CSV via simulations ASM1
│   └── train_ml_model.py          # Entraîne un modèle ML et sauvegarde le pickle
├── tests/               # Tests unitaires et d'intégration (pytest)
├── utils/
├── main.py
└── requirements.txt
```

---

## Modèles disponibles

### Modèles empiriques (mécanistes)

| ID | Classe | Composants | Processus | Phosphore |
|----|--------|-----------|-----------|-----------|
| `asm1` | `ASM1Model` | 13 | 8 | ✗ |
| `asm2d` | `ASM2dModel` | 19 | 21 | ✓ |
| `asm3` | `ASM3Model` | 13 | 12 | ✗ |
| `takacs` | `TakacsModel` | *n* couches | — | — |

Ces modèles résolvent des EDO via un solveur RK4 à chaque pas de temps. L'influent brut (DCO, MES, TKN…) est automatiquement **fractionné** en composants internes avant simulation.

### Modèles Machine Learning

| ID | Classe | Description |
|----|--------|-------------|
| `linear` | `LinearModel` | Régression linéaire |
| `randomforest` | `RandomForestModel` | Forêt aléatoire (scikit-learn) |

Ces modèles prédictent la qualité de l'effluent (DCO, NH4, MES…) à partir des conditions d'entrée (débit, température, qualité de l'influent, HRT, SRT). Ils constituent des **modèles de substitution** (surrogates) entraînés à reproduire le comportement des modèles mécanistes ou de données réelles.

**Workflow d'entraînement :**

```bash
# 1. Générer des données d'entraînement via simulations ASM1
python tools/generate_training_data.py --n 1000
# → data/processed/asm1_training_data.csv

# 2. Entraîner le modèle et sauvegarder le pickle
python tools/train_ml_model.py --model LinearModel
python tools/train_ml_model.py --model RandomForestModel
# → models/trained/linear.pkl / randomforest.pkl

# 3. Référencer le pickle dans la config de simulation
```

```json
"config": {
  "model": "LinearModel",
  "model_path": "models/trained/linear.pkl"
}
```

> Si `model_path` est absent, le modèle est automatiquement entraîné sur des données synthétiques au démarrage — comportement de secours, qualité réduite.

> Les scripts `tools/` sont isolés du reste de la simulation. Ils deviennent inutiles dès que des données réelles sont disponibles : remplacer le CSV d'entrée de `train_ml_model.py` par les données réelles (mêmes colonnes), régénérer le pickle.

**Visualisation :** les modèles ML affichent un dashboard de type *snapshot* (influent vs effluent, taux d'épuration, HRT/SRT) plutôt qu'une série temporelle, car le modèle prédit un état stationnaire à chaque pas.

---

## Procédés disponibles

| Type (`type`) | Classe | Description |
|---------------|--------|-------------|
| `ActivatedSludgeProcess` | `UnifiedActivatedSludgeProcess` | Réacteur CSTR — supporte ASM1/2d/3 et modèles ML |
| `SecondarySettlerProcess` | `SecondarySettlerProcess` | Décanteur secondaire — modèle de Takacs |

---

## Configuration

La simulation est pilotée par un fichier JSON.

### Paramètres globaux

| Champ | Obligatoire | Description |
|-------|-------------|-------------|
| `name` | ✓ | Identifiant de la simulation (utilisé pour nommer les fichiers de sortie) |
| `description` | | Description libre |
| `simulation.start_time` | ✓ | Début de la simulation (ISO 8601, ex. `"2025-01-01T00:00:00"`) |
| `simulation.end_time` | ✓ | Fin de la simulation (ISO 8601) |
| `simulation.timestep_hours` | | Pas de temps en heures (défaut : `0.1`) |

### Paramètres de l'influent

| Champ | Description |
|-------|-------------|
| `flowrate` | Débit entrant (m³/h) |
| `temperature` | Température (°C) |
| `composition` | Paramètres mesurables de l'effluent brut (mg/L) |

Paramètres de composition reconnus : `cod`, `ss` (MES), `tkn`, `nh4`, `no3`, `po4`, `alkalinity`.

### Structure minimale

```json
{
  "name": "ma_simulation",
  "simulation": {
    "start_time": "2025-01-01T00:00:00",
    "end_time":   "2025-01-02T00:00:00",
    "timestep_hours": 0.1
  },
  "influent": {
    "flowrate": 1000.0,
    "temperature": 20.0,
    "auto_fractionate": true,
    "composition": {
      "cod": 500.0,
      "ss":  250.0,
      "tkn":  40.0,
      "nh4":  28.0,
      "no3":   0.5,
      "po4":   8.0,
      "alkalinity": 6.0
    }
  },
  "processes": [
    {
      "node_id": "bassin_1",
      "type": "ActivatedSludgeProcess",
      "name": "Boues activées #1",
      "config": {
        "model": "ASM1Model",
        "volume": 5000.0,
        "dissolved_oxygen_setpoint": 2.0,
        "depth": 4.0,
        "recycle_ratio": 1.0,
        "waste_ratio": 0.01
      }
    }
  ],
  "connections": [
    {
      "source": "influent",
      "target": "bassin_1",
      "fraction": 1.0,
      "is_recycle": false
    }
  ]
}
```

### Paramètres de procédé — boues activées

| Paramètre | Obligatoire | Défaut | Description |
|-----------|-------------|--------|-------------|
| `model` | ✓ | `ASM1Model` | Modèle biologique |
| `volume` | ✓ | `5000.0` | Volume du bassin (m³) |
| `dissolved_oxygen_setpoint` | ✓ | `2.0` | Consigne OD (mg/L) |
| `depth` | | `4.0` | Profondeur (m) |
| `recycle_ratio` | | `1.0` | Ratio Qrecycle/Qin — débit de recyclage interne |
| `waste_ratio` | | `0.01` | Ratio Qwaste/Qin — fraction du débit éliminée comme boues en excès |
| `model_path` | | `null` | Chemin modèle ML pré-entraîné |

### Paramètres de procédé — décanteur secondaire

| Paramètre | Obligatoire | Défaut | Description |
|-----------|-------------|--------|-------------|
| `area` | ✓ | `1000.0` | Surface (m²) |
| `depth` | ✓ | `4.0` | Profondeur (m) |
| `n_layers` | | `10` | Nombre de couches |
| `underflow_ratio` | | `0.5` | Ratio Qunderflow/Qin |
| `feed_layer_ratio` | | `0.5` | Position alimentation (0=fond, 1=surface) |

---

## Connexions entre procédés

Le simulateur supporte des topologies arbitraires : chaîne simple, dérivations parallèles, recyclages.

Chaque connexion est définie par :

| Champ | Description |
|-------|-------------|
| `source` | ID du nœud source (`"influent"` ou un `node_id`) |
| `target` | ID du nœud cible |
| `fraction` | Fraction du débit transmise (0 < fraction ≤ 1.0) |
| `is_recycle` | `true` si c'est un recyclage (ignoré dans le tri topologique) |

### Exemple — chaîne série simple

```
influent ──► bassin_1 ──► decanteur_1
```

```json
"connections": [
  { "source": "influent",    "target": "bassin_1",    "fraction": 1.0, "is_recycle": false },
  { "source": "bassin_1",    "target": "decanteur_1", "fraction": 1.0, "is_recycle": false }
]
```

### Exemple — boues activées avec décanteur et recyclage

Configuration typique d'une station d'épuration : le décanteur concentre les boues, dont une partie est recyclée vers le bassin pour maintenir un SRT > HRT.

```
influent ──► bassin_1 ──► decanteur_1 ──► effluent traité
                ▲               │
                └── recyclage ──┘ (boues recirculées)
```

```json
{
  "name": "step_avec_recyclage",
  "simulation": {
    "start_time": "2025-01-01T00:00:00",
    "end_time":   "2025-01-02T00:00:00",
    "timestep_hours": 0.1
  },
  "influent": {
    "flowrate": 1000.0,
    "temperature": 20.0,
    "auto_fractionate": true,
    "composition": {
      "cod": 500.0, "ss": 250.0, "tkn": 40.0,
      "nh4": 28.0, "no3": 0.5, "po4": 8.0, "alkalinity": 6.0
    }
  },
  "processes": [
    {
      "node_id": "bassin_1",
      "type": "ActivatedSludgeProcess",
      "name": "Bassin aération",
      "config": {
        "model": "ASM1Model",
        "volume": 5000.0,
        "dissolved_oxygen_setpoint": 2.0,
        "recycle_ratio": 1.0,
        "waste_ratio": 0.005
      }
    },
    {
      "node_id": "decanteur_1",
      "type": "SecondarySettlerProcess",
      "name": "Décanteur secondaire",
      "config": {
        "area": 1000.0,
        "depth": 4.0,
        "n_layers": 10,
        "underflow_ratio": 0.6
      }
    }
  ],
  "connections": [
    { "source": "influent",    "target": "bassin_1",    "fraction": 1.0, "is_recycle": false },
    { "source": "bassin_1",    "target": "decanteur_1", "fraction": 1.0, "is_recycle": false },
    { "source": "decanteur_1", "target": "bassin_1",    "fraction": 0.6, "is_recycle": true  }
  ]
}
```

### Exemple — dérivation parallèle

```
                ┌──► bassin_2 ──┐
influent ──► bassin_1           ├──► bassin_4
                └──► bassin_3 ──┘
```

```json
"connections": [
  { "source": "influent", "target": "bassin_1", "fraction": 1.0, "is_recycle": false },
  { "source": "bassin_1", "target": "bassin_2", "fraction": 0.5, "is_recycle": false },
  { "source": "bassin_1", "target": "bassin_3", "fraction": 0.5, "is_recycle": false },
  { "source": "bassin_2", "target": "bassin_4", "fraction": 1.0, "is_recycle": false },
  { "source": "bassin_3", "target": "bassin_4", "fraction": 1.0, "is_recycle": false }
]
```

> Si aucune connexion n'est définie, le simulateur crée automatiquement une chaîne séquentielle dans l'ordre de déclaration des procédés.

---

## Sorties

Après chaque simulation, les résultats sont écrits dans `output/results/<nom_simulation>/` :

```
output/results/ma_simulation/
├── csv/
│   └── bassin_1_results.csv          # Série temporelle complète par nœud
├── metrics/
│   ├── bassin_1_performance.csv      # DCO, NH4, biomasse, énergie…
│   └── performance_metrics_*.json   # Statistiques agrégées (min/max/moy)
├── figures/
│   └── bassin_1_dashboard.html       # Dashboard Plotly interactif
├── performance_report.txt            # Rapport textuel lisible
├── ma_simulation_full.json           # Historique complet sérialisé
└── ma_simulation_summary.txt         # Résumé statistique
```

Les métriques calculées pour chaque nœud incluent notamment : DCO totale et soluble, taux d'épuration soluble, NH4, NO3, PO4, biomasse active, MLSS, SRT, SVI, HRT, consommation énergétique (kWh et kWh/m³).

Les logs sont disponibles dans `output/logs/simulation.log`.

---

## Tests

```bash
# Lancer tous les tests
pytest

# Avec rapport de couverture
pytest --cov

# Tests unitaires uniquement
pytest tests/unit/

# Tests d'intégration uniquement
pytest tests/integration/
```

---

## Limitations connues

### Phosphore
ASM1 et ASM3 ne modélisent pas le phosphore. La métrique `po4` dans les sorties sera toujours `0.0` avec ces modèles. Utiliser **ASM2d** pour un suivi du phosphore.

### SRT dans un réacteur seul (sans décanteur)
Dans un `ActivatedSludgeProcess` seul, le SRT effectif est égal au HRT — le paramètre `waste_ratio` retire une fraction du réacteur mais ne concentre pas les boues. Pour obtenir un SRT > HRT (nécessaire en pratique pour éviter le lessivage biologique), il faut coupler le bassin avec un `SecondarySettlerProcess` et une connexion de recyclage (`is_recycle: true`).

En conséquence, le SRT affiché dans les métriques (calculé comme `V / (waste_ratio × Q)`) est informatif mais ne reflète le SRT réel que dans une configuration avec décanteur + recyclage.

---

## Étendre le simulateur

### Ajouter un nouveau modèle

#### 1. Fichier de configuration JSON

Créer `core/model/config/<catégorie>/<nom_modele>.json` :

```json
{
  "id": "mon_modele",
  "type": "MonModele",
  "name": "Mon modèle",
  "description": "...",
  "category": "empirical",
  "components_count": 5,
  "processes_count": 3,
  "default_temperature": 20.0,
  "parameters": [
    { "id": "mu_max", "label": "Taux de croissance max.", "unit": "1/j", "default": 6.0 }
  ],
  "components": [
    { "id": "ss", "name": "Substrat soluble", "unit": "mg COD/L" }
  ],
  "metrics": {
    "cod": ["ss"],
    "nh4": "snh",
    "no3": null
  },
  "module": "models.empyrical.mon_modele.model",
  "class": "MonModele"
}
```

> Référence : `core/model/config/empirical/asm1.json`

#### 2. Enregistrement dans l'index

Ajouter dans `core/model/config/index.json` :

```json
{ "id": "mon_modele", "path": "empirical/mon_modele.json" }
```

#### 3. Implémentation Python

Dans `models/empyrical/mon_modele/model.py`, hériter de la classe de base adaptée :

| Type de modèle | Classe de base | Méthodes obligatoires |
|----------------|----------------|-----------------------|
| Biologique (EDO) | `ReactionModel` | `process_rates`, `stoichiometric_matrix`, `concentrations_to_dict`, `dict_to_concentrations` |
| Transport / sédimentation | `TransportModel` | `compute_fluxes`, `compute_settling_velocity`, `derivatives` |
| Machine Learning | `MLModel` | `fit`, `predict_step`, `initialize_state`, `save`, `load` |

#### 4. Fractionnement (si nécessaire)

Si le modèle utilise des composants internes différents des paramètres mesurés standards, créer `models/empyrical/mon_modele/fraction.py` avec une méthode de classe `fractionate(cod, tss, tkn, nh4, ...)`.

Puis déclarer l'association dans `core/registries/fractionation/config/model_strategies.json` :

```json
{
  "MonModele": "ASM1FractionationStrategy"
}
```

Si le modèle nécessite une stratégie de fractionnement sur-mesure, créer un fichier dans `core/registries/fractionation/strategies/` en héritant de `FractionationStrategy`, l'exporter depuis `strategies/__init__.py`, et ajouter son constructeur dans `_STRATEGY_CONSTRUCTORS` de `registry.py`.

---

### Ajouter un nouveau procédé

#### 1. Fichier de configuration JSON

Créer `core/process/config/processes/<nom_procede>.json` :

```json
{
  "id": "mon_procede",
  "type": "MonProcede",
  "name": "Mon procédé",
  "description": "...",
  "category": "biological",
  "model": "",
  "has_model_choice": false,
  "required_params": [
    { "name": "volume", "label": "Volume", "unit": "m³", "default": 1000.0, "min": 1.0, "max": 100000.0 }
  ],
  "optional_params": [],
  "module": "processes.mon_procede.mon_procede_process",
  "class": "MonProcedeProcess"
}
```

> Référence : `core/process/config/processes/activated_sludge.json`

#### 2. Enregistrement dans l'index

Ajouter dans `core/process/config/index.json` :

```json
{ "id": "mon_procede", "path": "processes/mon_procede.json" }
```

#### 3. Implémentation Python

Dans `processes/mon_procede/mon_procede_process.py`, hériter de `ProcessNode` et implémenter les méthodes abstraites :

| Méthode | Rôle |
|---------|------|
| `initialize()` | Initialiser l'état interne |
| `process(inputs, dt)` | Calculer les sorties pour un pas de temps |
| `update_state(outputs)` | Mettre à jour l'état après chaque pas |
| `get_required_inputs()` | Déclarer les clés d'entrée attendues |

> Référence : `processes/sludge_process/unified_activated_sludge_process.py`

---

### Points de vigilance

- Le champ `type` dans le JSON doit correspondre **exactement** au nom de la classe Python.
- Le champ `module` doit être un chemin Python valide (ex. `models.empyrical.asm1.model`).
- La section `metrics` du JSON fait le lien entre métriques standard (`cod`, `nh4`…) et composants internes — une erreur ici produit des valeurs nulles sans message d'erreur explicite.
- `ModelRegistry`, `ProcessRegistry`, `MetricsRegistry`, `FractionationRegistry` et `ExportRegistry` sont des **singletons** chargés au démarrage. Toute modification des fichiers JSON pendant l'exécution nécessite un redémarrage.

---

### Vérification après ajout

```bash
# 1. Vérifier que le modèle/procédé apparaît dans le mode interactif
python main.py -i

# 2. Lancer une simulation minimale
python main.py config/ma_config_test.json --no-plots

# 3. Contrôler les sorties
# → output/results/ : valeurs non nulles, plages réalistes

# 4. En cas d'erreur, activer le mode debug
python main.py config/ma_config_test.json --log-level DEBUG
# → output/logs/simulation.log
```
