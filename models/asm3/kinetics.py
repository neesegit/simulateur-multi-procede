import numpy as np

def calculate_process_rate(c: np.ndarray, p: dict) -> np.ndarray:

    rho = np.zeros(12)

    # raccourcie
    so2 = max(c[0], 1e-6)
    si = max(c[1], 1e-6)
    ss = max(c[2], 1e-6)
    snh4 = max(c[3], 1e-6)
    sn2 = max(c[4], 1e-6)
    snox = max(c[5], 1e-6)
    salk = max(c[6], 1e-6)
    xi = max(c[7], 1e-6)
    xs = max(c[8], 1e-6)
    xh = max(c[9], 1e-6)
    xsto = max(c[10], 1e-6)
    xa = max(c[11], 1e-6)
    xss = max(c[12], 1e-6)

    k_h = p['k_h']
    k_x = p['k_x']
    k_sto_rate = p['k_sto_rate']
    eta_nox = p['eta_nox']
    k_o2 = p['k_o2']
    k_nox = p['k_nox']
    k_s = p['k_s']
    k_sto = p['k_sto']
    mu_h = p['mu_h']
    k_nh4 = p['k_nh4']
    k_alk = p['k_alk']
    b_h_o2 = p['b_h_o2']
    b_h_nox = p['b_h_nox']
    b_sto_o2 = p['b_sto_o2']
    b_sto_nox = p['b_sto_nox']
    mu_a = p['mu_a']
    k_a_nh4 = p['k_a_nh4']
    k_a_o2 = p['k_a_o2']
    k_a_alk = p['k_a_alk']
    b_a_o2 = p['b_a_o2']
    b_a_nox = p['b_a_nox']

    #1 Hydrolysis
    rho[0] = k_h*((xs/xh)/(k_x+(xs/xh)))*xh
    #2 Aerobic storage of Ss
    rho[1] = k_sto_rate*(so2/(k_o2+so2))*(ss/(k_s+ss))*xh
    #3 Anoxic storage of Ss
    rho[2] = k_sto_rate*eta_nox*(k_o2/(k_o2+so2))*(snox/(k_nox+snox))*(ss/(k_s+ss))*xh
    #4 Aerobic growth
    rho[3] = mu_h*(so2/(k_o2+so2))*(snh4/(k_nh4+snh4))*(salk/(k_alk+salk))*((xsto/xh)/(k_sto+(xsto/xh)))*xh
    #5 Anoxic growth (denitrification)
    rho[4] = mu_h*eta_nox*(k_o2/(k_o2+so2))*(snox/(k_nox+snox))*(snh4/(k_nh4+snh4))*(salk/(k_alk+salk))*((xsto/xh)/(k_sto+(xsto/xh)))*xh
    #6 Aerobic endogenous respiration
    rho[5] = b_h_o2*(so2/(k_o2+so2))*xh
    #7 Anoxic endogenous respiration
    rho[6] = b_h_nox*(k_o2/(k_o2+so2))*(snox/(k_nox+snox))*xh
    #8 Aerobic respiration of Xsto
    rho[7] = b_sto_o2*(so2/(k_o2+so2))*xsto
    #9 Anoxic respiration of Xsto
    rho[8] = b_sto_nox*(k_o2/(k_o2+so2))*(snox/(k_nox+snox))*xsto
    #10 Aerobic growth of Xa, nitrification
    rho[9] = mu_a*(so2/(k_a_o2+so2))*(snh4/(k_a_nh4+snh4))*(salk/(k_a_alk+salk))*xa
    #11 Aerobic endogenous respiration
    rho[10] = b_a_o2*(so2/(k_a_o2+so2))*xa
    #12 Anoxic endogenous respiration
    rho[11] = b_a_nox*(k_a_o2/(k_a_o2+so2))*(snox/(k_nox+snox))*xa

    return rho