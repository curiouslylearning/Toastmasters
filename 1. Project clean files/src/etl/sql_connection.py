#Functions for connecting with the SQL database
from sqlalchemy import create_engine


#OBS! Ändra så att dessa ligger i en annan fil, så att inlogg o lösen inte riskerar ligga öppet

def sql_engine():
    USER = "postgres"
    PASSWORD = "CDTMmd2025!"
    HOST = "127.0.0.1"  # "localhost"
    PORT = 5432
    DB = "Toastmasters"

    engine = create_engine(
        f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB}",
        connect_args={"connect_timeout": 5},)

    return engine