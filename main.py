from r9s.cli_tools.cli import main


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        raise SystemExit(0) from None
