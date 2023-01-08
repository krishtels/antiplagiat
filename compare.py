import argparse
import ast


def levenstein(str_1, str_2):
    n, m = len(str_1), len(str_2)
    if n > m:
        str_1, str_2 = str_2, str_1
        n, m = m, n

    current_row = range(n + 1)
    for i in range(1, m + 1):
        previous_row, current_row = current_row, [i] + [0] * n
        for j in range(1, n + 1):
            add, delete, change = previous_row[j] + 1, current_row[j - 1] + 1, previous_row[j - 1]
            if str_1[j - 1] != str_2[i - 1]:
                change += 1
            current_row[j] = min(add, delete, change)

    return current_row[n]


class TemplateCodeTransformer(ast.NodeTransformer):
    @staticmethod
    def del_annotation(node):
        node.returns = None
        if node.args.args:
            for arg in node.args.args:
                arg.annotation = None
        return node

    @staticmethod
    def del_comments(node):
        new_body = []
        for body_el in node.body:
            if (hasattr(body_el, 'value')) and isinstance(body_el.value, ast.Str):
                continue
            new_body.append(body_el)
        node.body = new_body
        return node

    @staticmethod
    def check_internal_elem(node):
        for el in node.body:
            if isinstance(el, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                TemplateCodeTransformer().visit(el)
        return node

    def visit_FunctionDef(self, node):
        TemplateCodeTransformer.del_annotation(node)
        TemplateCodeTransformer.del_comments(node)
        TemplateCodeTransformer.check_internal_elem(node)
        return node

    def visit_AsyncFunctionDef(self, node):
        TemplateCodeTransformer.del_annotation(node)
        TemplateCodeTransformer.del_comments(node)
        TemplateCodeTransformer.check_internal_elem(node)
        return node

    def visit_ClassDef(self, node):
        TemplateCodeTransformer.del_comments(node)
        TemplateCodeTransformer.check_internal_elem(node)
        return node


class ChangeNames(ast.NodeTransformer):
    def visit_arg(self, node):
        return ast.arg(**{**node.__dict__, 'arg':node.arg[0].lower()})

    def visit_Name(self, node):
        return ast.arg(**{**node.__dict__, 'arg': node.id.lower()})


def code_change(file_name):
    with open(file_name, 'r') as file:
        parsed_source = ast.parse(file.read())
        transformed = TemplateCodeTransformer().visit(parsed_source)
        transformed = ChangeNames().visit(transformed)
        result_file = str(ast.unparse(transformed))
    return result_file


parser = argparse.ArgumentParser()
parser.add_argument('input', type=str)
parser.add_argument('output', type=str)
args = parser.parse_args()

if __name__ == '__main__':
    with open(args.input, 'r') as input_file:
        result_scores = []
        for line in input_file:
            first_path, second_path = line.split()
            first_file = code_change(first_path)
            second_file = code_change(second_path)
            result_scores.append(levenstein(first_file, second_file) * 2 / (len(first_file) + len(second_file)))

    with open(args.output, 'w') as output_file:
        for score in result_scores:
            output_file.write(str(score) + '\n')
