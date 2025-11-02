from app.core.cli.app import main
import asyncio

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('\n Console Shutdown')