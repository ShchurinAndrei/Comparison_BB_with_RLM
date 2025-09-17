import requests
from requests.auth import HTTPBasicAuth
import json
import os
import yaml
import glob
import locale

usrname = os.getlogin()
usrname = usrname.split('@')[0]
psswd_SIGMA = input('Введите пароль пользователя для домена SIGMA:')
psswd_OMEGA = input('Введите пароль пользователя для домена OMEGA:')


url_PROD = 'https://sbrf-bitbucket.sigma.sbrf.ru/rest/api/1.0/projects/CI00149046/repos/ci00149046_sbbol/raw/environments/PROD/group_vars/gotham_ca/stand_PROD.yaml'
url_LT = 'https://sbrf-bitbucket.sigma.sbrf.ru/rest/api/1.0/projects/CI00149046/repos/ci00149046_sbbol/raw/environments/IFT/group_vars/gotham_delta/stand_LT.yaml'
url_IFT = 'https://sbrf-bitbucket.sigma.sbrf.ru/rest/api/1.0/projects/CI00149046/repos/ci00149046_sbbol/raw/environments/IFT/group_vars/gotham_delta/stand_IFT.yaml'
url_PSI = 'https://sbrf-bitbucket.sigma.sbrf.ru/rest/api/1.0/projects/CI00149046/repos/ci00149046_sbbol/raw/environments/PSI/group_vars/gotham_ca/stand_PSI.yaml'
url_list = [url_PROD, url_PSI, url_IFT, url_LT]

str_table_main = ''
team_dict_main = {}
str_table_standin = ''
team_dict_standin = {}
grope_host_dict = {}
without_CI_STAND = []

# функция заполнения словаря соответсвий стенд-хосты
def get_CI_STAND(title):
    FP_list = yml_data[title]['inventory'].keys()
    for FP in FP_list:
        try:
            # print(FP)
            hosts = list()
            role_list = list()
            FP_clusters = yml_data[title]['inventory'][FP]['clusters']

            for i in FP_clusters:
                role_list.append(i['cluster_role'])
            for i in range(len(role_list)):
                host_list = yml_data[title]['inventory'][FP]['clusters'][i]['hosts']
                CI_STAND = yml_data[title]['inventory'][FP]['clusters'][i]['CI_STAND']
                for i in host_list:
                    hosts.append(i['host'])
                    if CI_STAND in grope_host_dict:
                        grope_host_dict[CI_STAND].append(i['host'].split('.', 1)[0])
                    else:
                        grope_host_dict[CI_STAND] = [i['host'].split('.', 1)[0]]
        except Exception:
            # print (f'{FP} - без CI_STAND')
            without_CI_STAND.append(FP)
    # print(grope_host_dict)
    return grope_host_dict, without_CI_STAND

# функция получения хостов по CI стенда из RLM
def select_from_RLM(CI_STAND):
    rlm_url = 'https://rlm.sigma.sbrf.ru'
    user_rlm = {}
    request_data = {
        "checked":None,
        "filters":{"2594": {}},
        "searchUnmatched":False,
        "segments":{},
        "service":"pgsediagnostic",
        "sort_column":None,
        "sort_direction":None,
        "task":None,
        "terms": {"invstend_ci_stend": CI_STAND},
        "unloader":None
    }

    session = requests.Session()
    requests.packages.urllib3.disable_warnings()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 SberBrowser/26.0.0.0",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    session.headers.update(headers)
    r = session.get(rlm_url, verify=False)
    session.cookies.update(r.cookies)
    r = session.post(rlm_url + '/api/auth', json={"username": usrname, "password": psswd_OMEGA},headers=headers, verify=False)

    if r.status_code == 200:
        user_rlm = r.json()
    else:
        return f"Error: {r.status_code}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36  SberBrowser/11.2.68.1",
        "Accept": "*/*", "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7", "Content-Type": "application/json",
        "Authorization": user_rlm["token_type"] + " " + user_rlm["token"]}

    session.headers.update(headers)
    resp = requests.post(rlm_url + '/api/dashboard/records/psqlseclusterstandalone/search.json?page_size=100', json=request_data, verify=False,headers=headers)
    return resp

# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

requests.packages.urllib3.disable_warnings()
for url in url_list:    # цикл по файлам из BB
    if url.split('/')[-1] == 'stand_PROD.yaml':
        title = 'gotham_dict_prod'
    elif url.split('/')[-1] == 'stand_LT.yaml':
        title = 'gotham_dict_lt2'
    elif url.split('/')[-1] == 'stand_IFT.yaml':
        title = 'gotham_dict_ift'
    elif url.split('/')[-1] == 'stand_PSI.yaml':
        title = 'gotham_dict_psi'

    requests.packages.urllib3.disable_warnings()
    response = requests.get(url, auth=HTTPBasicAuth(usrname, psswd_SIGMA), headers={"Content-Type": "application/json"}, params={"limit":"10000"}, verify=False)
    cod = response.status_code
    with open('stand.yaml', 'w', encoding='utf-8') as outfile:
        outfile.writelines(response.text)
        outfile.close()
    with open('stand.yaml', 'r', encoding='utf-8') as yaml_file:
        yml_data = yaml.load(yaml_file, Loader=yaml.FullLoader)
        yaml_file.close()

    grope_host_dict, without_CI_STAND = get_CI_STAND(title)
    if title == 'gotham_dict_prod':
        url_PROD_SIGMA = 'https://sbrf-bitbucket.sigma.sbrf.ru/rest/api/1.0/projects/CI00149046/repos/ci00149046_sbbol/raw/environments/PROD/group_vars/gotham_sigma/stand_PROD.yaml'
        requests.packages.urllib3.disable_warnings()
        response = requests.get(url_PROD_SIGMA, auth=HTTPBasicAuth(usrname, psswd_SIGMA), headers={"Content-Type": "application/json"}, params={"limit": "10000"}, verify=False)
        with open('stand.yaml', 'w', encoding='utf-8') as outfile:
            outfile.writelines(response.text)
            outfile.close()
        with open('stand.yaml', 'r', encoding='utf-8') as yaml_file:
            yml_data = yaml.load(yaml_file, Loader=yaml.FullLoader)
            yaml_file.close()
        grope_host_dict, without_CI_STAND = get_CI_STAND(title)


    # Создание сессии подключения к RLM
    session = requests.Session()

    for CI_STAND in grope_host_dict:
        hosts_RLM = []
        missing_BB = []
        missing_RLM = []
        FP_CI_STAND = {}
        response = select_from_RLM(CI_STAND)
        if type(response) == str:
            raise SystemExit("Ошибка подключения к RLM:" + response)
        response_json = response.json()

        if response.status_code == 200:
                response_json = response.json()
                for host in response_json["results"]:
                    hosts_RLM.append(host["invsvm_aliaces"][0])

                hosts_RLM = list(set(hosts_RLM))
                missing_BB = [x for x in grope_host_dict[CI_STAND] if x not in hosts_RLM]
                missing_RLM = [x for x in hosts_RLM if x not in grope_host_dict[CI_STAND]]

                if len(missing_BB) == 0 and len(missing_RLM) == 0:
                    # print(f'ФП "{group_zabbix}" - идентично')
                    pass
                elif len(missing_BB) != 0 and len(missing_RLM) == 0:
                    print (f'"{CI_STAND}" - РАСХОДИТЬСЯ!\nЕсть в BB, но нет в RLM: {missing_BB}')
                elif len(missing_BB) == 0 and len(missing_RLM) != 0:
                    print (f'"{CI_STAND}" - РАСХОДИТЬСЯ!\nЕсть в RLM, но нет в BB: {missing_RLM}')
                else:
                    print (f'"{CI_STAND}" - РАСХОДИТЬСЯ!\nЕсть в BB, но нет в RLM: {missing_BB}\nЕсть в RLM, но нет в BB: {missing_RLM}')
    if len(without_CI_STAND) != 0:
        print('ФП с неуказанными CI_STAND в BB: ' + str(without_CI_STAND))
