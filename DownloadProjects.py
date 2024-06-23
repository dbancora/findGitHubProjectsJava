import os
import json
import javalang
from javalang import tree
import git
import re

def extract_test_methods(repo_name, json_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for repo_info in data:
        repo_url = repo_info['url']
        repo_name = repo_info['name']
        local_path = clone_repo(repo_url, repo_name)
        if local_path:
            process_java_files(local_path, repo_name)

def clone_repo(repo_url, repo_name):
    local_path = f"./CloneRepo/{repo_name}"  # Cartella locale dove verrà clonato il repository

    # Assicura che la directory esista
    if not os.path.exists(local_path):
        os.makedirs(local_path)

    try:
        repo = git.Repo.clone_from(repo_url, local_path)
        print(f"Repository cloned to {local_path}")
        return local_path
    except git.exc.GitCommandError as e:
        print(f"Error cloning repository: {e}")
        return None

def extract_methods_from_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()

        source_lines = source_code.splitlines()
        methods = []
        tree_root = javalang.parse.parse(source_code)

        for path, node in tree_root:
            if isinstance(node, javalang.tree.MethodDeclaration):
                # Verifica se il metodo ha l'annotazione @Test
                if any(annotation.name == 'Test' for annotation in node.annotations):
                    # Trova la riga di inizio del metodo
                    method_start_line = node.position.line - 1  # Converti da 1-based a 0-based
                    # Trova la riga di fine del metodo
                    method_end_line = find_method_end(source_lines, method_start_line)

                    # Estrae il metodo completo (header e corpo)
                    method_text = "\n".join(source_lines[method_start_line:method_end_line + 1])
                    method_text = clean_method_text(method_text)
                    method_text = remove_comments(method_text)
                    methods.append({
                        'method_name': node.name,
                        'method_text': method_text
                    })

        return methods

    except javalang.parser.JavaSyntaxError as e:
        print(f"Error parsing {file_path}: {e}")
        return []

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return []

def find_method_end(source_lines, start_line):
    open_braces = 0
    for i in range(start_line, len(source_lines)):
        line = source_lines[i]
        open_braces += line.count('{')
        open_braces -= line.count('}')
        if open_braces == 0:
            return i
    return len(source_lines) - 1  # Fallback nel caso non trovi la fine del metodo

def clean_method_text(method_text):
    lines = method_text.split('\n')
    cleaned_lines = [line.strip() for line in lines if line.strip()]
    cleaned_text = " ".join(cleaned_lines)
    return cleaned_text

def remove_comments(method_text):
    # Usa una regex per rimuovere i commenti che iniziano con //
    return re.sub(r'//.*', '', method_text)

def process_java_files(repo_path, repo_name):
    results = []
    for root, dirs, files in os.walk(repo_path):
        for file_name in files:
            if file_name.endswith('.java'):
                file_path = os.path.join(root, file_name)
                test_methods = extract_methods_from_file(file_path)
                if test_methods:
                    for method in test_methods:
                        results.append({
                            'repository': repo_name,
                            'file': file_path,
                            'method': method
                        })

    # Creazione del percorso del file JSON
    output_dir = './Results'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Creazione del nome del file JSON basato sul nome della repository
    sanitized_repo_name = re.sub(r'[^a-zA-Z0-9_-]', '_', repo_name)  # Sostituisce caratteri non validi
    output_file = os.path.join(output_dir, f'results_{sanitized_repo_name}.json')

    # Salvataggio dei risultati su file JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

    # Post-processamento per rimuovere i caratteri di escape dalle virgolette
    with open(output_file, 'r', encoding='utf-8') as f:
        file_contents = f.read()

    file_contents = file_contents.replace('\\"', '"')

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(file_contents)

    print(f"I metodi @Test trovati sono stati salvati in '{output_file}'.")

def process_repository(repo_name):
    json_file = f'github_repositories_{repo_name}.json'
    extract_test_methods(repo_name, json_file)

if __name__ == '__main__':
    repo_name = 'test'  # Cambia con il nome del file JSON da elaborare
    process_repository(repo_name)
