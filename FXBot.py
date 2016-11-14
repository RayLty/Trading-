from base import *
import datetime
class FXBot(BaseBot):
    def __init__(self):
        super(FXBot, self).__init__()
        self.contracts = [0]*8 # EURJPY/CHFJPY/USDCHF/EURCHF/EURCAD/EURUSD/USDJPY/USDCAD
        self.cash = [0]*8 # JPY/EUR/USD/CHF/CAD
        self.limits = [102000000, 900000, 1000000, 980000, 1300000] # JPY/EUR/USD/CHF/CAD
        self.bids = [] # EURJPY/CHFJPY/USDCHF/EURCHF/EURCAD/EURUSD/USDJPY/USDCAD
        self.asks = [] # EURJPY/CHFJPY/USDCHF/EURCHF/EURCAD/EURUSD/USDJPY/USDCAD
        self.tickers = ['EURJPY', 'CHFJPY', 'USDCHF', 'EURCHF', 'EURCAD', 'EURUSD', 'USDJPY', 'USDCAD']
        self.bestBids = [0]*8
        self.bestAsks = [0]*8
        self.bestQuantityBids = [0]*8
        self.bestQuantityAsks = [0]*8
        self.lastActionTime = 0
        self.currentTime = 0


    def update_state(self, msg):
        if self.options.get('verbose'):
            print(msg)
        message_type = msg.get('message_type')
        orders = []
        if msg.get('elapsed_time'):
            self.currentTime = msg.get('elapsed_time')
            if len(self.bids) > 0 and self.currentTime - self.lastActionTime >= 1:
                self.lastActionTime = self.currentTime
                self.bestBidAndQuantity()
                self.bestAskAndQuantity()
                orders.extend(self.arbitrage())
            if len(orders) > 0:
                action = {
                    'message_type': 'MODIFY ORDERS',
                    'orders': orders,
                }
                orders = dumps(action)
        if message_type == 'ACK REGISTER':
            market_states = msg['market_states']
            self.bids = [market_states['EURJPY']['bids'], market_states['CHFJPY']['bids'], \
            market_states['USDCHF']['bids'], market_states['EURCHF']['bids'],\
            market_states['EURCAD']['bids'], market_states['EURUSD']['bids'],\
            market_states['USDJPY']['bids'], market_states['USDCAD']['bids']]
            self.asks = [market_states['EURJPY']['asks'], market_states['CHFJPY']['asks'], \
            market_states['USDCHF']['asks'], market_states['EURCHF']['asks'],\
            market_states['EURCAD']['asks'], market_states['EURUSD']['asks'],\
            market_states['USDJPY']['asks'], market_states['USDCAD']['asks']]
            positions = msg['trader_state']['positions']
            self.contracts = [positions['EURJPY'], positions['CHFJPY'], \
            positions['USDCHF'], positions['EURCHF'], positions['EURCAD'], \
            positions['EURUSD'], positions['USDJPY'], positions['USDCAD']]
            cash = msg['trader_state']['cash']
            self.cash = [cash['JPY'], cash['EUR'], cash['USD'], cash['CHF'], cash['CAD']]
            print('register')
        elif message_type == 'TRADER UPDATE':
            positions = msg['trader_state']['positions']
            cash = msg['trader_state']['cash']
            self.contracts = [positions['EURJPY'], positions['CHFJPY'], \
            positions['USDCHF'], positions['EURCHF'], positions['EURCAD'], \
            positions['EURUSD'], positions['USDJPY'], positions['USDCAD']]
            self.cash = [cash['JPY'], cash['EUR'], cash['USD'], cash['CHF'], cash['CAD']]
        elif message_type == 'MARKET UPDATE':
            #print('market update')
            ticker = msg['market_state']['ticker']
            bids = msg['market_state']['bids']
            asks = msg['market_state']['asks']
            if ticker == 'EURJPY':
                self.bids[0] = bids
                self.asks[0] = asks
            if ticker == 'CHFJPY':
                self.bids[1] = bids
                self.asks[1] = asks
            if ticker == 'USDCHF':
                self.bids[2] = bids
                self.asks[2] = asks
            if ticker == 'EURCHF':
                self.bids[3] = bids
                self.asks[3] = asks
            if ticker == 'EURCAD':
                self.bids[4] = bids
                self.asks[4] = asks
            if ticker == 'EURUSD':
                self.bids[5] = bids
                self.asks[5] = asks
            if ticker == 'USDJPY':
                self.bids[6] = bids
                self.asks[6] = asks
            if ticker == 'USDCAD':
                self.bids[7] = bids
                self.asks[7] = asks
        elif message_type == 'NEWS':
            print('News update:')
            print(msg)
        elif message_type == 'TRADE':
            pass
        elif message_type == 'PING':
            pass
        elif message_type == 'ACK MODIFY ORDERS':
            #print(msg)
            pass
        else:
            print('Other message:')
            print(msg)
        if len(orders) > 0:
            return orders
        else:
            return None

    def bestBidAndQuantity(self):
        for index in range(8):
            bids = self.bids[index]
            highestBid = 0.0
            quantity = 0
            for bid in bids:
                if float(bid) > highestBid:
                    highestBid = float(bid)
                    quantity = bids[bid]
            self.bestBids[index] = highestBid
            self.bestQuantityBids[index] = quantity
        
    def bestAskAndQuantity(self):
        for index in range(8):
            asks = self.asks[index]
            lowestAsk = 1000.0
            quantity = 0
            for ask in asks:
                if float(ask) < lowestAsk:
                    lowestAsk = float(ask)
                    quantity = asks[ask]
            self.bestAsks[index] = lowestAsk
            self.bestQuantityAsks[index] = quantity

    def idxBaseQuote(self, index):
        if index == 0:
            return (1, 0)
        if index == 1:
            return (3, 0)
        if index == 2:
            return (2, 3)
        if index == 3:
            return (1, 3)
        if index == 4:
            return (1, 4)
        if index == 5:
            return (1, 2)
        if index == 6:
            return (2, 0)
        if index == 7:
            return (2, 4)

    def calculateQuantities(self, idx1, idx2, idx3, direction):
        multiplier = -1.05
        (base1, quote1) = self.idxBaseQuote(idx1)
        (base2, quote2) = self.idxBaseQuote(idx2)
        (base3, quote3) = self.idxBaseQuote(idx3)
        quantity1 = 0
        quantity2 = 0
        quantity3 = 0
        if direction == -1: # short
            quantity1 = self.bestQuantityBids[idx1]
            quantity2 = self.bestQuantityBids[idx2]
            quantity3 = self.bestQuantityAsks[idx3]
            exchange1 = self.bestBids[idx1]
            exchange2 = self.bestBids[idx2]
            exchange3 = self.bestAsks[idx3]
            quantity1_limit = min(self.limits[base1]+self.cash[base1], 1.0/exchange1*(self.limits[quote1]-self.cash[quote1]), 1000)
            quantity2_limit = min(self.limits[base2]+self.cash[base2], 1.0/exchange2*(self.limits[quote2]-self.cash[quote2]), 1000)
            quantity3_limit = min(self.limits[base3]-self.cash[base3], 1.0/exchange3*(self.limits[quote3]+self.cash[quote3]), 1000)
            quantity1 = min(quantity1, quantity1_limit)
            quantity2 = min(quantity2, quantity2_limit)
            quantity3 = min(quantity3, quantity3_limit)
            quantity1 = min(quantity1, quantity3, quantity2/exchange1)
            quantity1 = int(quantity1*multiplier)
            quantity2 = int(quantity1*exchange1)
            quantity3 = int(-quantity1)
        else:
            quantity1 = self.bestQuantityAsks[5]
            quantity2 = self.bestQuantityAsks[7]
            quantity3 = self.bestQuantityBids[4]
            exchange1 = self.bestAsks[idx1]
            exchange2 = self.bestAsks[idx2]
            exchange3 = self.bestBids[idx3]
            quantity1_limit = min(self.limits[base1]-self.cash[base1], 1.0/exchange1*(self.limits[quote1]+self.cash[quote1]), 1000)
            quantity2_limit = min(self.limits[base2]-self.cash[base2], 1.0/exchange2*(self.limits[quote2]+self.cash[quote2]), 1000)
            quantity3_limit = min(self.limits[base3]+self.cash[base3], 1.0/exchange3*(self.limits[quote3]-self.cash[quote3]), 1000)
            quantity1 = min(quantity1, quantity1_limit)
            quantity2 = min(quantity2, quantity2_limit)
            quantity3 = min(quantity3, quantity3_limit)
            quantity1 = min(quantity1, quantity3, quantity2/exchange1)
            quantity1 = int(-quantity1*multiplier)
            quantity2 = int(quantity1*exchange1)
            quantity3 = int(-quantity1)
        if abs(quantity1) < 10 or abs(quantity2) < 10 or abs(quantity3) < 10:
            quantity1 = 0
            quantity2 = 0
            quantity3 = 0
        return (quantity1, quantity2, quantity3)

    def arbitrage(self):
        orders = []
        order_quantities = [0]*8 # EURJPY/CHFJPY/USDCHF/EURCHF/EURCAD/EURUSD/USDJPY

        # EURUSD*USDCAD=EURCAD
        if self.bestBids[5]*self.bestBids[7] > self.bestAsks[4]:
            #print('arb1')
            (quantity1, quantity2, quantity3) = self.calculateQuantities(5, 7, 4, -1)
            #if 0.005*(abs(quantity1)+abs(quantity2)+abs(quantity3)) < 1.0*abs(quantity1)*(self.bestBids[5]*self.bestBids[7]-self.bestAsks[4])/self.bestBids[7]:
            if abs(order_quantities[5] + quantity1) >= 10 and abs(order_quantities[7] + quantity2) >= 10 and abs(order_quantities[4] + quantity3) >= 10:
                order_quantities[5] += quantity1
                order_quantities[7] += quantity2
                order_quantities[4] += quantity3
        if self.bestAsks[5]*self.bestAsks[7] < self.bestBids[4]:
            #print('arb2')
            (quantity1, quantity2, quantity3) = self.calculateQuantities(5, 7, 4, 1)
            #if 0.005*(abs(quantity1)+abs(quantity2)+abs(quantity3)) < 1.0*abs(quantity1)*(self.bestBids[4]-self.bestAsks[5]*self.bestAsks[7])/self.bestAsks[7]:
            if abs(order_quantities[5] + quantity1) >= 10 and abs(order_quantities[7] + quantity2) >= 10 and abs(order_quantities[4] + quantity3) >= 10:
                order_quantities[5] += quantity1
                order_quantities[7] += quantity2
                order_quantities[4] += quantity3
        # EURUSD*USDCHF = EURCHF
        if self.bestBids[5]*self.bestBids[2] > self.bestAsks[3]:
            #print('arb3')
            (quantity1, quantity2, quantity3) = self.calculateQuantities(5, 2, 3, -1)
            #if 0.005*(abs(quantity1)+abs(quantity2)+abs(quantity3)) < 1.0*abs(quantity1)*(self.bestBids[5]*self.bestBids[2]-self.bestAsks[3])/self.bestBids[2]:
            if abs(order_quantities[5] + quantity1) >= 10 and abs(order_quantities[2] + quantity2) >= 10 and abs(order_quantities[3] + quantity3) >= 10:
                order_quantities[5] += quantity1
                order_quantities[2] += quantity2
                order_quantities[3] += quantity3
        if self.bestAsks[5]*self.bestAsks[2] < self.bestBids[3]:
            #print('arb4')
            (quantity1, quantity2, quantity3) = self.calculateQuantities(5, 2, 3, 1)
            #if 0.005*(abs(quantity1)+abs(quantity2)+abs(quantity3)) < 1.0*abs(quantity1)*(self.bestBids[3]-self.bestAsks[5]*self.bestAsks[2])/self.bestAsks[2]:
            if abs(order_quantities[5] + quantity1) >= 10 and abs(order_quantities[2] + quantity2) >= 10 and abs(order_quantities[3] + quantity3) >= 10:
                order_quantities[5] += quantity1
                order_quantities[2] += quantity2
                order_quantities[3] += quantity3
        # EURUSD*USDJPY=EURJPY
        if self.bestBids[5]*self.bestBids[6] > self.bestAsks[0]:
            #print('arb5')
            (quantity1, quantity2, quantity3) = self.calculateQuantities(5, 6, 0, -1)
            #if 0.005*(abs(quantity1)+abs(quantity2)+abs(quantity3)) < 1.0*abs(quantity1)*(self.bestBids[5]*self.bestBids[6]-self.bestAsks[0])/self.bestBids[6]:
            if abs(order_quantities[5] + quantity1) >= 10 and abs(order_quantities[6] + quantity2) >= 10 and abs(order_quantities[0] + quantity3) >= 10:
                order_quantities[5] += quantity1
                order_quantities[6] += quantity2
                order_quantities[0] += quantity3
        if self.bestAsks[5]*self.bestAsks[6] < self.bestBids[0]:
            #print('arb6')
            (quantity1, quantity2, quantity3) = self.calculateQuantities(5, 6, 0, 1)
            #if 0.005*(abs(quantity1)+abs(quantity2)+abs(quantity3)) < 1.0*abs(quantity1)*(self.bestBids[0]-self.bestAsks[5]*self.bestAsks[6])/self.bestAsks[6]:
            if abs(order_quantities[5] + quantity1) >= 10 and abs(order_quantities[6] + quantity2) >= 10 and abs(order_quantities[0] + quantity3) >= 10:
                order_quantities[5] += quantity1
                order_quantities[6] += quantity2
                order_quantities[0] += quantity3
        # USDCHF*CHFJPY=USDJPY
        if self.bestBids[2]*self.bestBids[1] > self.bestAsks[6]:
            #print('arb7')
            (quantity1, quantity2, quantity3) = self.calculateQuantities(2, 1, 6, -1)
            #if 0.005*(abs(quantity1)+abs(quantity2)+abs(quantity3)) < 1.0*abs(quantity1)*(self.bestBids[2]*self.bestBids[1]-self.bestAsks[6])/self.bestBids[6]:
            if abs(order_quantities[2] + quantity1) >= 10 and abs(order_quantities[1] + quantity2) >= 10 and abs(order_quantities[6] + quantity3) >= 10:
                order_quantities[2] += quantity1
                order_quantities[1] += quantity2
                order_quantities[6] += quantity3
        if self.bestAsks[2]*self.bestAsks[1] < self.bestBids[6]:
            #print('arb8')
            (quantity1, quantity2, quantity3) = self.calculateQuantities(2, 1, 6, 1)
            #if 0.005*(abs(quantity1)+abs(quantity2)+abs(quantity3)) < 1.0*abs(quantity1)*(self.bestBids[6]-self.bestAsks[2]*self.bestAsks[1])/self.bestAsks[6]:
            if abs(order_quantities[2] + quantity1) >= 10 and abs(order_quantities[1] + quantity2) >= 10 and abs(order_quantities[6] + quantity3) >= 10:
                order_quantities[2] += quantity1
                order_quantities[1] += quantity2
                order_quantities[6] += quantity3
        # EURCHF*CHFJPY=EURJPY
        if self.bestBids[3]*self.bestBids[1] > self.bestAsks[0]:
            #print('arb9')
            (quantity1, quantity2, quantity3) = self.calculateQuantities(3, 1, 0, -1)
            #if 0.005*(abs(quantity1)+abs(quantity2)+abs(quantity3)) < 1.0*abs(quantity1)*(self.bestBids[3]*self.bestBids[1]-self.bestAsks[0])/self.bestBids[6]:
            if abs(order_quantities[3] + quantity1) >= 10 and abs(order_quantities[1] + quantity2) >= 10 and abs(order_quantities[0] + quantity3) >= 10:
                order_quantities[3] += quantity1
                order_quantities[1] += quantity2
                order_quantities[0] += quantity3
        if self.bestAsks[3]*self.bestAsks[1] < self.bestBids[0]:
            #print('arb10')
            (quantity1, quantity2, quantity3) = self.calculateQuantities(3, 1, 0, 1)
            #if 0.005*(abs(quantity1)+abs(quantity2)+abs(quantity3)) < 1.0*abs(quantity1)*(self.bestBids[0]-self.bestAsks[3]*self.bestAsks[1])/self.bestAsks[6]:
            if abs(order_quantities[3] + quantity1) >= 10 and abs(order_quantities[1] + quantity2) >= 10 and abs(order_quantities[0] + quantity3) >= 10:
                order_quantities[3] += quantity1
                order_quantities[1] += quantity2
                order_quantities[0] += quantity3

        for i in range(len(order_quantities)):
            if order_quantities[i]:
                    
                ticker = self.tickers[i]
                buy = order_quantities[i] > 0
                quantity = abs(order_quantities[i])
                orders.append({
                    'ticker': ticker,
                    'buy': buy,
                    'quantity': quantity,
                })
        # print('trade: ', order_quantities)
        # print('bids: ', self.bestBids)
        # print('asks: ', self.bestAsks)
        # print('quantitybid: ', self.bestQuantityBids)
        # print('quantityask: ', self.bestQuantityAsks)
        # if (datetime.datetime.now() - self.last_time) > datetime.timedelta(microseconds = 30)
        #     self.last_time = datetime.datetime.now()
        return orders

    def process(self, msg):
        orders = super(FXBot, self).process(msg)
        #print(orders)
        return orders

if __name__ == '__main__':
    bot = FXBot()
    print "options are", bot.options.data

    for t in bot.makeThreads():
        t.daemon = True
        t.start()

    while not bot.done:
        sleep(0.03)


