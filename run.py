from pcs import create_app


if __name__ == '__main__':
    create_app('config').run(load_dotenv=True)
