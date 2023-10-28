import requests as r
import pandas as pd
import psycopg2 as ps


class DBConnection:
    def __init__(self):
        self.connection = ps.connect(
            host='localhost',
            port='5434',
            user='postgres',
            password='postgres',
            database='testdb'
        )

    def get_connection(self):
        return self.connection


class MonthRates:
    url_base = 'http://api.exchangerate.host/'
    api_method = 'timeframe'
    api_key = '9320603ab554ad114bd43b3d4b5905c0'
    result = []

    def __init__(self, start_date, end_date, rate_base, rate_target, connection):
        self.start_date = start_date
        self.end_date = end_date
        self.rate_base = rate_base
        self.rate_target = rate_target
        self.connection = connection

    def get_rates(self):
        url = self.url_base + self.api_method
        return r.get(url, params={'access_key': self.api_key,
                                  'source': self.rate_base,
                                  'currencies': self.rate_target,
                                  'start_date': self.start_date,
                                  'end_date': self.end_date,
                                  'format': 1})

    def generate_rate_list(self, rate_list):
        for day in rate_list['quotes']:
            self.result.append(
                tuple((
                    day,
                    self.rate_base,
                    self.rate_target,
                    rate_list['quotes'][day][self.rate_base + self.rate_target]
                ))
            )

    def rate_to_db(self):
        cursor = self.connection.cursor()
        query = "TRUNCATE public.rates"
        cursor.execute(query)
        query = "INSERT INTO public.rates (get_date, rate_base, rate_target, rate) VALUES (%s, %s, %s, %s)"
        cursor.executemany(query, self.result)
        cursor.close()
        self.connection.commit()

    def get_from_db(self, table_name):
        cursor = self.connection.cursor()
        try:
            query = 'SELECT * FROM public.' + table_name
            cursor.execute(query)
            return cursor.fetchall()
        finally:
            cursor.close()

    def create_table_indicators(self, ind):
        cursor = self.connection.cursor()
        query = ''' CREATE TABLE IF NOT EXISTS public.indicators (
                        month varchar(15),
                        rate_base varchar(5),
                        rate_target varchar(5),
                        day_max_rate date,
                        day_min_rate date,
                        max_rate numeric,
                        min_rate numeric,
                        avg_rate numeric,
                        last_day_rate numeric
                        );'''
        cursor.execute(query)

        query = ("INSERT INTO public.indicators VALUES ('{}', '{}', '{}', '{}', '{}', {}, {}, {}, {});"
                 .format('Сентябрь', self.rate_base, self.rate_target, ind['day_max_rate'], ind['day_min_rate'],
                         ind['max_rate'], ind['min_rate'], ind['avg_rate'], ind['last_day_rate']))
        cursor.execute(query)

        cursor.close()
        self.connection.commit()


class RateCalculator:
    max_rate = ''
    min_rate = ''
    avg_rate = ''
    day_max_rate = ''
    day_min_rate = ''
    last_day_rate = ''

    def __init__(self, df):
        self.df = df

    def get_day_max_rate(self):
        print("day_max_rate")
        if (self.max_rate == ''):
            self.get_max_rate()
        self.day_max_rate = df.loc[df['rate'] == self.max_rate, 'get_date'].values[0]
        return self.day_max_rate

    def get_day_min_rate(self):
        print("day_min_rate")
        if (self.min_rate == ''):
            self.get_min_rate()
        self.day_min_rate = df.loc[df['rate'] == self.min_rate, 'get_date'].values[0]
        return self.day_min_rate

    def get_max_rate(self):
        print("max_rate")
        self.max_rate = df['rate'].max()
        return self.max_rate

    def get_min_rate(self):
        print("min_rate")
        self.min_rate = df['rate'].min()
        return self.min_rate

    def get_avg_rate(self):
        print("avg_rate")
        self.avg_rate = df['rate'].mean()
        return self.avg_rate

    def get_last_day_rate(self):
        print("last_day_rate")
        df_sort = df.sort_values('get_date')
        self.last_day_rate = df_sort['rate'].iloc[-1]
        return self.last_day_rate


connection = DBConnection().get_connection()

# Создаю объект для получения и записи в БД курсов валют за определнный период, по определенным валютным парам 
btcusd = MonthRates('2023-09-01', '2023-09-30', 'BTC', 'USD', connection)

# Получаю список курсов
response = btcusd.get_rates()
if response.status_code == 200:
    rates = response.json()

    # Преобразовываю список в необходимый вид
    btcusd.generate_rate_list(rates)

    # Записываю курсы в базу данных
    btcusd.rate_to_db()

    # Читаю из базы данных
    rate_list = btcusd.get_from_db('rates')
    print(rate_list)

    # Формирую датафрейм
    df = pd.DataFrame(rate_list, columns=['rate_id', 'get_date', 'rate_base', 'rate_target', 'rate'])

    # Создаю объект для вычисления показателей
    calculator = RateCalculator(df)

    # Вычисляю показатели
    indicators = {'max_rate': calculator.get_max_rate(),
                  'min_rate': calculator.get_min_rate(),
                  'avg_rate': calculator.get_avg_rate(),
                  'day_max_rate': calculator.get_day_max_rate(),
                  'day_min_rate': calculator.get_day_min_rate(),
                  'last_day_rate': calculator.get_last_day_rate()}

    # Формирую витрину с показателями
    btcusd.create_table_indicators(indicators)


else:
    print('Ошибка при выполнении запроса:', response.status_code)
    connection.close()
