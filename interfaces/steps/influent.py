from typing import Dict
from utils.decorators import step
from utils.input_helpers import ask_number

@step("ETAPE 3/8 : Caractéristique de l'influent")
def configure_influent(config: Dict) -> None:
    """Configure les caractéristiques de l'influent"""

    # Débit
    flowrate = ask_number(
        "\nDébit d'entrée (m^3/h)",
        default=1000.0,
        min_val=1.0
    )

    # Température
    temperature = ask_number(
        "Température (°C)",
        default=20.0,
        min_val=5.0,
        max_val=35.0
    )

    # Paramètres de pollution
    print("\nParamètres de pollution :")
    cod = ask_number("\tDCO totale (mg/L)", default=500.0, min_val=0)
    ss = ask_number("\tMES (mg/L)", default=250.0, min_val=0)
    tkn = ask_number("\tTKN - Azote Kjeldahl (mg/L)", default=40.0, min_val=0)
    nh4 = ask_number("\tNH4 - Ammonium (mg/L)", default=28.0, min_val=0)
    no3 = ask_number("\tNO3 - Nitrates (mg/L)", default=0.5, min_val=0)
    po4 = ask_number("\tPO4 - Phosphates (mg/L)", default=8.0, min_val=0)
    alkalinity = ask_number("\tAlcalinité (mmol/L)", default=6.0, min_val=0)

    config.update({
        'influent': {
            'flowrate': flowrate,
            'temperature': temperature,
            'model_type': 'ASM1', # Pour l'instant fixé à ASM1
            'auto_fractionate': True,
            'composition': {
                'cod': cod,
                'ss': ss,
                'tkn': tkn,
                'nh4': nh4,
                'no3': no3,
                'po4': po4,
                'alkalinity': alkalinity
            }
        }
    })

    print(f"\nInfluent configuré : Q = {flowrate} m^3/h, DCO = {cod} mg/L")