import numpy as np

def calculate_process_rates(c: np.ndarray, p: dict) -> np.ndarray:

    rho = np.zeros(21)

    so2 = max(c[0], 1e-10)
    sf = max(c[1], 1e-10)
    sa = max(c[2], 1e-10)
    snh4 = max(c[3], 1e-10)
    sno3 = max(c[4], 1e-10)
    spo4 = max(c[5], 1e-10)
    si = c[6]
    salk = max(c[7], 1e-10)
    sn2 = c[8]
    xi = c[9]
    xs = max(c[10], 1e-10)
    xh = max(c[11], 1e-10)
    xpao = max(c[12], 1e-10)
    xpp = max(c[13], 1e-10)
    xpha = max(c[14], 1e-10)
    xaut = max(c[15], 1e-10)
    xtss = c[16]
    xmeoh = max(c[17], 1e-10)
    xmep = c[18]

    k_o2 = p['k_o2']
    k_no3 = p['k_no3']
    k_a = p['k_a']
    k_nh4 = p['k_nh4']
    k_p = p['k_p']
    k_ps = p['k_ps']
    k_alk = p['k_alk']

    k_h = p['k_h']
    eta_no3 = p['eta_no3']
    eta_fe = p['eta_fe']
    k_x = p['k_x']

    mu_h = p['mu_h']
    q_fe = p['q_fe']
    eta_no3_h = p['eta_no3_h']
    b_h = p['b_h']
    k_f = p['k_f']
    k_fe = p['k_fe']

    q_pha = p['q_pha']
    q_pp = p['q_pp']
    mu_pao = p['mu_pao']
    eta_no3_pao = p['eta_no3_pao']
    b_pao = p['b_pao']
    b_pp = p['b_pp']
    b_pha = p['b_pha']
    k_pp = p['k_pp']
    k_max = p['k_max']
    k_ipp = p['k_ipp']
    k_pha = p['k_pha']

    mu_aut = p['mu_aut']
    b_aut = p['b_aut']
    k_o2_aut = p['k_o2_aut']
    k_alk_aut = p['k_alk_aut']

    k_pre = p['k_pre']
    k_red = p['k_red']

    #1 Aerobic hydrolysis
    rho[0] = k_h*(so2/(k_o2+so2))*((xs/xh)/(k_x+xs/xh))*xh
    #2 Anoxic hydrolysis
    rho[1] = k_h*eta_no3*(k_o2/(k_o2+so2))*(sno3/(k_no3+sno3))*((xs/xh)/(k_x+xs/xh))*xh
    #3 Anaerobic hydrolysis
    rho[2] = k_h*eta_fe*(k_o2/(k_o2+so2))*(k_no3/(k_no3+sno3))*((xs/xh)/(k_x+xs/xh))*xh
    #4 Aerobic growth of XH on SF
    rho[3] = mu_h*(so2/(k_o2+so2))*(sf/(k_f+sf))*(sf/(sf+sa))*(snh4/(k_nh4+snh4))*(spo4/(k_p+spo4))*(salk/(k_alk+salk))*xh
    #5 Aerobic growth of XH on SA
    rho[4] = mu_h*(so2/(k_o2+so2))*(sa/(k_a+sa))*(sa/(sf+sa))*(snh4/(k_nh4+snh4))*(spo4/(k_p+spo4))*(salk/(k_alk+salk))*xh
    #6 Anoxic growth of XH on SF
    rho[5] = mu_h*eta_no3_h*(k_o2/(k_o2+so2))*(k_no3/(k_no3+sno3))*(sf/(k_f+sf))*(sf/(sf+sa))*(snh4/(k_nh4+snh4))*(spo4/(k_p+spo4))*(salk/(k_alk+salk))*xh
    #7 Anoxic growth of XH on SA
    rho[6] = mu_h*eta_no3_h*(k_o2/(k_o2+so2))*(k_no3/(k_no3+sno3))*(sa/(k_a+sa))*(sa/(sf+sa))*(snh4/(k_nh4+snh4))*(spo4/(k_p+spo4))*(salk/(k_alk+salk))*xh
    #8 Fermentation
    rho[7] = q_fe*(k_o2/(k_o2+so2))*(k_no3/(k_no3+sno3))*(sf/(k_f+sf))*(salk/(k_alk+salk))*xh
    #9 Lysis
    rho[8] = b_h*xh
    #10 Storage of XPHA
    rho[9] = q_pha*(sa/(k_a+sa))*(salk/(k_alk+salk))*((xpp/xpao)/(k_pp+xpp/xpao))*xpao
    #11 Aerobic storage of XPP
    rho[10] = q_pp*(so2/(k_o2+so2))*(spo4/(k_ps+spo4))*(salk/(k_alk+salk))*((xpha/xpao)/(k_pha+xpha/xpao))*((k_max-xpp/xpao)/(k_pp+k_max-xpp/xpao))*xpao
    #12 Anoxic storage of XPP
    rho[11] = rho[10]*eta_no3_pao*(k_o2/(k_o2+so2))*(sno3/(k_no3+sno3))
    #13 Aerobic growth of XPAO
    rho[12] = mu_pao*(so2/(k_o2+so2))*(snh4/(k_nh4+snh4))*(spo4/(k_p+spo4))*(salk/(k_alk+salk))*((xpha/xpao)/(k_pha+xpha/xpao))*xpao
    #14 Anoxic growth of XPAO
    rho[13] = rho[12]*eta_no3*(k_o2/(k_o2+so2))*(sno3/(k_no3+sno3))
    #15 Lysis of XPAO
    rho[14] = b_pao*xpao*(salk/(k_alk+salk))
    #16 Lysis of XPP
    rho[15] = b_pp*xpp*(salk/(k_alk+salk))
    #17 Lysis of XPHA
    rho[16] = b_pha*xpha*(salk/(k_alk+salk))
    #18 Aerobic growth of XAUT
    rho[17] = mu_aut*(so2/(k_o2_aut+so2))*(snh4/(k_nh4+snh4))*(spo4/(k_p+spo4))*(salk/(k_alk_aut*salk))*xaut
    #19 Lysis
    rho[18] = b_aut*xaut
    #20 Precipitation
    rho[19] = k_pre*spo4*xmeoh
    #21 Redissolution
    rho[20] = k_red*xmep*(salk/(k_alk_aut+salk))

    return rho