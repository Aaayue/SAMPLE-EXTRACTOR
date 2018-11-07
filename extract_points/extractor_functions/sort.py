import numpy


def sorting(ppx, ppy, rre, block):
    """
    function to sort x, y coordinate into blocks
    the blocks is defined in data file, e,g, 640x640, 256 x256
    # TODO better ways of doing this?
    """
    py_block = (ppy / block + 1).astype(int)
    px_block = (ppx / block + 1).astype(int)

    sort_index = py_block.argsort()
    py_block = py_block[sort_index]
    px_block = px_block[sort_index]
    ppx = ppx[sort_index]
    ppy = ppy[sort_index]
    rre = rre[sort_index]

    temp = numpy.empty(0)
    temp0 = numpy.empty(0)
    temp1 = numpy.empty(0)
    temp2 = numpy.empty(0)

    last_element = None
    ppx_return = numpy.empty(0)
    ppy_return = numpy.empty(0)
    rre_return = numpy.empty(0)

    for i, val in enumerate(py_block):
        if val != last_element and last_element is not None:
            index = temp.argsort()
            ppx_return = numpy.append(ppx_return, temp0[index])
            ppy_return = numpy.append(ppy_return, temp1[index])
            rre_return = numpy.append(rre_return, temp2[index])

            temp = numpy.empty(0)
            temp0 = numpy.empty(0)
            temp1 = numpy.empty(0)
            temp2 = numpy.empty(0)

            temp = numpy.append(temp, px_block[i])
            temp0 = numpy.append(temp0, ppx[i])
            temp1 = numpy.append(temp1, ppy[i])
            temp2 = numpy.append(temp2, rre[i])

            last_element = val
        else:
            temp = numpy.append(temp, px_block[i])
            temp0 = numpy.append(temp0, ppx[i])
            temp1 = numpy.append(temp1, ppy[i])
            temp2 = numpy.append(temp2, rre[i])
            last_element = val

        if i == py_block.shape[0] - 1:  # deal with the last element
            index = temp.argsort()
            ppx_return = numpy.append(ppx_return, temp0[index])
            ppy_return = numpy.append(ppy_return, temp1[index])
            rre_return = numpy.append(rre_return, temp2[index])
    return ppx_return, ppy_return, rre_return


ppx = numpy.array([2, 3, 41, 2, 2, 5, 3, 6, 6, 19, 32, 11, 23, 45, 2])
ppy = numpy.array([9, 11, 23, 1, 19, 24, 3, 99, 89, 10, 21, 9, 21, 90, 99])
rre = numpy.array(
    ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O"]
)
block = 5

x, y, z = sorting(ppx, ppy, rre, block)
print(ppx)
print(ppy)
print(rre)
print(x)
print(y)
print(z)
