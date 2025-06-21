import json
from itemadapter import ItemAdapter
import psycopg2
from psycopg2 import IntegrityError
from dotenv import load_dotenv
import os

load_dotenv()

dbname = os.getenv("dbname")
user = os.getenv("user")
password = os.getenv("password")
host = os.getenv("host")
port = os.getenv("port")
table_name = os.getenv("table_name")


class SchemeFinderPipeline:
    def open_spider(self, spider):
        try:
            self.conn = psycopg2.connect(
                dbname=dbname, user=user, password=password, host=host, port=port
            )
            self.cur = self.conn.cursor()
            self.cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id SERIAL PRIMARY KEY,
                    slug TEXT UNIQUE,
                    url TEXT,
                    name TEXT,
                    tags TEXT[],  -- Assuming tags are a list of strings
                    state TEXT[], -- Assuming state is a list of strings
                    category TEXT[], -- Assuming category is a list of strings
                    description TEXT,
                    age JSONB, -- Assuming age is a JSONB object
                    benefits TEXT,
                    exclusions TEXT,
                    process TEXT,
                    eligibility TEXT,
                    documents_required TEXT
                )
                """
            )
            self.conn.commit()
        except psycopg2.Error as e:
            spider.logger.error(f"Error opening database connection: {e}")
            raise

    def close_spider(self, spider):
        try:
            if self.cur:
                self.cur.close()
            if self.conn:
                self.conn.close()
        except psycopg2.Error as e:
            spider.logger.error(f"Error closing database connection: {e}")

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        try:
            age = json.dumps(adapter.get("age"))
            values_to_insert = (
                adapter.get("slug"),
                adapter.get("url"),
                adapter.get("name"),
                adapter.get("tags"),
                adapter.get("state"),
                adapter.get("category"),
                adapter.get("description"),
                age,
                adapter.get("benefits"),
                adapter.get("exclusions"),
                adapter.get("process"),
                adapter.get("eligibility"),
                adapter.get("documents_required"),
            )

            self.cur.execute(
                f"""
                INSERT INTO {table_name} (
                    slug, url, name, tags, state, category, description, age, benefits, exclusions, process, eligibility, documents_required
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                values_to_insert,
            )
            self.conn.commit()

        except IntegrityError:
            self.conn.rollback()
            spider.logger.info(f"Duplicate entry for slug: {adapter.get('slug')}")
        except psycopg2.Error as e:
            spider.logger.error(f"Error processing item: {e}, item: {item}")
            self.conn.rollback()
        return item
