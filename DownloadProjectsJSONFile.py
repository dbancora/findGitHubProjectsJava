import os
import json
import javalang
import git
import re
import shutil
import stat

def extract_test_methods(json_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for repo_info in data:
        repo_url = repo_info['url']
        repo_name = repo_info['name']
        local_path = clone_repo(repo_url, repo_name)
        if local_path:
            try:
                process_java_files(local_path, repo_name)
            except Exception as e:
                print(f"Errore durante l'elaborazione della repository {repo_name}: {e}")
            finally:
                cleanup_repo(local_path)  # Cleaning up the repository after processing

def clone_repo(repo_url, repo_name):
    local_path = f"./CloneRepo/{repo_name}"
    if not os.path.exists(local_path):
        os.makedirs(local_path)
    try:
        repo = git.Repo.clone_from(repo_url, local_path)
        print(f"Repository cloned to {local_path}")
        return local_path
    except git.exc.GitCommandError as e:
        print(f"Error cloning repository: {e}")
        return None

def process_java_files(repo_path, repo_name):
    results = []
    for root, dirs, files in os.walk(repo_path):
        for file_name in files:
            if file_name.endswith('.java'):
                file_path = os.path.join(root, file_name)
                test_methods = extract_methods_from_file(file_path, repo_path)
                if test_methods:
                    results.extend(test_methods)

    if results:
        results_with_focal = [result for result in results if result['method_focal']['focal_method_text']]
        if results_with_focal:
            save_results(results_with_focal, repo_name)
        else:
            print(f"No relevant test methods with a focal method found in {repo_name}.")
    else:
        print(f"No relevant test methods found in {repo_name}.")

def save_results(results, repo_name):
    output_dir = './Results'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    sanitized_repo_name = re.sub(r'[^a-zA-Z0-9_-]', '_', repo_name)
    output_file = os.path.join(output_dir, f'results_{sanitized_repo_name}.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    print(f"Test methods found with focal methods are saved in '{output_file}'.")

def change_permissions_and_remove(path):
    for root, dirs, files in os.walk(path):
        for dir in dirs:
            os.chmod(os.path.join(root, dir), stat.S_IRWXU)
        for file in files:
            os.chmod(os.path.join(root, file), stat.S_IRWXU)
    shutil.rmtree(path)

def cleanup_repo(repo_path):
    try:
        change_permissions_and_remove(repo_path)
        print(f"Rimossa la repository clonata in {repo_path}")


        parent_path = os.path.dirname(repo_path)
        if os.path.exists(parent_path) and not os.listdir(parent_path):
            os.rmdir(parent_path)
            print(f"Rimossa anche la cartella principale {parent_path}")
    except Exception as e:
        print(f"Errore durante la rimozione della directory {repo_path}: {e}")

def extract_methods_from_file(file_path, repo_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()

        source_lines = source_code.splitlines()
        methods = []
        tree_root = javalang.parse.parse(source_code)

        for path, node in tree_root:
            if isinstance(node, javalang.tree.MethodDeclaration):
                if any(annotation.name == 'Test' for annotation in node.annotations):
                    method_start_line = node.position.line - 1
                    method_end_line = find_method_end(source_lines, method_start_line)
                    method_text = "\n".join(source_lines[method_start_line:method_end_line + 1])
                    method_text = clean_method_text(method_text)
                    method_text = remove_comments(method_text)

                    if count_asserts(method_text) == 1:
                        focal_method_name = extract_focal_method(method_text)
                        focal_method_text = find_method_in_code(repo_path, focal_method_name)

                        methods.append({
                            'method_name': node.name,
                            'method_text': method_text,
                            'method_focal': {
                                'focal_method_name': focal_method_name,
                                'focal_method_text': focal_method_text
                            }
                        })

        return methods

    except javalang.parser.JavaSyntaxError as e:
        print(f"Error parsing {file_path}: {e}")
        raise e

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        raise e

def extract_focal_method(method_text):
    try:
        match = re.search(r'assertEquals\s*\((.*?)\)', method_text, re.DOTALL)
        if match:
            args_inside_assert = match.group(1).strip()

            focal_method_match = re.search(r'\.\s*(\w+)\s*\(', args_inside_assert)
            if focal_method_match:
                focal_method_name = focal_method_match.group(1)
                return focal_method_name

        return None

    except Exception as e:
        print(f"Error extracting focal method: {e}")
        return None

def find_method_in_code(repo_path, method_name):
    if method_name is None:
        return []

    results = []
    parsed_files = set()

    for root, dirs, files in os.walk(repo_path):
        for file_name in files:
            if file_name.endswith('.java'):
                file_path = os.path.join(root, file_name)

                if file_path in parsed_files:
                    continue

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        source_code = f.read()

                    tree = javalang.parse.parse(source_code)
                    for path, node in tree:
                        if isinstance(node, javalang.tree.MethodDeclaration) and node.name == method_name:

                            modifiers = [modifier for modifier in node.modifiers]
                            if any(modifier in ['public', 'private', 'protected'] for modifier in modifiers):
                                method_start_line = node.position.line - 1
                                method_end_line = find_method_end(source_code.splitlines(), method_start_line)
                                method_lines = source_code.splitlines()[method_start_line:method_end_line + 1]
                                method_text = "\n".join(method_lines)
                                results.append(clean_method_text(method_text))

                except javalang.parser.JavaSyntaxError as e:
                    print(f"Error parsing {file_path}: {e}")
                    parsed_files.add(file_path)
                    raise e

                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
                    parsed_files.add(file_path)
                    raise e

    if not results:
        print(f"Method {method_name} not found in {repo_path}")
        return []

    return results

def find_method_end(source_lines, start_line):
    open_braces = 0
    for i in range(start_line, len(source_lines)):
        line = source_lines[i]
        open_braces += line.count('{')
        open_braces -= line.count('}')
        if open_braces == 0:
            return i
    return len(source_lines) - 1

def clean_method_text(method_text):
    lines = method_text.split('\n')
    cleaned_lines = [line.strip() for line in lines if line.strip()]
    cleaned_text = " ".join(cleaned_lines)
    return cleaned_text

def remove_comments(method_text):

    method_text = re.sub(r'//.*', '', method_text)

    method_text = re.sub(r'/\*[\s\S]*?\*/', '', method_text)
    return method_text

def count_asserts(method_text):
    return len(re.findall(r'\bassert\w*\(', method_text))

if __name__ == '__main__':
    repo_name = '2020_04'
    extract_test_methods(f'github_repositories_{repo_name}.json')
