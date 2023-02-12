import requests
from environs import Env
from terminaltables import AsciiTable


def predict_rub_salary(vacancy, currency, salary_from, salary_to):
    if vacancy['currency'] != currency:
        return None
    if vacancy[salary_from] and vacancy[salary_to]:
        return (vacancy[salary_from] + vacancy[salary_to]) / 2
    if vacancy[salary_to]:
        return vacancy[salary_to] * .8
    if vacancy[salary_from]:
        return vacancy[salary_from] * 1.2
    return None


def predict_rub_salary_hh(vacancy, currency, salary_from, salary_to):
    if not vacancy['salary']:
        return None
    salary_details = vacancy['salary']
    return predict_rub_salary(
        salary_details, currency,
        salary_from, salary_to)


def get_all_language_vacancies_hh(language, sj_api_key=None):
    url = 'https://api.hh.ru/vacancies'
    headers = {'User-Agent': 'HH-User-Agent'}
    all_vacancies = []
    page = 0
    pages_number = 1
    while page < pages_number:
        params = {'text': f"Программист {language}",
                  'area': 1, # id Москвы
                  'period': 30,
                  'page': page
                  }
        response = requests.get(url, params=params, headers=headers)
        page += 1
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError:
            continue
        page_payload = response.json()
        page_vacancies = page_payload['items']
        vacancies_found = page_payload['found']
        all_vacancies.extend(page_vacancies)
    return all_vacancies, vacancies_found


def get_average_language_salaries(predict_salary, vacancies,
                                  amount_of_vacancies, currency,
                                  salary_from, salary_to):
    total_salary = 0
    vacancies_processed = 0
    for vacancy in vacancies:
        salary = predict_salary(vacancy, currency, salary_from, salary_to)
        if salary:
            total_salary += salary
            vacancies_processed += 1
    average_salary = None
    if vacancies_processed:
        average_salary = int(total_salary / vacancies_processed)
    salaries_details = {'vacancies_found': amount_of_vacancies,
                        'vacancies_processed': vacancies_processed,
                        'average_salary': average_salary}
    return salaries_details


def get_all_languages_salary(get_all_language_vacancies,
                             predict_rub_salary,
                             currency,
                             salary_from,
                             salary_to, sj_api_key=None):
    languages = ['python', 'c', 'c#', 'c++', 'java', 'JavaScript', 'ruby', 'go', '1c']
    all_languages_salary = {}
    for language in languages:
        vacancies, amount_of_vacancies = get_all_language_vacancies(language, sj_api_key=sj_api_key)
        all_languages_salary[language] = get_average_language_salaries(
            predict_rub_salary,
            vacancies,
            amount_of_vacancies,
            currency,
            salary_from,
            salary_to)
    return all_languages_salary


def get_all_language_vacancies_sj(language, sj_api_key):
    url = 'https://api.superjob.ru/2.0/vacancies'
    page = 0
    next_page = True
    all_vacancies = []
    vacancies_found = 0
    while next_page:
        params = {'town': 4,  # id Москвы
                  'catalogues': 48,  # id каталога "Разработка, программирование"
                  'count': 5,  # api запрещает запрашивать больше 100 вакансий
                  'page': page,
                  'keyword': language,
                  'period': 0,
                  }
        headers = {'X-Api-App-Id': sj_api_key}
        page_response = requests.get(url, params, headers=headers)
        page += 1
        try:
            page_response.raise_for_status()
        except requests.exceptions.HTTPError:
            next_page = False
            continue
        decoder_response = page_response.json()
        all_vacancies.extend(decoder_response['objects'])
        vacancies_found = decoder_response['total']
        next_page = decoder_response['more']
    return all_vacancies, vacancies_found


def get_table(title, salary_statistics):
    salary_table = [['Язык программирования',
                     'Вакансий найдено',
                     'Вакансий обработано',
                     'Средняя зарплата']]
    salary_table.extend(
        [[language_name,
          salary_details['vacancies_found'],
          salary_details['vacancies_processed'],
          salary_details['average_salary']]
         for language_name, salary_details in salary_statistics.items()])
    table_instance = AsciiTable(salary_table, title)
    return table_instance.table


def main():
    env = Env()
    env.read_env()
    sj_api_key = env.str('SJ_KEY')
    salary_stats_hh = get_all_languages_salary(
        get_all_language_vacancies_hh,
        predict_rub_salary_hh,
        'RUR', 'from', 'to'
    )
    salary_stats_sj = get_all_languages_salary(
        get_all_language_vacancies_sj,
        predict_rub_salary,
        'rub', 'payment_from', 'payment_to',
        sj_api_key=sj_api_key
    )
    site_name = 'HaedHunter'
    print(get_table(site_name, salary_stats_hh))

    print()
    site_name = 'SuperJob'
    print(get_table(site_name, salary_stats_sj))


if __name__ == '__main__':
    main()

