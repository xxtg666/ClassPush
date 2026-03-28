import sys
import os

# Add the classpush directory to sys.path so absolute imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    from app import ClassPushApp

    application = ClassPushApp()
    sys.exit(application.run())


if __name__ == "__main__":
    main()
