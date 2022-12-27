from fields.field import FQ


def dot(vector_a, vector_b):
    result = FQ(0)

    for x, y in zip(vector_a, vector_b):
        result += x * y

    return result
