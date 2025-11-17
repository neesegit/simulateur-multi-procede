import numpy as np

def build_stoichiometric_matrix(params: dict) -> np.ndarray:
    """
    Construit la matrice stoechiométrique complète 13x12

    Returns:
        np.ndarray: Matrice numpy 13x12
    """
    S = np.zeros((12,13))

    #raccourcie
    f_si = params['f_si']
    y_sto_o2 = params['y_sto_o2']
    y_sto_nox = params['y_sto_nox']
    y_h_o2 = params['y_h_o2']
    y_h_nox = params['y_h_nox']
    y_a = params['y_a']
    f_xi = params['f_xi']
    i_n_si = params['i_n_si']
    i_n_ss = params['i_n_ss']
    i_n_xi = params['i_n_xi']
    i_n_xs = params['i_n_xs']
    i_n_bm = params['i_n_bm']
    i_ss_xi = params['i_n_xi']
    i_ss_xs = params['i_ss_xs']
    i_ss_bm = params['i_ss_bm']

    # 1. Hydrolysis
    S[0,1] = f_si
    S[0,2] = 1-f_si
    S[0,3] = i_n_xs-f_si*i_n_si-(1-f_si)*i_n_ss
    S[0,6] = (i_n_xs-f_si*i_n_si-(1-f_si)*i_n_ss)/14
    S[0,8] = -1
    S[0,12] = -i_ss_xs

    # 2. Aerobic storage of Ss
    S[1,0] = -1+y_sto_o2
    S[1,2] = -1
    S[1,3] = i_n_ss
    S[1,6] = (i_n_ss)/14
    S[1,10] = y_sto_o2
    S[1,12] = 0.60*y_sto_o2

    # 3. Anoxic storage of Ss

    S[2,2] = -1
    S[2,3] = i_n_ss
    S[2,4] = -((y_sto_nox-1)/2.86)
    S[2,5] = (y_sto_nox-1)/2.86
    S[2,6] = (2.86*i_n_ss-y_sto_nox+1)/40.04
    S[2,10] = y_sto_nox
    S[2,12] = 0.60*y_sto_nox

    # 4. Aerobic growth of Xh
    S[3,0] = 1-(1/y_h_o2)
    S[3,3] = -i_n_bm
    S[3,6] = -(i_n_bm/14)
    S[3,9] = 1
    S[3,10] = -1/y_h_o2
    S[3,12] = i_ss_bm - 0.60/y_h_o2

    # 5. Anoxic growth (denitrific.)
    S[4,3] = -i_n_bm
    S[4,4] = (1-y_h_nox)/(2.86*y_h_nox)
    S[4,5] = -((1-y_h_nox)/(2.86*y_h_nox))
    S[4,6] = (1/14)*(-i_n_bm+(1-y_h_nox)/(2.86*y_h_nox))
    S[4,9] = 1
    S[4,10] = -1/y_h_nox
    S[4,12] = i_ss_bm - 0.60/y_h_nox

    # 6. Aerobic endog. respiration
    S[5,0] = f_xi - 1
    S[5,3] = i_n_bm-f_xi*i_n_xi
    S[5,6] = (i_n_bm-f_xi*i_n_xi)/14
    S[5,7] = f_xi
    S[5,9] = -1
    S[5,12] = f_xi*i_ss_xi-i_ss_bm

    # 7. Anoxic endog. respiration
    S[6,3] = i_n_bm-f_xi*i_n_xi
    S[6,4] = -((f_xi-1)/2.86)
    S[6,5] = (f_xi-1)/2.86
    S[6,6] = (i_n_bm-f_xi*i_n_xi -((f_xi-1)/2.86))/14
    S[6,7] = f_xi
    S[6,9] = -1
    S[6,12] = f_xi*i_ss_xi-i_ss_bm

    # 8. Aerobic respiration of Xsto
    S[7,0] = -1
    S[7,10] = -1
    S[7,12] = -1

    # 9. Anoxic respiration of Xsto
    S[8,4] = 1/2.86
    S[8,5] = -1/2.86
    S[8,6] = 1/40.04
    S[8,10] = -1
    S[8,12] = -1

    # 10. Aerobic growth of Xa
    S[9,0] = 1-4.87/y_a
    S[9,3] = -(1/y_a + i_n_bm)
    S[9,5] = 1/y_a
    S[9,6] = -1/(7*y_a) - i_n_bm/14
    S[9,11] = 1
    S[9,12] = 1

    # 11. Aerobic endog. respiration
    S[10,0] = f_xi-1
    S[10,3] = i_n_bm - f_xi*i_n_xi
    S[10,6] = (i_n_bm - f_xi*i_n_xi)/14
    S[10,7] = f_xi
    S[10,11] = -1
    S[10,12] = f_xi*i_ss_xi - i_ss_bm

    # 12 Anoxic endog. respiration
    S[11,3] = i_n_bm-f_xi*i_n_xi
    S[11,4] = -((f_xi-1)/2.86)
    S[11,5] = (f_xi-1)/2.86
    S[11,6] = (1/14)*(i_n_bm-f_xi*i_n_xi - (f_xi-1)/2.86)
    S[11,7] = f_xi
    S[11,11] = -1
    S[11,12] = f_xi*i_ss_xi-i_ss_bm

    return S