from dotenv import load_dotenv
import os


load_dotenv()

bot_token = os.getenv("BOT_TOKEN")

postrges_user = 'postgres'
postrges_password = os.getenv('POSTGRES_PASSWORD')
postrges_host = 'postgres-db'
postrges_port = 5432
postrges_db = ''