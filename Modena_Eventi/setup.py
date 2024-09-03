import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'modena_eventi.settings')
django.setup()


from modena_eventi.setupDB import init_db, erase_db


if __name__ == "__main__":
    erase_db()
    init_db()