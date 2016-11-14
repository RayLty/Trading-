import numpy as np
import time
from base import *

class DataPoint():
    def __init__(self, source_name, t, data):
        self.source_name = source_name
        self.t = t
        # data is a list in order of TRA, DER, SA, TM, IT
        self.data = data

class NewsData():
    def __init__(self):
        # a list of DataPoint objects
        self.data_list = []

        self.calculated_vector = 0
        self.predicted_vector = 4

class PDBot(BaseBot):
    def __init__(self):
        super(PDBot, self).__init__()
        self.Buzzfeed_data = NewsData()
        self.Associated_data = NewsData()
        self.Seeking_data = NewsData()
        self.ETF_data = NewsData()
        self.estimations = [0, 0, 0, 0, 0]

        self.TRA_price = 0
        self.DER_price = 0
        self.SA_price = 0
        self.TM_price = 0
        self.IT_price = 0
        self.index_price = 0

        # change this to true on >1 rounds
        self.know_qs = False
        # this should be in order Buzzfeed, Associated, Seeking, ETF
        self.known_qs = [0.4, 0.8, 2.0, 4.0]
        # TODO: CHANGE THIS AFTER FIRST ROUND!!!

    def update_state(self, msg):
        
        if self.options.get('veITose'):
            # print(msg)
            pass

        message_type = msg.get('message_type')

        if message_type == 'ACK REGISTER':
            print('Registered:')
            print(msg)

        elif message_type == 'TRADER UPDATE':
            # print('Got positions')
            states = msg['trader_state']
            positions = states['positions']
            PNL = states['pnl']

            f = open('PNL', 'a')
            f.seek(0)
            f.write(str(PNL))

        elif message_type == 'MARKET UPDATE':
            market_state = msg['market_state']
            if market_state['ticker'] == 'TRA':
                self.TRA_price = market_state['last_price']
            elif market_state['ticker'] == 'DER':
                self.DER_price = market_state['last_price']
            elif market_state['ticker'] == 'SA':
                self.SA_price = market_state['last_price']
            elif market_state['ticker'] == 'TM':
                self.TM_price = market_state['last_price']
            elif market_state['ticker'] == 'IT':
                self.IT_price = market_state['last_price']

            index_price = self.TRA_price + self.DER_price + self.SA_price + self.TM_price + self.IT_price
            current_prices = 'current prices are: ' + ' TRA: ' + str(self.TRA_price) + ' DER: ' + str(self.DER_price) + ' SA: ' + str(self.SA_price) + ' TM: ' + str(self.TM_price) + ' IT: ' + str(self.IT_price) + ' IDX: ' + str(index_price)
            f = open('PRICES', 'a')
            f.seek(0)
            f.write(str(current_prices))

        elif message_type == 'NEWS':
            # print('News update')
            news = msg['news']
            body = news['body']
            list1 = body.split(';')
            estimation_list = []
            for parsed in list1:
                estimation_list.append(float(parsed.split(' ')[-1]))
            data_point = DataPoint(news['source'], news['time'], estimation_list)
            if news['source'] == 'Buzzfeed':
                self.Buzzfeed_data.data_list.append(data_point)
            elif news['source'] == 'The Associated Press':
                self.Associated_data.data_list.append(data_point)
            elif news['source'] == 'Seeking Alpha':
                self.Seeking_data.data_list.append(data_point)
            if news['source'] == '@ETFGodfather':
                self.ETF_data.data_list.append(data_point)

        elif message_type == 'TRADE':
            pass
        elif message_type == 'PING':
            pass
        else:
            pass
            # print('Other message:')
            # print(msg)
 
    def process(self, msg):
        super(PDBot, self).process(msg)

        #---------- FOR BUZZFEED --------------------
        Buzzfeed_weighted_means = [0, 0, 0, 0, 0]
        Associated_weighted_means = [0, 0, 0, 0, 0]
        Seeking_weighted_means = [0, 0, 0, 0, 0]
        ETF_weighted_means = [0, 0, 0, 0, 0]

        if len(self.Buzzfeed_data.data_list) > 0:
            # for each of the five tickers
            # Buzzfeed_weighted_means = [0, 0, 0, 0, 0]
            for i in range(5):
                # we could try square the weights here
                Buzzfeed_weighted_means[i] = np.average([data_point.data[i] for data_point in self.Buzzfeed_data.data_list],
                    weights = [np.square(1./(600. - data_point.t)) for data_point in self.Buzzfeed_data.data_list])
            Buzzfeed_Qs = []
            for i in range(len(self.Buzzfeed_data.data_list)):
                data = self.Buzzfeed_data.data_list[i].data
                sum = 0
                for j in range(5):
                    sum = sum + np.square(data[j] - Buzzfeed_weighted_means[j])
                sd = np.sqrt(sum/5.)
                q = (sd * 60.)/(600. - self.Buzzfeed_data.data_list[i].t)
                Buzzfeed_Qs.append(q)
            self.Buzzfeed_data.calculated_vector = np.average(Buzzfeed_Qs)

        #---------- FOR ASSOCIATED --------------------
        if len(self.Associated_data.data_list) > 0:
            # for each of the five tickers
            # Associated_weighted_means = [0, 0, 0, 0, 0]
            for i in range(5):
                # we could try square the weights here
                Associated_weighted_means[i] = np.average([data_point.data[i] for data_point in self.Associated_data.data_list],
                    weights = [np.square(1./(600. - data_point.t)) for data_point in self.Associated_data.data_list])
            Associated_Qs = []
            for i in range(len(self.Associated_data.data_list)):
                data = self.Associated_data.data_list[i].data
                sum = 0
                for j in range(5):
                    sum = sum + np.square(data[j] - Associated_weighted_means[j])
                sd = np.sqrt(sum/5.)
                q = (sd * 60.)/(600. - self.Associated_data.data_list[i].t)
                Associated_Qs.append(q)
            self.Associated_data.calculated_vector = np.average(Associated_Qs)

        #---------- FOR SEEKING --------------------
        if len(self.Seeking_data.data_list) > 0:
            # for each of the five tickers
            # Seeking_weighted_means = [0, 0, 0, 0, 0]
            for i in range(5):
                # we could try square the weights here
                Seeking_weighted_means[i] = np.average([data_point.data[i] for data_point in self.Seeking_data.data_list],
                    weights = [np.square(1./(600. - data_point.t)) for data_point in self.Seeking_data.data_list])
            Seeking_Qs = []
            for i in range(len(self.Seeking_data.data_list)):
                data = self.Seeking_data.data_list[i].data
                sum = 0
                for j in range(5):
                    sum = sum + np.square(data[j] - Seeking_weighted_means[j])
                sd = np.sqrt(sum/5.)
                q = (sd * 60.)/(600. - self.Seeking_data.data_list[i].t)
                Seeking_Qs.append(q)
            self.Seeking_data.calculated_vector = np.average(Seeking_Qs)

        #---------- FOR ETF --------------------
        if len(self.ETF_data.data_list) > 0:
            # for each of the five tickers
            # ETF_weighted_means = [0, 0, 0, 0, 0]
            for i in range(5):
                # we could try square the weights here
                ETF_weighted_means[i] = np.average([data_point.data[i] for data_point in self.ETF_data.data_list], 
                    weights = [np.square(1./(600. - data_point.t)) for data_point in self.ETF_data.data_list])
            ETF_Qs = []
            for i in range(len(self.ETF_data.data_list)):
                data = self.ETF_data.data_list[i].data
                sum = 0
                for j in range(5):
                    sum = sum + np.square(data[j] - ETF_weighted_means[j])
                sd = np.sqrt(sum/5.)
                q = (sd * 60.)/(600. - self.ETF_data.data_list[i].t)
                ETF_Qs.append(q)
            self.ETF_data.calculated_vector = np.average(ETF_Qs)

        if (self.Buzzfeed_data.calculated_vector != 0 or self.Associated_data.calculated_vector != 0 or self.Seeking_data.calculated_vector != 0 or self.ETF_data.calculated_vector != 0):
            actual_qs = [0.4, 0.8, 2.0, 4.0]
            difference = 999
            if not self.Buzzfeed_data.calculated_vector == 0:
                if len(self.Buzzfeed_data.data_list) <2: 
                    self.Buzzfeed_data.predicted_vector = 4.0
                else:
                    for q in actual_qs:
                        if np.absolute(self.Buzzfeed_data.calculated_vector - q) < difference:
                            difference = np.absolute(self.Buzzfeed_data.calculated_vector - q)
                            self.Buzzfeed_data.predicted_vector = q


            difference = 999
            if not self.Associated_data.calculated_vector == 0:
                if len(self.Associated_data.data_list) <2:
                    self.Associated_data.predicted_vector = 4.0
                else:
                    for q in actual_qs:
                        if np.absolute(self.Associated_data.calculated_vector - q) < difference:
                            difference = np.absolute(self.Associated_data.calculated_vector - q)
                            self.Associated_data.predicted_vector = q
            
            difference = 999
            if not self.Seeking_data.calculated_vector == 0:
                if len(self.Seeking_data.data_list) < 2:
                    self.Seeking_data.predicted_vector = 4.0
                else:
                    for q in actual_qs:
                        if np.absolute(self.Seeking_data.calculated_vector - q) < difference:
                            difference = np.absolute(self.Seeking_data.calculated_vector - q)
                            self.Seeking_data.predicted_vector = q
            
            difference = 999
            if not self.ETF_data.calculated_vector == 0:
                if len(self.ETF_data.data_list) < 2:
                    self.ETF_data.predicted_vector = 4.0
                else:
                    for q in actual_qs:
                        if np.absolute(self.ETF_data.calculated_vector - q) < difference:
                            difference = np.absolute(self.ETF_data.calculated_vector - q)
                            self.ETF_data.predicted_vector = q

            # REORDER THIS THING AND CHECK!!!!! DON'T FORGET!!!
            # import pdb; pdb.set_trace()
            # if len(self.Buzzfeed_data.data_list) >=1 and len(self.Associated_data.data_list) >=1 and len(self.Seeking_data.data_list) >= 1 and len(self.ETF_data.data_list) >=1:
                # import pdb; pdb.set_trace()
            if len(self.Buzzfeed_data.data_list) >=3 and len(self.Associated_data.data_list) >=3 and len(self.Seeking_data.data_list) >= 3 and len(self.ETF_data.data_list) >=3:
                calculated_qs = [self.Buzzfeed_data.calculated_vector, self.Associated_data.calculated_vector, self.Seeking_data.calculated_vector, self.ETF_data.calculated_vector]
                sorted_calculated = calculated_qs
                sorted_calculated.sort()
                if self.Buzzfeed_data.calculated_vector  == sorted_calculated[0]:
                    self.Buzzfeed_data.predicted_vector = 0.4
                elif self.Buzzfeed_data.calculated_vector  == sorted_calculated[1]:
                    self.Buzzfeed_data.predicted_vector = 0.8
                elif self.Buzzfeed_data.calculated_vector  == sorted_calculated[2]:
                    self.Buzzfeed_data.predicted_vector = 2.0
                elif self.Buzzfeed_data.calculated_vector  == sorted_calculated[3]:
                    self.Buzzfeed_data.predicted_vector = 4.0

                if self.Associated_data.calculated_vector  == sorted_calculated[0]:
                    self.Associated_data.predicted_vector = 0.4
                elif self.Associated_data.calculated_vector  == sorted_calculated[1]:
                    self.Associated_data.predicted_vector = 0.8
                elif self.Associated_data.calculated_vector  == sorted_calculated[2]:
                    self.Associated_data.predicted_vector = 2.0
                elif self.Associated_data.calculated_vector  == sorted_calculated[3]:
                    self.Associated_data.predicted_vector = 4.0
                
                if self.Seeking_data.calculated_vector  == sorted_calculated[0]:
                    self.Seeking_data.predicted_vector = 0.4
                elif self.Seeking_data.calculated_vector  == sorted_calculated[1]:
                    self.Seeking_data.predicted_vector = 0.8
                elif self.Seeking_data.calculated_vector  == sorted_calculated[2]:
                    self.Seeking_data.predicted_vector = 2.0
                elif self.Seeking_data.calculated_vector  == sorted_calculated[3]:
                    self.Seeking_data.predicted_vector = 4.0

                if self.ETF_data.calculated_vector  == sorted_calculated[0]:
                    self.ETF_data.predicted_vector = 0.4
                elif self.ETF_data.calculated_vector  == sorted_calculated[1]:
                    self.ETF_data.predicted_vector = 0.8
                elif self.ETF_data.calculated_vector  == sorted_calculated[2]:
                    self.ETF_data.predicted_vector = 2.0
                elif self.ETF_data.calculated_vector  == sorted_calculated[3]:
                    self.Associated_data.predicted_vector = 4.0

            if self.know_qs:
                self.Buzzfeed_data.predicted_vector = self.known_qs[0]
                self.Associated_data.predicted_vector = self.known_qs[1]
                self.Seeking_data.predicted_vector = self.known_qs[2]
                self.ETF_data.predicted_vector = self.known_qs[3]

            calculated_qs = [self.Buzzfeed_data.calculated_vector, self.Associated_data.calculated_vector, self.Seeking_data.calculated_vector, self.ETF_data.calculated_vector]
            predicted_qs = [self.Buzzfeed_data.predicted_vector, self.Associated_data.predicted_vector, self.Seeking_data.predicted_vector, self.ETF_data.predicted_vector]
            
            # import itertools
            # perms = list(itertools.permutations(calculated_qs))
            # least_error = 100
            # least_error_list = [0, 0, 0, 0]
            
            # for perm in perms:
            #     error = 0
            #     for j in range(4):
            #         error = error + np.square(actual_qs[j] - perm[j])
            #     if error < least_error:
            #         least_error = error
            #         least_error_list = perm

            # for i in range(len(least_error_list)):
            #     if least_error_list[i] == calculated_qs[0]:
            #         self.Buzzfeed_data.predicted_vector = actual_qs[i]
            #     elif least_error_list[i] == calculated_qs[1]:
            #         self.Associated_data.predicted_vector = actual_qs[i]
            #     elif least_error_list[i] == calculated_qs[2]:
            #         self.Seeking_data.predicted_vector = actual_qs[i]  
            #     elif least_error_list[i] == calculated_qs[3]:
            #         self.ETF_data.predicted_vector = actual_qs[i]
            
            # print('calculated Qs are: ', calculated_qs)

            # print('predicated Qs are: ', predicted_qs)


            # def func(x, sign = -1.0, self):
            #     Buzzfeed_vectors = [data_point.data for data_point in self.Buzzfeed_data.data_list]
            #     Buzzfeed_times = [data_point.time for data_point in self.Buzzfeed_data.data_list]
            #     Buzzfeed_q = self.Buzzfeed_data.predicted_vector
            #     Buzzfeed_sigmas = [Buzzfeed_q * (600. - t) / 60. for t in Buzzfeed_times]
            #     sum_Buzzfeed = 0
            #     for i in range(len(Buzzfeed_vectors)):
            #         c = (np.power(Buzzfeed_sigmas[i], -2.5))/(np.power(6.28318530718, 2.5))
            #         sum_Buzzfeed = sum_Buzzfeed + np.log(c) - (np.sum([np.square(Buzzfeed_vectors[i][j] - x[j]) for j in range(5)]))/Buzzfeed_sigmas[i]
                
            #     Associated_vectors = [data_point.data for data_point in self.Associated_data.data_list]
            #     Associated_times = [data_point.time for data_point in self.Associated_data.data_list]
            #     Associated_q = self.Associated_data.predicted_vector
            #     Associated_sigmas = [Associated_q * (600. - t) / 60. for t in Associated_times]
            #     sum_Associated = 0
            #     for i in range(len(Associated_vectors)):
            #         c = (np.power(Associated_sigmas[i], -2.5))/(np.power(6.28318530718, 2.5))
            #         sum_Associated = sum_Associated + np.log(c) - (np.sum([np.square(Associated_vectors[i][j] - x[j]) for j in range(5)]))/Associated_sigmas[i]

            #     Seeking_vectors = [data_point.data for data_point in self.Seeking_data.data_list]
            #     Seeking_times = [data_point.time for data_point in self.Seeking_data.data_list]
            #     Seeking_q = self.Seeking_data.predicted_vector
            #     Seeking_sigmas = [Seeking_q * (600. - t) / 60. for t in Seeking_times]
            #     sum_Seeking = 0
            #     for i in range(len(Seeking_vectors)):
            #         c = (np.power(Seeking_sigmas[i], -2.5))/(np.power(6.28318530718, 2.5))
            #         sum_Seeking = sum_Seeking + np.log(c) - (np.sum([np.square(Seeking_vectors[i][j] - x[j]) for j in range(5)]))/Seeking_sigmas[i]

            #     ETF_vectors = [data_point.data for data_point in self.ETF_data.data_list]
            #     ETF_times = [data_point.time for data_point in self.ETF_data.data_list]
            #     ETF_q = self.ETF_data.predicted_vector
            #     ETF_sigmas = [ETF_q * (600. - t) / 60. for t in ETF_times]
            #     sum_ETF = 0
            #     for i in range(len(ETF_vectors)):
            #         c = (np.power(ETF_sigmas[i], -2.5))/(np.power(6.28318530718, 2.5))
            #         sum_ETF = sum_ETF + np.log(c) - (np.sum([np.square(ETF_vectors[i][j] - x[j]) for j in range(5)]))/ETF_sigmas[i]

            #     return sign*(np.sum([sum_Buzzfeed, sum_Associated, sum_Seeking, sum_ETF]))
            
            # def func_deriv(x, sign = -1.0):
            #     Buzzfeed_vectors = [data_point.data for data_point in self.Buzzfeed_data.data_list]
            #     Buzzfeed_times = [data_point.time for data_point in self.Buzzfeed_data.data_list]
            #     Buzzfeed_q = self.Buzzfeed_data.predicted_vector
            #     Buzzfeed_sigmas = [Buzzfeed_q * (600. - t) / 60. for t in Buzzfeed_times]
            #     sum_Buzzfeed = [0, 0, 0, 0, 0]
            #     for i in range(len(Buzzfeed_vectors)):
            #         for j in range(5):
            #             sum_Buzzfeed[j] = sum_Buzzfeed[j] + (-2) * (1./Buzzfeed_sigmas[i]) * (Buzzfeed_vectors[i][j] - x[j])
                
            #     Associated_vectors = [data_point.data for data_point in self.Associated_data.data_list]
            #     Associated_times = [data_point.time for data_point in self.Associated_data.data_list]
            #     Associated_q = self.Associated_data.predicted_vector
            #     Associated_sigmas = [Associated_q * (600. - t) / 60. for t in Associated_times]
            #     sum_Associated = [0, 0, 0, 0, 0]
            #     for i in range(len(Associated_vectors)):
            #         for j in range(5):
            #             sum_Associated[j] = sum_Associated[j] + (-2) * (1./Associated_sigmas[i]) * (Associated_vectors[i][j] - x[j])
                
            #     Seeking_vectors = [data_point.data for data_point in self.Seeking_data.data_list]
            #     Seeking_times = [data_point.time for data_point in self.Seeking_data.data_list]
            #     Seeking_q = self.Seeking_data.predicted_vector
            #     Seeking_sigmas = [Seeking_q * (600. - t) / 60. for t in Seeking_times]
            #     sum_Seeking = [0, 0, 0, 0, 0]
            #     for i in range(len(Seeking_vectors)):
            #         for j in range(5):
            #             sum_Seeking[j] = sum_Seeking[j] + (-2) * (1./Seeking_sigmas[i]) * (Seeking_vectors[i][j] - x[j])
                
            #     ETF_vectors = [data_point.data for data_point in self.ETF_data.data_list]
            #     ETF_times = [data_point.time for data_point in self.ETF_data.data_list]
            #     ETF_q = self.ETF_data.predicted_vector
            #     ETF_sigmas = [ETF_q * (600. - t) / 60. for t in ETF_times]
            #     sum_ETF = [0, 0, 0, 0, 0]
            #     for i in range(len(ETF_vectors)):
            #         for j in range(5):
            #             sum_ETF[j] = sum_ETF[j] + (-2) * (1./ETF_sigmas[i]) * (ETF_vectors[i][j] - x[j])
                
            #     dfdx0 = sign * np.sum(sum_Buzzfeed[0], sum_Associated[0], sum_Seeking[0], sum_ETF[0])
            #     dfdx1 = sign * np.sum(sum_Buzzfeed[1], sum_Associated[1], sum_Seeking[1], sum_ETF[1])
            #     dfdx2 = sign * np.sum(sum_Buzzfeed[2], sum_Associated[2], sum_Seeking[2], sum_ETF[2])
            #     dfdx3 = sign * np.sum(sum_Buzzfeed[3], sum_Associated[3], sum_Seeking[3], sum_ETF[3])
            #     dfdx4 = sign * np.sum(sum_Buzzfeed[4], sum_Associated[4], sum_Seeking[4], sum_ETF[4])
                
            #     return np.array([dfdx0, dfdx1, dfdx2, dfdx3, dfdx4])
            

            init_list = [0, 0, 0, 0, 0]
            index_price = self.TRA_price + self.DER_price + self.SA_price + self.TM_price + self.IT_price
                
            for i in range(5):
                init_list[i] = np.average([Buzzfeed_weighted_means[i], Associated_weighted_means[i], Seeking_weighted_means[i], ETF_weighted_means[i]], weights = [np.square(1/self.Buzzfeed_data.predicted_vector), np.square(1/self.Associated_data.predicted_vector), np.square(1/self.Seeking_data.predicted_vector), np.square(1/self.ETF_data.predicted_vector)])
            if init_list != self.estimations or index_price != self.index_price:
                print('length of data: ', [len(self.Buzzfeed_data.data_list), len(self.Associated_data.data_list), len(self.Seeking_data.data_list), len(self.ETF_data.data_list)])
                print('calculated Qs are: ', calculated_qs)
                print('predicted Qs are: ', predicted_qs)
                print('price estimations are: ', ' TRA: ', round(init_list[0], 2), ' DER: ', round(init_list[1],2), ' SA: ', round(init_list[2],2), ' TM: ', round(init_list[3],2), ' IT: ', round(init_list[4],2), ' IDX: ', round(np.sum(init_list), 2))
                print('current prices are:    ', ' TRA: ', round(self.TRA_price, 2), ' DER: ', round(self.DER_price,2), ' SA: ', round(self.SA_price,2), ' TM: ', round(self.TM_price,2), ' IT: ', round(self.IT_price,2), ' IDX: ', round(index_price,2))
                print('-----------------------------------')
                self.estimations = init_list
                self.index_price = index_price

                # f = open('predicted_qs_doc', 'a')
                # f.seek(0)
                # f.write(str(', '.join(predicted_qs)))
            # res = sp.minimize(func, init_list, args = (-1.0), jac = func_deriv, method = 'SLSQP', options={'disp': True})
            # print('estimated true price: ', res)
        return None
 
if __name__ == '__main__':
    bot = PDBot()
    print "options are", bot.options.data
    for t in bot.makeThreads():
        t.daemon = True
        t.start()
    while not bot.done:
        sleep(0.01)