import sqlite3 as sql
from typing import Any

class Database:
    __slots__ = ("_connection", "_cursor")
    
    
    def __init__(self) -> None:
        print("Initializing database connection!")
        
        try:
            self._connection = sql.connect("data\\tidebot.db")
            self._cursor     = self._connection.cursor()
        except Exception as e:
            print(e); exit(1)
    
        self.validate_databases()
    
    
    def validate_databases(self) -> None:
        res = self._cursor.execute("SELECT name FROM sqlite_master")
        
        if not any("gear" in table for table in res):
            print("Gear table doesn't exist! Initializing new table.")
            self._cursor.execute(""" CREATE TABLE gear(user_id INTEGER PRIMARY KEY, 
                                                       ap INTEGER, aap INTEGER, dp INTEGER, hp INTEGER, 
                                                       total_ap INTEGER, total_aap INTEGER, accuracy INTEGER, 
                                                       dr TEXT, dr_rate REAL, evasion TEXT, se_rate REAL,
                                                       class TEXT, level REAL, plan TEXT, gear INTEGER ) """)
        
        if not any("ranking" in table for table in res):
            print("Ranking table doesn't exist! Initializing new table.")
            self._cursor.execute(""" CREATE TABLE ranking(user_id INTEGER PRIMARY KEY, exp INTEGER, level INTEGER, 
                                                          bg_color INTEGER, full_bar_color INTEGER, progress_bar_color INTEGER,
                                                          text_color INTEGER, bg_image INTEGER ) """)
    
    
    def select(self, values: str, table: str, condition: str = "") -> None:
        self._cursor.execute(
            f"SELECT {values} FROM {table}{' WHERE ' if bool(condition) else ''}{condition}")
    
    
    def update(self, values: str, table: str, condition: str = "") -> None:
        self._cursor.execute(
            f"UPDATE {table} SET {values}{' WHERE ' if bool(condition) else ''}{condition}")


    def insert(self, values: str, table: str, condition: str = "") -> None:
        self._cursor.execute(
            f"INSERT INTO {table} VALUES {values}{' WHERE ' if bool(condition) else ''}{condition}")
    
    
    def delete(self, table: str, condition: str) -> None:
        self._cursor.execute(f"DELETE FROM {table} WHERE {condition}")
        
        
    def contains(self, table: str, condition: str) -> bool:
        self._cursor.execute(f"SELECT EXISTS(SELECT 1 FROM {table} WHERE {condition})")        
        res = self.fetchone()
        return bool(res[0])
    
    
    def fetchone(self) -> Any:
        return self._cursor.fetchone()
    
    
    def fetchall(self) -> list[Any]:
        return self._cursor.fetchall()
        
        
    def begin(self) -> None:
        self._cursor.execute("BEGIN")    
        
        
    def commit(self) -> None:
        self._connection.commit()


    def rollback(self) -> None:
        self._connection.rollback()


    def close(self) -> None:
        print("Closing database connection!")

        self._cursor.close()
        self._connection.close()     


    @property
    def connection(self):
        return self._connection
    
    
    @property
    def cursor(self):
        return self._cursor



db = Database()