from scipy.sparse import coo_matrix


def matrix_to_coo(m):
    m_coo = coo_matrix(m)
    return [[[int(m_coo.row[i]), int(m_coo.col[i])], float(m_coo.data[i])] for i, _ in enumerate(m_coo.data)]
