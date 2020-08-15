from lichessbot import StockfishBot


def main():
    import configparser

    config = configparser.ConfigParser()
    config.read('consts.ini')
    api_key = config['lichess']['API_KEY']
    stockfish = (r'C:\Users\danie\PythonProjects\lichessbot'
                 r'\stockfish-11-win\Windows\stockfish_20011801_32bit.exe')

    bot = StockfishBot(stockfish, level=1, api_key=api_key)
    bot.run()


if __name__ == '__main__':
    main()
