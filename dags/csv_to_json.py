import os
import pandas as pd
import json
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime


CSV_FILE_PATH = "STOCK_LIST.csv"
JSON_FILE_PATH = "STOCK_LIST.json"

def csv_to_json():
    """CSV 데이터를 읽어 JSON 형식으로 변환"""
    if not os.path.exists(CSV_FILE_PATH):
        raise FileNotFoundError(f"CSV file not found at {CSV_FILE_PATH}")
    
    # CSV 읽기
    df = pd.read_csv(CSV_FILE_PATH)
    
    # DataFrame을 JSON으로 변환
    json_data = df.to_dict(orient="records")
    
    # JSON 데이터 저장
    with open(JSON_FILE_PATH, "w") as json_file:
        json.dump(json_data, json_file, indent=4)
    
    print(f"JSON data saved to {JSON_FILE_PATH}")

# 기본 DAG 설정
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
}

with DAG(
    dag_id='csv_to_json',
    default_args=default_args,
    description='Convert CSV data to JSON format',
    schedule_interval=None,
    start_date=datetime(2025, 2, 18),
    catchup=False,
) as dag:

    convert_csv_to_json = PythonOperator(
        task_id='convert_csv_to_json',
        python_callable=csv_to_json,
    )

convert_csv_to_json