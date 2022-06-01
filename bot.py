import krakenex
import json
import time
import datetime
import calendar

#get market data
def get_crypto_data(pair,since):
  return api.query_public('OHLC', data = {'pair': pair, 'since': since })['result'][pair] #get result only(filter)

def analyze(pair, since):
  #concatenate XETH + ZUSD
  data = get_crypto_data(pair[0] + pair[1], since)

  lowest = 0
  highest = 0
  
  for prices in data:
    balance = get_fake_balance() #can replace to get real balance
    last_trade = get_last_trade(pair[0] + pair[1])
    last_trade_price = float(last_trade['price'])

    open_ = float(prices[1])
    high_ = float(prices[2])
    low_ = float(prices[3])
    close_ = float(prices[4])

    did_sell = False #check if sold or bought
    #try to sell pair only if we have it
    try:
      balance[pair[0]]
      # if we own any pair currency that we are looking at then check sell
      #profit margin
      selling_point_win = last_trade_price * 1.005
      #stop loss
      selling_point_loss = last_trade_price * 0.995
      
      #selling at a win
      if open_ >= selling_point_win or close_ >= selling_point_win:
        #sell at a profit
        did_sell = True
        fake_sell(pair, close_, last_trade)
      elif open_ <= selling_point_loss or close_ <= selling_point_loss:
        #sell at a stop loss
        did_sell = True
        fake_sell(pair, close_, last_trade)
    except:
      pass

    #logic for if we should buy
    #check if we sold, cause if we sold we dont want to buy and check balance in account is sufficient
    if not did_sell and float(balance['USD.HOLD']) > 0:
      if low_ < lowest or lowest == 0:
        lowest = low_
      if high_ > highest:
        highest = high_
      price_to_buy = 1.0005
      if highest/lowest >= price_to_buy and low_ <= lowest:
        available_money = balance['USD.HOLD']
        #buy
        fake_buy(pair, available_money, close_, last_trade)

def fake_update_balance(pair, dollar_amount, close_, was_sold):
  balance = get_fake_balance()
  prev_balance = float(balance['USD.HOLD'])
  new_balance = 0
  if was_sold:
    new_balance = prev_balance + float(dollar_amount)
    del balance[pair[0]] #if we sell, sell of it so remove it from balance.json
  else:
    new_balance = prev_balance - float(dollar_amount)
    balance[pair[0]] = str(float(dollar_amount)/close_)
  balance['USD.HOLD'] = str(new_balance)

  with open('balance.json', 'w') as f:
    json.dump(balance, f, indent=4)

#dollar amount =  what we want to buy for
def fake_buy(pair, dollar_amount, close_, last_trade):
  trades_history = get_fake_trades_history()
  last_trade['price'] = str(close_)
  last_trade['type'] = 'buy'
  last_trade['cost'] = dollar_amount
  last_trade['time'] = datetime.datetime.now().timestamp()
  last_trade['vol'] = str(float(dollar_amount)/close_)

  #paper trade more complex need add trade to tradehistory and update balance
  trades_history['result']['trades'][str(datetime.datetime.now().timestamp())] = last_trade # add a new trade
  with open('tradeshistory.json', 'w') as f:
    json.dump(trades_history, f, indent=4)
    fake_update_balance(pair, dollar_amount, close_, False) #false because we bought
  # api.query_private('order', ) #to send an actual purchase order, 



def fake_sell(pair, close_, last_trade):
  trades_history = get_fake_trades_history()
  last_trade['price'] = str(close_)
  last_trade['type'] = 'sell'
  last_trade['cost'] = str(float(last_trade['vol']) * close_)
  last_trade['time'] = datetime.datetime.now().timestamp()

  trades_history['result']['trades'][str(datetime.datetime.now().timestamp())] = last_trade

  with open('tradeshistory.json', 'w') as f:
    json.dump(trades_history, f, indent=4)
    fake_update_balance(pair, float(last_trade['cost']), close_, True)


def get_last_trade(pair):
  trades_history = get_fake_trades_history()['result']['trades']

  last_trade = {}

  for trade in trades_history:
    trade = trades_history[trade]
    if trade['pair'] == pair and trade['type'] == 'buy':
      last_trade = trade
  return last_trade

def get_fake_balance():
  with open('balance.json', 'r') as f:
    return json.load(f)

def get_fake_trades_history():
  with open('tradeshistory.json', 'r') as f:
    return json.load(f)


# get your outstanding balance
def get_balance():
  #Note if you have no money, exclude `result`, else it will return error
  # return api.query_private('Balance')['result']
  return api.query_private('Balance')

def get_trades_history():
  start_date = datetime.datetime(2021,7,4)
  end_date = datetime.datetime.today()
  return api.query_private("TradesHistory", req(start_date, end_date, 1))['result']['trades']

def date_nix(str_date):
  return calendar.timegm(str_date.timetuple())

#request for the kraken api, get trades history
def req(start, end, ofs):
  req_data = {
    'type': 'all',
    'trades': 'true',
    'start': str(date_nix(start)),
    'end': str(date_nix(end)),
    'ofs': str(ofs)
  }
  return req_data



if __name__ == '__main__':

  api = krakenex.API() #connection to API
  api.load_key('kraken.key')#load our key to authenticate ourself and get data specific to us
  # pair = "XETHZUSD" #ethereum vs USD in krakenAPI, more info: https://api.kraken.com/0/public/AssetPairs
  pair = ("XETH", "ZUSD")
  since = str(int(time.time() - 36000)) #3600s = 1hr

  #can create an array of pairs to analyse and run it in a while loop
  #eg while True: analyze(pair)

  analyze(pair,since)

  print(json.dumps(get_fake_trades_history(), indent=4))

