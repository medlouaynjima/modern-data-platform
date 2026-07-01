from fastapi import FastAPI
from impala.dbapi import connect
import pandas as pd
from typing import List, Dict, Any

app = FastAPI(title="Modern Data Platform API")

def get_connection():
    # Connect to Spark Thrift Server
    return connect(host='spark-thrift', port=10000, auth_mechanism='PLAIN')

@app.get("/sales/daily")
def get_daily_sales() -> List[Dict[str, Any]]:
    query = """
    SELECT order_date as date, 
           sum(gross_revenue) as total_sales_amount, 
           sum(order_count) as total_orders 
    FROM fct_daily_sales 
    GROUP BY order_date 
    ORDER BY order_date DESC LIMIT 30
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                results = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                df = pd.DataFrame(results, columns=columns)
                if 'date' in df.columns:
                    df['date'] = df['date'].astype(str)
                return df.to_dict(orient="records")
    except Exception as e:
        return [{"error": str(e)}]

@app.get("/customers/top")
def get_top_customers() -> List[Dict[str, Any]]:
    query = """
    SELECT customer_id, sum(revenue) as total_spent, sum(orders) as total_orders 
    FROM fct_customer_activity 
    GROUP BY customer_id 
    ORDER BY total_spent DESC LIMIT 10
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                results = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                df = pd.DataFrame(results, columns=columns)
                return df.to_dict(orient="records")
    except Exception as e:
        return [{"error": str(e)}]

@app.get("/inventory/position")
def get_inventory_position() -> List[Dict[str, Any]]:
    query = "SELECT * FROM fct_inventory_position ORDER BY snapshot_date DESC LIMIT 50"
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                results = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                df = pd.DataFrame(results, columns=columns)
                if 'snapshot_date' in df.columns:
                    df['snapshot_date'] = df['snapshot_date'].astype(str)
                return df.to_dict(orient="records")
    except Exception as e:
        return [{"error": str(e)}]

@app.get("/health")
def health_check():
    return {"status": "ok"}
