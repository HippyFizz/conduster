from graphene.types.scalars import Scalar


class JSONDict(Scalar):
    '''JSON Dict'''

    @staticmethod
    def serialize(dt):
        return dt

    @staticmethod
    def parse_literal(node):
        return node.value

    @staticmethod
    def parse_value(value):
        return value
