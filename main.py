# main.py
try:
    from src.faux import cli
except ImportError:
    print("Could not import cli from src.faux")
    cli = None

if __name__ == '__main__':
    if cli:
        cli.main()
