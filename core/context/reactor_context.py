from dataclasses import dataclass

@dataclass(frozen=True)
class ReactorContext:
    """
    Contexte opératoire pour un réacteur CSTR

    Attributs:
        Q_in: Débit d'entrée (m^3/h)
        Volume: Volume du réacteur (m^3)
        temperature : Température (°C)
        DO_setpoint: Consigne d'oxygène dissous (mg/L), optionnel
    """
    Q_in: float
    volume: float
    temperature: float = 20.0
    DO_setpoint: float = 2.0

    def dilution_rate(self) -> float:
        """Calcule le taux de dilution (1/j)"""
        hrt_hours = self.volume / self.Q_in if self.Q_in > 0 else 0
        return (1.0 / (hrt_hours / 24.0)) if hrt_hours > 0 else 0
    
    def to_dict(self) -> dict:
        """Convertit le contexte en dictionnaire"""
        return {
            'Q_in': self.Q_in,
            'volume': self.volume,
            'temperature': self.temperature,
            'DO_setpoint': self.DO_setpoint,
            'dilution_rate': self.dilution_rate()
        }