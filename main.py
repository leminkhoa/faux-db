# main.py
try:
    from src.kuriboh import cli
except ImportError:
    print("Could not import cli from src.kuriboh")
    cli = None

if __name__ == '__main__':
    if cli:
        cli.main()
