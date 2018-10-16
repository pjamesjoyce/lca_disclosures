from scipy.sparse import coo_matrix
from pandas import DataFrame


def matrix_to_data(m):
    """
    Convert a recognizable numpy matrix (valid input to coo_matrix) to the nested-list format specified in the
    disclosure data spec: [[[row, col], val], [[row, col], val], ...]
    :param m:
    :return:
    """
    m_coo = coo_matrix(m)
    return [[[int(m_coo.row[i]), int(m_coo.col[i])], float(d)] for i, d in enumerate(m_coo.data)]


def data_to_rcv(matrix):
    """
    convert a data spec matrix into lists of rows, columns, and values
    :param matrix:
    :return:
    """
    r = [x[0][0] for x in matrix['data']]
    c = [x[0][1] for x in matrix['data']]
    v = [x[1] for x in matrix['data']]
    return r, c, v


def data_to_coo(matrix):
    """
    convert a data spec matrix into a sparse COO matrix
    :param matrix:
    :return:
    """
    r, c, v = data_to_rcv(matrix)
    return coo_matrix((v, (r, c)), shape=matrix['shape'])


def matrix_to_excel(writer, sheetname, matrix, index=None, **kwargs):
    df = DataFrame(matrix, index=index, **kwargs)
    df[df == 0] = None
    df.to_excel(writer, sheet_name=sheetname)
