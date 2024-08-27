import os


def get_directory_structure(path):
    def traverse(current_path, indent=''):
        result = []
        for item in sorted(os.listdir(current_path)):
            item_path = os.path.join(current_path, item)
            if os.path.isdir(item_path):
                result.append(f"{indent}{item}/")
                result.extend(traverse(item_path, indent + '  '))
            else:
                result.append(f"{indent}{item}")
        return result

    return '\n'.join(traverse(path))
