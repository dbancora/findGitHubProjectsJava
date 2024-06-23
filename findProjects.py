import requests
import base64
import time
import json


def search_github_repositories(query, start_page=1):
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'Authorization': 'Bearer IL TUO TOKEN '  # Sostituisci con il tuo token di accesso GitHub
    }

    params = {
        'q': query,
        'per_page': 100,
        'page': start_page
    }

    repositories = []
    current_page = start_page

    while True:
        url = 'https://api.github.com/search/repositories'
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            response_data = response.json()
            items = response_data['items']
            repositories.extend(items)

            if len(items) < 100:
                break

            current_page += 1
            params['page'] = current_page
            time.sleep(6)  # Attendi 2 secondi tra una richiesta e l'altra
        else:
            print(f"Errore nella richiesta: {response.status_code}, {response.text}")
            break

    return repositories


def check_pom_for_junit(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/pom.xml"
    print(f"{url}")
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'Authorization': 'Bearer IL TUO TOKEN'  # Sostituisci con il tuo token di accesso GitHub
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        content_data = response.json()
        content = base64.b64decode(content_data['content']).decode('utf-8')

        # Verifica se JUnit è una dipendenza nel pom.xml
        if '<artifactId>junit</artifactId>' in content:
            print(f"Ho trovato JUnit")
            return True
        else:
            print(f"Non c'è JUnit")
            return False
    else:
        if(response.status_code == 403):
            print(f"Limite di richieste. Vado in sleep per 1 ora!")
            time.sleep(3670)

            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                content_data = response.json()
                content = base64.b64decode(content_data['content']).decode('utf-8')

                # Verifica se JUnit è una dipendenza nel pom.xml
                if '<artifactId>junit</artifactId>' in content:
                    print(f"Ho trovato JUnit")
                    return True
                else:
                    print(f"Non c'è JUnit")
                    return False
            else:
                print(f"Non c'è il pom: Risposta: {response}")
                return False
            # Se il file pom.xml non esiste, ritorna False
        else:
            print(f"Non c'è il pom: Risposta: {response}")
            return False

def save_to_file(data, filename):
    repositories_info = [{'name': repo['name'], 'url': repo['url']} for repo in data]

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(repositories_info, f, ensure_ascii=False, indent=4)


def get_intervals_for_month(year, month):
    if month in [1, 3, 5, 7, 8, 10, 12]:
        return [(1, 10), (11, 20), (21, 31)]
    elif month in [4, 6, 9, 11]:
        return [(1, 10), (11, 20), (21, 30)]
    elif month == 2:
        if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
            return [(1, 10), (11, 20), (21, 29)]
        else:
            return [(1, 10), (11, 20), (21, 28)]

def main(year):
    query_template = 'language:Java junit in:pom.xml created:{}-{:02d}-{:02d}..{}-{:02d}-{:02d}'

    for month in range(1, 13):
        intervals = get_intervals_for_month(year, month)
        all_results = []

        for start_day, end_day in intervals:
            query = query_template.format(year, month, start_day, year, month, end_day)
            print(f"Eseguendo query: {query}")
            results = search_github_repositories(query)

            if results:
                for result in results:
                    owner = result['owner']['login']
                    repo_name = result['name']
                    if check_pom_for_junit(owner, repo_name):
                        all_results.append({
                            'name': f"{owner}/{repo_name}",
                            'url': result['html_url']
                        })

                print(f"Numero di repository trovati per l'intervallo {start_day}-{end_day}: {len(all_results)}")

        # Salva i risultati del mese
        month_filename = f'github_repositories_{year}_{month:02d}.json'
        save_to_file(all_results, month_filename)
        print(f"I nomi dei repository e i loro link per il mese {month} sono stati salvati in '{month_filename}'.")


if __name__ == '__main__':
    year = 2024  # Metti l'anno che vuoi cercare
    main(year)
