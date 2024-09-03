import json
import math
from pprint import pprint
import pandas as pd
from dataclasses import dataclass
from collections import defaultdict 


@dataclass
class LootData:
    m_TypeName: str
    chance: float
    min: int
    max: int
    minq: float
    maxq: float
    minHealth: int
    maxHealth: int
    attachments: list


@dataclass
class Coordinates:
    coordinates: pd.ExcelFile

    def get_coordinate_by_num(self, tir_num: str) -> dict:
        out_dict = defaultdict(list)
        sheet_names = self.coordinates.sheet_names

        sheet = None

        for name in sheet_names:
            if int(name.split()[-1]) == tir_num:
                sheet = self.coordinates.parse(name)
        
        for _, row in sheet.iterrows():
            coord = [float(i.strip()) for i in row.iloc[2].split(',')]
            orient = [float(i.strip()) for i in row.iloc[3].split(',')]
            
            out_dict[row.iloc[1]].append({"pos": coord, "orient": orient})
        
        return out_dict
    

@dataclass
class Tirs:
    tirs: pd.ExcelFile

    def get_caches_names(self, list_name: str):
        out_list = []
        wsh = self.tirs.parse(list_name)

        for _, row in wsh.iterrows():
            if isinstance(row.iloc[11], str):
                out_list.append([row.iloc[10], row.iloc[11]])

        return out_list

    def get_attachments(self, row: pd.Series, coll: int = 2) -> list:
        sample = {
            "defaultattachments": [],
            "betterattachments": []
        }
        if isinstance(att_str := row.iloc[coll], str):
            sample["defaultattachments"] = [
                att.strip() for att in att_str.split(',')
            ]

        return sample
    
    def get_loot(self, list_name: str):
        out_list = []
        wsh = self.tirs.parse(list_name)

        for _, row in wsh.iterrows():
            if not row.iloc[0].lower().startswith('класснейм') \
                and isinstance(row.iloc[0], str):

                min = 1
                max = 1
                if isinstance(row.iloc[7], int):
                    min = row.iloc[7]
                if isinstance(row.iloc[8], int):
                    max = row.iloc[8]

                minq = 0.15
                maxq = 0.75
                if isinstance(row.iloc[5], float) and not math.isnan(row.iloc[5]):
                    minq = float(row.iloc[5])
                if isinstance(row.iloc[6], float) and not math.isnan(row.iloc[6]):
                    maxq = float(row.iloc[6])

                min_health = 15
                if row.isna().iloc[3] and row.iloc[3] > min_health:
                    min_health = float(row.iloc[3])
                
                max_health = 75
                if row.isna().iloc[4] and row.iloc[4] > min_health:
                    max_health = float(row.iloc[4])

                out_list.append(
                    {
                        "m_TypeName": row.iloc[0],
                        "chance": float(row.iloc[9]),
                        "min": min,
                        "max": max,
                        "minq": minq,
                        "maxq": maxq,
                        "minHealth": min_health,
                        "maxHealth": max_health,
                        "attachments": self.get_attachments(row)
                    }
                )

        return out_list


def main():
    coordinates_path = pd.ExcelFile('work_files/ТИРЫ.xlsx')
    tirs_path = pd.ExcelFile('work_files/КОРДЫ.xlsx')
    all_configs = {}

    coordinates = Coordinates(coordinates_path)
    tirs = Tirs(tirs_path)

    for work_list_name in tirs.tirs.sheet_names:
        tir_num = int(work_list_name.split()[-1])

        tir_coord_dict = coordinates.get_coordinate_by_num(tir_num)
        caches_names = tirs.get_caches_names(work_list_name)

        for cache in caches_names:
            one_config = {}

            one_config['m_Name'] = f'{cache[0]}_{tir_num}'
            one_config['m_Model'] = cache[0]
            one_config['m_Container'] = cache[1]
            one_config['m_PosOrient'] = tir_coord_dict[cache[0]]
            one_config['m_Items'] = tirs.get_loot(work_list_name)
            one_config['m_MinAmount'] = 100
            one_config['m_MaxAmount'] = 100

            all_configs[f'{cache[0]}_{tir_num}'] = one_config
    
    for config_name, config in all_configs.items():
        with open(f'results/{config_name}.json', 'w', encoding='u8') as f:
            json.dump(config, f)


if __name__ == '__main__':
    # python -m main

    main()