import os
import pandas as pd
import json
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from sqlalchemy import create_engine


CSV_FILE_PATH = "/opt/airflow/dags/STOCK_LIST.csv"
JSON_FILE_PATH = "/opt/airflow/dags/STOCK_LIST.json"

def csv_to_json():
    """CSV 데이터를 읽어 JSON 형식으로 변환"""
    if not os.path.exists(CSV_FILE_PATH):
        raise FileNotFoundError(f"CSV file not found at {CSV_FILE_PATH}")
    
    # CSV 읽기
    df = pd.read_csv(CSV_FILE_PATH)

    # NaN 값을 빈문자열로 대체
    df = df.fillna("")

    # 컬럼 이름 매핑 (한국어 -> 영어)
    column_mapping = {
        "날짜": "trd_dd",
        "종목코드": "isu_cd",
        "종목명": "isu_kor_nm",
        "시장구분": "market_code",
        "소속부": "market_division",
        "종가": "close_price",
        "대비": "price_diff",
        "등락률": "fluctuation_rate",
        "시가": "open_price",
        "고가": "high_price",
        "저가": "low_price",
        "거래량": "volume",
        "거래대금": "transaction_amount",
        "시가총액": "market_cap",
        "상장주식수": "listed_shares_count"
    }
    df.rename(columns=column_mapping, inplace=True)
    
    # DataFrame을 JSON으로 변환
    json_data = df.to_dict(orient="records")
    
    # JSON 데이터 저장
    with open(JSON_FILE_PATH, "w") as json_file:
        json.dump(json_data, json_file, ensure_ascii=False, indent=4)
    
    print(f"JSON data saved to {JSON_FILE_PATH}")

def preprocess_and_store_to_postgres():
    """JSON 데이터를 전처리하고 PostgreSQL에 저장"""
    if not os.path.exists(JSON_FILE_PATH):
        raise FileNotFoundError(f"JSON file not found at {JSON_FILE_PATH}")

    # JSON 파일 읽기
    with open(JSON_FILE_PATH, "r") as json_file:
        data = json.load(json_file)

    # 데이터프레임으로 변환 및 전처리 (예: 특정 열 필터링)
    ## 필요한 키만 추출
    filtered_data = [
        {key: item[key] for key in ['isu_cd', 'isu_kor_nm', 'market_code'] if key in item}
        for item in data
    ]

    df = pd.DataFrame(filtered_data)

    # PostgreSQL 데이터베이스 연결
    engine = create_engine('postgresql://postgres:1234@stock:5432/stock')

    # PostgreSQL에 저장
    with engine.connect() as connection:
        df.to_sql('kr_stock_list', con=connection, if_exists='replace', index=False)
        result = connection.execute("SELECT 'Connection successful!'")
        print(result.scalar())


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

    process_and_store_task = PythonOperator(
        task_id='process_json_and_store_to_postgres',
        python_callable=preprocess_and_store_to_postgres,
    )

convert_csv_to_json >> process_and_store_task