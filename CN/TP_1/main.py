import random
import math

class Node:
    def __init__(self, data):
        self.left = None
        self.right = None
        self.data = data
        self.func_set = ['+', '-', '*', '/']
        self.term_set = ['x1_1', 'x1_2', 'x2_1', 'x2_2']

    def generate_expr(self, depth, method):
        if depth == 0 or (method == "grow" and random.random() < float(len(self.term_set))/(len(self.term_set) + len(self.func_set))):
            self.data = self.choose_random_element(self.term_set)
        else:
            self.data = self.choose_random_element(self.func_set)

            self.left = Node('')
            self.left.generate_expr(depth - 1, method)

            self.right = Node('')
            self.right.generate_expr(depth - 1, method)

    def choose_random_element(self, chosen_set):
        index = math.floor(random.random() * len(chosen_set))
        return chosen_set[index]

    def PrintTree(self):
        if self.left:
            self.left.PrintTree()
        print( self.data),
        if self.right:
            self.right.PrintTree()

    def unroll_expression(self, expr_list):
        expr_list.append(self.data)
        if self.left is not None:
            expr_list = self.left.unroll_expression(expr_list)
        if self.right is not None:
            expr_list = self.right.unroll_expression(expr_list)
        return expr_list

    def eval(self, params1, params2, expr_list):
        reverse_expr = expr_list[::-1]
        new_expr = []
        for elem in reverse_expr:
            if elem not in self.func_set:
                value = self.map_value_to_param(elem, params1, params2)
                new_expr.append(value)
            else:
                value1 = new_expr.pop()

                value2 = new_expr.pop()
                
                if elem == '+':
                    new_expr.append(value1 + value2)
                elif elem == '-':
                    new_expr.append(value1 - value2)
                elif elem == '*':
                    new_expr.append(value1 * value2)
                else:
                    if value2 == 0:
                        new_expr.append(1)
                    else:
                        new_expr.append(float(value1) / value2)
        return new_expr[0]

    def map_value_to_param(self, value, params1, params2):
        if value[:2] == 'x1':
            return params1[int(value.split('_')[1]) - 1]
        else:
            return params2[int(value.split('_')[1]) - 1]


if __name__ == "__main__" :
    root = Node('')
    root2 = Node('')

    root.generate_expr(2, 'grow')
    root2.generate_expr(2, 'full')

    print("Tree 1:\n")
    root.PrintTree()
    print("\n\nTree 2:\n")
    root2.PrintTree()

    expr = root.unroll_expression([])
    expr2 = root2.unroll_expression([])

    print(expr)
    print(expr2)

    print(root.eval([1, 2], [3, 4], expr))
    print(root.eval([3, 1], [2, 4], expr))

    print(root.eval([1, 2], [3, 4], expr2))
    print(root.eval([3, 1], [2, 4], expr2))
    