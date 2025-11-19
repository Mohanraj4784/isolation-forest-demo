#import mysql.connector
import pymysql
import pickle
import logging
from river import anomaly
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MySQLModelPersistence:
    def __init__(self, host="localhost", user="CARDHOST", password="CARDHOST", database="AI_MODEL"):
        self.conn = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            charset='utf8mb4'
        )
        self.create_table()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_model (
                id INT PRIMARY KEY,
                model LONGBLOB
            )
        """)
        self.conn.commit()

    def save_model(self, model):
            model_data = pickle.dumps(model)
            cursor = self.conn.cursor()
            # Use REPLACE so that we update the model if it exists.
            cursor.execute("REPLACE INTO ai_model (id, model) VALUES (%s, %s)", (1, model_data))
            self.conn.commit()

    def load_model(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT model FROM ai_model WHERE id = %s", (1,))
        row = cursor.fetchone()
        if row:
            return pickle.loads(row[0])
        return None
