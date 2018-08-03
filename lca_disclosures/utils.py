import numpy as np
from scipy.sparse import coo_matrix

def matrix_to_coo(m):
    m_coo = coo_matrix(m)
    return [[[int(m_coo.row[i]), int(m_coo.col[i])], float(m_coo.data[i])] for i, _ in enumerate(m_coo.data)]

def reconstruct_matrix(matrix_dict, normalise=False, clear_diagonal=False):
    m = np.zeros(matrix_dict['shape'])
    for (r, c), v in matrix_dict['data']:
        m[r, c] = v
    
    if normalise and sum(m.diagonal()) != 0:
        m = -m/m.diagonal()
        
        if clear_diagonal:
            m = m + np.eye(matrix_dict['shape'][0])
        
    return m
