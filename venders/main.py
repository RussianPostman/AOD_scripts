import json
import time
import gspread
from pprint import pprint
from dataclasses import dataclass


@dataclass
class PriceParams:
    name: str
    vender: str = None


JSON_MASK = {
    "Version": "2.5",
    "EnableAutoCalculation": 0,
    "EnableAutoDestockAtRestart": 0,
    "EnableDefaultTraderStock": 0,
    "TraderCategories": []
}


JSON_FOOTER = [
    {
        "CategoryName": "---(Денежный-Размен)---",
        "Products": [
            "TraderPlus_Money_Ruble5000,1,-1,1,5000,-1",
            "TraderPlus_Money_Ruble2000,1,-1,1,2000,-1",
            "TraderPlus_Money_Ruble1000,1,-1,1,1000,-1",
            "TraderPlus_Money_Ruble500,1,-1,1,500,-1",
            "TraderPlus_Money_Ruble200,1,-1,1,200,-1",
            "TraderPlus_Money_Ruble100,1,-1,1,100,-1"
        ]
    },
    {
        "CategoryName": "---(Размен-Бабла)---",
        "Products": [
            "TraderPlus_Money_Ruble5000,1,-1,1,5000,-1",
            "TraderPlus_Money_Ruble2000,1,-1,1,2000,-1",
            "TraderPlus_Money_Ruble1000,1,-1,1,1000,-1",
            "TraderPlus_Money_Ruble500,1,-1,1,500,-1",
            "TraderPlus_Money_Ruble200,1,-1,1,200,-1",
            "TraderPlus_Money_Ruble100,1,-1,1,100,-1"
        ]
    }
]


def read_config(sh: gspread.Spreadsheet) -> dict:
    buy_config = {}
    sel_config = {}
    wsh = None

    for i in sh.worksheets():
        if i.title == 'Конфиг +':
            wsh = i
    
    if not wsh:
        return {}, {}

    names = wsh.col_values(2)[1:]

    buy_names = (i for i in names)
    buy_price = (i for i in wsh.col_values(3)[1:])
    buy_is_active = (i for i in wsh.col_values(4)[1:])
    buy_vender = (i for i in wsh.col_values(5)[1:])

    sel_names = (i for i in names)
    sel_price = (i for i in wsh.col_values(6)[1:])
    sel_is_active = (i for i in wsh.col_values(7)[1:])
    sel_vender = (i for i in wsh.col_values(8)[1:])

    for price in buy_price:
        name = next(buy_names).strip()
        active = next(buy_is_active).strip()
        vender = next(buy_vender).strip()
        vender = vender.lower() if len(vender) >= 2 else None

        if len(price.strip()) > 0 and 'да' in active.lower():
            buy_config[(name, vender)] = price
    
    for price in sel_price:
        name = next(sel_names).strip()
        active = next(sel_is_active).strip()
        vender = next(sel_vender).strip().lower()
        vender = vender.lower() if len(vender) >= 2 else None

        if len(price.strip()) > 0 and 'да' in active.lower():
            sel_config[(name, vender)] = price

    pprint(buy_config)
    pprint(sel_config)

    return buy_config, sel_config


def read_token() -> gspread.Client:
    with open('token/token.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
    return gspread.service_account_from_dict(data)


def one_seler_handler(
        wsh: gspread.Worksheet,
        buy_config: dict,
        sel_config: dict,
        venders_category_list: list
    ):
    names = wsh.col_values(2)
    value_1 = wsh.col_values(3)
    value_2 = wsh.col_values(4)
    value_3 = wsh.col_values(5)
    buy = wsh.col_values(6)
    sel = wsh.col_values(7)

    data_colls = [names, value_1, value_2, value_3, buy, sel]

    out_list = []
    one_seler_dict = {}
    vender = None

    for row_num in range(1, len(names)):
        
        if names[row_num].startswith('('):
            if one_seler_dict.get('CategoryName'):
                out_list.append(one_seler_dict.copy())
                one_seler_dict = {}
                
            venders_category_list.append(names[row_num])
            one_seler_dict['CategoryName'] = names[row_num]
            one_seler_dict['Products'] = []
            vender = names[row_num].strip().split()[0][1:-1].lower()
                    
        elif value_1[row_num] and value_1[row_num][-1].isdigit():
            conf_str = ','.join([str(i[row_num]) for i in data_colls[:4]])
            round_by = -1
            # print(vender)
            print((names[row_num], vender))

            # обработка цен на покупку
            if value := buy_config.get((names[row_num], vender)):
                conf_str += ',' + str(
                    int(round(int(buy[row_num]) * (int(value) / 100), round_by))
                )

            elif value := buy_config.get((names[row_num], None)):
                conf_str += ',' + str(
                    int(round(int(buy[row_num]) * (int(value) / 100), round_by))
                )
            
            elif value := buy_config.get((one_seler_dict['CategoryName'], vender)):
                conf_str += ',' + str(
                    int(round(int(buy[row_num]) * (int(value) / 100), round_by))
                )
            
            elif value := buy_config.get((one_seler_dict['CategoryName'], None)):
                conf_str += ',' + str(
                    int(round(int(buy[row_num]) * (int(value) / 100), round_by))
                )
            
            else:
                conf_str += ',' + str(buy[row_num])

            # обработка цен на продажу
            if value := sel_config.get((names[row_num], vender)):
                conf_str += ',' + str(
                    int(round(int(sel[row_num]) * (int(value) / 100), round_by))
                )

            elif value := sel_config.get((names[row_num], None)):
                conf_str += ',' + str(
                    int(round(int(sel[row_num]) * (int(value) / 100), round_by))
                )
            
            elif value := sel_config.get((one_seler_dict['CategoryName'], vender)):
                conf_str += ',' + str(
                    int(round(int(sel[row_num]) * (int(value) / 100), round_by))
                )
            
            elif value := sel_config.get((one_seler_dict['CategoryName'], None)):
                conf_str += ',' + str(
                    int(round(int(sel[row_num]) * (int(value) / 100), round_by))
                )
            
            else:
                conf_str += ',' + str(sel[row_num])
            
            one_seler_dict['Products'].append(conf_str)

    out_list.append(one_seler_dict.copy())

    return out_list


def main():
    gc = read_token()
    sh = gc.open_by_url("https://docs.google.com/spreadsheets/d/1LUf8ObmF-ohrIu_jhSWmrFxSVXYydyoK5XrrGQmI7OE/edit?gid=0#gid=0")
    buy_config, sel_config = read_config(sh)

    all_items = []
    venders_category_list = []
    for wsh in sh.worksheets():
        if wsh.title.startswith('+'):
            all_items += one_seler_handler(
                wsh,
                buy_config,
                sel_config,
                venders_category_list
            )
            print('Спим 25 сек')
            time.sleep(25)
    
    all_items += JSON_FOOTER
    JSON_MASK['TraderCategories'] = all_items
    
    with open("data.json", "w", encoding="utf-8") as file:
        json.dump(JSON_MASK, file)
    
    with open("venders_results/venders_category_list.json", "w", encoding="utf-8") as file:
        json.dump(venders_category_list, file)
    
    print('Готово')


if __name__ == '__main__':
    # python -m main

    main()