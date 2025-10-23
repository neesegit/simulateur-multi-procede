"""
ASM1Process - Wrapper ProcessNode pour le modèle ASM1

Ce fichier fait le pont entre :
- L'orchestrator (qui gère le flux de simulation)
- Le modèle ASM1 (qui contient les équations)

Rôle :
- Reçoit les données via DataBus (FlowData)
- Les convertit en format numpy pour ASM1Model
- Appelle le modèle
- Reconvertit les résultats en FlowData
- Calcule des métriques (énergie, qualité eau)
"""
from typing import Dict, Any, List
import numpy as np
import logging

from core.process.process_node import ProcessNode
from models.asm1_model import ASM1Model

logger = logging.getLogger(__name__)

class ASM1Process(ProcessNode):
    """
    ProcessNode implémentant un bassin d'aération avec modèle ASM1
    """

    def __init__(self, node_id: str, name: str, config: Dict[str, Any]):
        """
        Initialise le processus ASM1

        Args:
            node_id (str): Identifiant unique
            name (str): Nom du procédé
            config (Dict[str, Any]): Configuration contenant :
                - volume : Volume du bassin (m^3)
                - depth : Profondeur (m)
                - dissolved_oxygen_setpoint : Consigne DO (mg/L)
                - parameters : Paramètres cinétiques ASM1 (optionnel)
        """
        super().__init__(node_id, name, config)

        # Paramètres physiques du bassin
        self.volume = config.get('volume', 5000.0) # m^3
        self.depth = config.get('depth', 4.0) # m
        self.do_setpoint = config.get('dissolved_oxygen_setpoint', 2.0) # mg/L

        # Ratio de recyclage
        self.recycle_ratio = config.get('recycle_ratio', 1.0) # Qr/Qin
        self.waste_ratio = config.get('waste_ratio', 0.01) # Qw/Qin

        # Crée l'instance du modèle ASM1
        asm1_params = config.get('parameters', None)
        self.model = ASM1Model(params=asm1_params)

        # Etat interne : concentrations actuelles (vecteur numpy 13)
        self.concentrations = np.zeros(13)

        self.logger.info(f"ASM1Process crée : V={self.volume} m^3, DO={self.do_setpoint} mg/L")

    def initialize(self) -> None:
        """
        Initialise l'état du bassin d'aération

        Explication :
        On part d'un état "stable" typique avec :
        - Biomasse présente (XBH, XBA)
        - Substrat faible (SS, XS)
        - Oxygène à la consigne
        """
        # Conditions initiales typiques (mg/L)
        initial_state = {
            'si': 30.0,                 # Substrat inerte soluble
            'ss': 5.0,                  # Substrat biodégradable (faible, déjà traité)
            'xi': 25.0,                 # Particulaire inerte
            'xs': 100.0,                # Substrat lentement biodégradable
            'xbh': 250.0,              # Biomasse hétérotrophe (concentration élevée)
            'xba': 150.0,               # Biomasse autotrophe
            'xp': 450.0,                # Produits inertes
            'so': self.do_setpoint,     # Oxygène à la consigne
            'sno': 5.0,                 # Nitrates
            'snh': 2.0,                 # Ammonium (faible, objectif de traitement)
            'snd': 1.0,                 # Azote organique soluble
            'xnd': 5.0,                 # Azote organique particulaire
            'salk': 7.0                 # Alcalinité
        }

        # Convertit en vecteur numpy
        self.concentrations = self.model.dict_to_concentrations(initial_state)

        # Stocke dans l'état ProcessNode
        self.state = self.model.concentrations_to_dict(self.concentrations)

        self.logger.info ("ASM1Process initialisé avec conditions par défaut")

    def get_required_inputs(self) -> List[str]:
        """
        Liste des entrées requises

        Returns:
            List[str]: Liste des clés nécessaires
        """
        return ['flow', 'flowrate', 'temperature']
    
    def process(self, inputs: Dict[str, Any], dt: float) -> Dict[str, Any]:
        """
        Traite l'influent pour un pas de temps donné
        Explication du traitement :

        1. On reçoit un influent (FlowData) avec Q_in et concentration C_in
        2. Le bassin a un volume V et des concentrations actuelles C
        3. On calcule le temps de séjour hydraulique : HRT = V / Q_in
        4. On applique le bilan de masse :
            dC/dt = (Q_in / V x C_in) - (Q_out / V x C) + réactions_biologiques
        5. Les réactions biologiques sont calculées par ASM1Model

        Args:
            inputs (Dict[str, Any]): Données d'entrée contenant FlowData
            dt (float): Pas de temps (heures)

        Returns:
            Dict[str, Any]: Données de sortie (concentrations traitées + métriques)
        """

        inputs = self.fractionate_input(inputs, target_model='ASM1')

        # Extrait les données d'entrée
        q_in = inputs['flowrate'] # m^3/h
        temp = inputs['temperature']
        components_in = inputs['components']

        # conertit les composants d'entrée en vecteur numpy
        c_in = self.model.dict_to_concentrations(components_in)

        # ============================================================
        # BILAN DE MASSE DANS LE RÉACTEUR
        # ============================================================
        # Le bassin est un réacteur parfaitement mélangé (CSTR)
        # 
        # Équation générale :
        # V × dC/dt = Q_in × C_in - Q_out × C + V × r(C)
        #
        # Où :
        # - V = volume du bassin (m³)
        # - Q_in = débit entrant (m³/h)
        # - Q_out = débit sortant = Q_in (hypothèse continuité)
        # - C_in = concentrations entrantes (mg/L)
        # - C = concentrations dans le bassin (mg/L)
        # - r(C) = vitesses de réaction biologiques (mg/L/j)
        #
        # En divisant par V :
        # dC/dt = (Q_in/V) × (C_in - C) + r(C)
        #         ↑                        ↑
        #    Transport hydraulique    Réactions bio
        # ============================================================

        # Temps de séjour hydraulique (heures -> jours pour ASM1)
        hrt_hours = self.volume / q_in # heures
        hrt_day = hrt_hours/ 24.0 # jours
        dt_days = dt / 24.0 # Convertit dt en jours

        # Taux de renouvellement (1/jours)
        dilution_rate = 1.0 / hrt_day if hrt_day > 0 else 0.0

        num_substeps = max(1,int(dt_days/0.01)) # sous-pas de 0.01 jours max
        dt_substep = dt_days / num_substeps

        c_current = self.concentrations.copy()

        for _ in range(num_substeps):
            # 1. Calcule les réactions biologiques
            reactions = self.model.compute_derivatives(c_current)

            # 2. Calcule le transport hydraulique
            transport = dilution_rate*(c_in - c_current)

            # 3. Combine transport + réaction
            dc_dt = transport + reactions

            # 4. Mise à jour Euler
            c_next = c_current + dc_dt*dt_substep

            # 5. Contraintes physiques
            c_next = np.maximum(c_next, 1e-10) # Pas de concentrations négatives

            # 6. Contrôle de l'oxygène dissous (aération)
            c_next[7] = self.do_setpoint # SO maintenu à la consigne

            c_current = c_next

        # Met à jour l'état interne
        self.concentrations = c_current

        # ============================================================
        # CALCUL DES MÉTRIQUES DE PERFORMANCE
        # ============================================================

        # Convertit en dictionnaire
        components_out = self.model.concentrations_to_dict(c_current)

        # calcule la DCO totale (somme des fractions organiques)
        cod_out = (components_out['si'] + components_out['ss'] + \
                   components_out['xi'] + components_out['xs'] + \
                   components_out['xbh'] + components_out['xba'] + \
                   components_out['xp'])
        
        # Calcule l'azote total
        tkn_out = (components_out['snh'] + components_out['snd'] + \
                   components_out['xnd'] + \
                   components_out['xbh'] * self.model.params['i_xb'] + \
                   components_out['xba'] * self.model.params['i_xb'])
        
        # Solides en suspension (fractions particulaires)
        ss_out = (components_out['xi'] + components_out['xs'] + \
                  components_out['xbh'] + components_out['xba'] + \
                  components_out['xp'])
        
        # DCO d'entrée (pour calcul de rendemant)
        cod_in = (c_in[0]+c_in[1]+c_in[2]+c_in[3]+c_in[4]+c_in[5]+c_in[6])

        # Taux d'abattement de la DCO
        cod_removal = ((cod_in - cod_out) / cod_in * 100) if cod_in > 0 else 0

        # Consommation d'oxygène (pour calcul énergie d'aération)
        # On estime à partir de la DCO éliminée
        oxygen_consumed = (cod_in - cod_out) * q_in * dt / 1000.0 # kg O2

        # Energie d'aération (approximation)
        # Règle empirique : 2 kWh par kg O2 transféré
        aeration_energy = oxygen_consumed * 2.0 # kWh

        # ============================================================
        # PRÉPARATION DES SORTIES
        # ============================================================

        outputs = {
            'flowrate': q_in,
            'temperature': temp,
            'model_type': 'ASM1',
            'components': components_out,

            # Paramètres globaux calculés
            'cod': cod_out,
            'ss': ss_out,
            'tkn': tkn_out,
            'bod': cod_out*0.6, # Approximation DBO = 60% DCO

            # Métriques de performance
            'cod_removal_rate': cod_removal,
            'hrt_hours': hrt_hours,
            'biomass_concentration': components_out['xbh'] + components_out['xba'],
            'mlss': ss_out, # Mixed Liquor Suspended Solids

            # Energie
            'oxygen_consumed_kg': oxygen_consumed,
            'aeration_energy_kwh': aeration_energy,
            'energy_per_m3': aeration_energy / (q_in * dt) if q_in > 0 else 0
        }

        # Stocke les métriques
        self.metrics = {
            'cod_removal': cod_removal,
            'hrt': hrt_hours,
            'mlss': ss_out,
            'energy_kwh': aeration_energy
        }

        return outputs
    
    def update_state(self, outputs: Dict[str, Any]) -> None:
        """
        Met à jour l'état interne après traitement

        Args:
            outputs (Dict[str, Any]): Sorties calculées par process()
        """
        # L'état a déjà été mis à jour dans process()
        # On stocke juste les composants pour traçabilité
        self.state = outputs['components'].copy()
        self.outputs = outputs
    
    def set_do_setpoint(self, setpoint: float) -> None:
        """
        Modifie la consigne d'oxygène dissous

        Utile pour le contrôle dynamique

        Args:
            setpoint (float): Nouvelle consigne DO (mg/L)
        """
        if setpoint < 0 or setpoint > 10:
            self.logger.warning(f"Consigne DO hors limites : {setpoint} mg/L")

        self.do_setpoint = setpoint
        self.logger.info(f"Consigne DO modifiée : {setpoint} mg/L")

    def get_biomass_concentration(self) -> float:
        """
        Retourne la concentration totale de biomasse active

        Returns:
            float: Concentration (mg COD/L)
        """
        return self.concentrations[4] + self.concentrations[5] # XBH + XBA
    
    def get_sludge_age(self) -> float:
        """
        Calcule l'âge des boues (SRT - Sludge Retention Time)

        Explication :
        SRT = (masse de boues dans le réacteur) / (masse de boues extraites par jour)

        Returns:
            float: Age des boues
        """
        biomass_mass = self.get_biomass_concentration() * self.volume # mg COD

        # Débit de purge
        q_in = self.inputs.get('flowrate', 1000.0) # m^3/h
        q_waste = q_in * self.waste_ratio * 24 # m^3/jour

        waste_mass = self.get_biomass_concentration() * q_waste # mg COD/jour

        srt = biomass_mass / waste_mass if waste_mass > 0 else float('inf')

        return srt
    
    def __repr__(self) -> str:
        return f"<ASM1Process(id={self.node_id}, V={self.volume}m^3, DO={self.do_setpoint}mg/L)"