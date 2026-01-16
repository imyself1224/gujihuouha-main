import json
import csv


def clean_entity(entity):
    """清洗实体，去除括号"""
    if entity.startswith('(') and entity.endswith(')'):
        return entity[1:-1]
    return entity


def convert_json_to_csv(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f_in, \
            open(output_file, 'w', newline='', encoding='utf-8') as f_out:

        writer = csv.writer(f_out)
        writer.writerow(['head', 'tail', 'relation'])  # 写入CSV表头

        for line in f_in:
            data = json.loads(line.strip())
            spo_list = data['spo_list']

            for spo in spo_list:
                subject = clean_entity(spo['subject'])
                predicate = spo['predicate']
                obj = clean_entity(spo['object'])

                writer.writerow([subject, obj, predicate])


if __name__ == '__main__':
    input_filename = 'RE-Hangaozubenji.json'
    output_filename = 're.csv'
    convert_json_to_csv(input_filename, output_filename)