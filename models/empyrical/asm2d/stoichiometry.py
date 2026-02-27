import numpy as np

def build_stoichiometric_matrix(params: dict) -> np.ndarray:
    """
    Construit la matrice sotechimétrique complète 21x19
    
    Returns:
        Matrice numpy 21x19
    """
    S = np.zeros((21,19))

    # racourcie
    f_si = params['f_si']
    i_n_sf = params['i_n_sf']
    i_n_xs = params['i_n_xs']
    i_p_sf = params['i_p_sf']
    i_p_xs = params['i_p_xs']
    i_tss_xs = params['i_tss_xs']
    y_h = params['y_h']
    y_po4 = params['y_po4']
    f_xi = params['f_xi']
    y_pha = params['y_pha']
    i_p_bm = params['i_p_bm']
    y_a = params['y_a']
    i_n_bm = params['i_n_bm']
    i_n_xi = params['i_n_xi']
    i_p_xi = params['i_p_xi']

    i_alk_nh4 = 1/14
    i_alk_po4 = -1.5/31
    i_cod_n2 = -24/14
    i_cod_no3 = -64/14

    #1 Aerobic hydrolysis
    #2 Anoxic hydrolysis
    #3 Anaerobic hydrolysis
    for i in range(3):
        S[i,1] = 1-f_si
        S[i,3] = -(i_n_sf-i_n_xs)
        S[i,5] = -(i_p_sf-i_p_xs)
        S[i,6] = f_si
        S[i,7] = -(i_n_sf-i_n_xs)*i_alk_nh4 -(i_p_sf-i_p_xs)*i_alk_po4
        S[i,10] = -1
        S[i,16] = -i_tss_xs

    #4 Aerobic growth of XH on SF
    S[3,0] = 1-1/y_h
    S[3,1] = -1/y_h
    S[3,11] = 1

    #5 Aerobic growth of XH on SA
    S[4,0] = 1-1/y_h
    S[4,2] = -1/y_h
    S[4,11] = 1

    #6 Anoxic growth of XH on SF
    S[5,1] = -1/y_h
    S[5,4] = -((1-y_h)/(2.86*y_h))
    S[5,8] = (1/y_h)/(2.86*y_h)
    S[5,11] = 1

    #7 Anoxic growth of XH on SA
    S[6,2] = -1/y_h
    S[6,4] = -((1-y_h)/(2.86*y_h))
    S[6,8] = ((1-y_h)/(2.86*y_h))
    S[6,11] = 1

    #8 Fermentation
    S[7,1] = -1
    S[7,2] = 1

    #9 Lysis
    S[8,9] = f_xi
    S[8,10] = 1-f_xi
    S[8,11] = -1

    #10 Storage of XPHA
    S[9,2] = -1
    S[9,5] = y_po4
    S[9,13] = -y_po4
    S[9,14] = 1

    #11 Aerobic storage of XPP
    S[10,0] = -y_pha
    S[10,5] = -1
    S[10,13] = 1
    S[10,14] = -y_pha

    #12 Anoxic storage of XPP
    S[11,4] = y_pha/(-i_cod_n2+i_cod_no3)
    S[11,5] = -1
    S[11,8] = -(y_pha/(-i_cod_n2+i_cod_no3))
    S[11,13] = 1

    #13 Aerobic growth of XPAO
    S[12,0] = 1-1/y_h
    S[12,5] = -i_p_bm
    S[12,12] = 1
    S[12,14] = -1/y_h

    #14 Anoxic growth of XPAO
    S[13,4] = (1-y_h)/(y_h*(-i_cod_n2+i_cod_no3))
    S[13,5] = -i_p_bm
    S[13,8] = -((1-y_h)/(y_h*(-i_cod_n2+i_cod_no3)))
    S[13,12] = 1
    S[13,14] = -1/y_h

    #15 Lysis of XPAO
    S[14,5] = -(f_xi*i_p_xi+(1-f_xi)*i_p_xs-i_p_bm)
    S[14,9] = f_xi
    S[14,10] = 1-f_xi
    S[14,12] = -1

    #16 Lysis of XPP
    S[15,5] = 1
    S[15,13] = -1

    #17 Lysis of XPHA
    S[16,2] = 1
    S[16,14] = -1

    #18 Aerobic growth of XAUT
    S[17,0] = -(4.57-y_a)/y_a
    S[17,3] = -((1/y_a)+i_n_bm)
    S[17,4] = 1/y_a
    S[17,5] = -i_p_bm
    S[17,15] = 1

    #19 Lysis
    S[18,3] = -(f_xi*i_n_xi+(1-f_xi)*i_n_xs-i_n_bm)
    S[18,5] = -(f_xi*i_p_xi+(1-f_xi)*i_p_xs-i_p_bm)
    S[18,9] = f_xi
    S[18,10] = 1-f_xi
    S[18,15] = -1

    #20 Precipitation
    S[19,5] = -1
    S[19,7] = -i_alk_po4
    S[19,16] = 1.42
    S[19,17] = -3.45
    S[19,18] = 4.87

    #21 Redissolution
    S[20,5] = 1
    S[20,7] = i_alk_po4
    S[20,16] = -1.42
    S[20,17] = 3.45
    S[20,18] = -4.87

    return S
