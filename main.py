#
#This program is to calculate the risk behind a mortgage rate based on payment and max payment
#
import sys

import csv

import numpy as np

import random

import matplotlib.pyplot as plt

HOME_PRICE = 600000
INTEREST_RATE = 4
TERM_LENGTH = 5 #RENEWS EVERY 5 YEARS
DOWN_PAYMENT = 0
LOAN_LENGTH = 30
MAX_MONTHLY_PAYMENT = 4500#maximum affordable monthly payment


#This function will load the historical interest rates
def load_historical():

	filename = "historical.csv"

	file_obj = open(filename, "r")

	csv_reader = csv.reader(file_obj)

	data = []

	for row in csv_reader:

		data.append(row)

	#from here we have all the data
	#date, interest rate

	data = data[1:]

	#now lets turn everything into numbers

	for each_point in range(len(data)):

		for i in range(2):

			data[each_point][i] = float(data[each_point][i])

	return data

#Helper function to get the average movement of interest rates
def get_average(data):

	#create some arrays to store the data

	up_diffs = []
	down_diffs = []
	same_diffs = []
	diffs = []

	for each_points in range(1, len(data)):

		temp_diff = data[each_points][1] - data[each_points-1][1]

		#from here determine what happened

		if temp_diff > 0:

			up_diffs.append(temp_diff)

		elif temp_diff < 0:

			down_diffs.append(temp_diff)
		else:

			same_diffs.append(temp_diff)

		diffs.append(temp_diff)

	up_diffs = np.array(up_diffs)
	down_diffs = np.array(down_diffs)
	same_diffs = np.array(same_diffs)
	diffs = np.array(diffs)

	#from here we want to get the statistics and return them in a package

	stats = {
		"up":[np.average(up_diffs), np.median(up_diffs), np.min(up_diffs), np.max(up_diffs), len(up_diffs)],
		"down":[np.average(down_diffs), np.median(down_diffs), np.min(down_diffs), np.max(down_diffs), len(down_diffs)],
		"total":[np.average(diffs), np.median(diffs), np.min(diffs), np.max(diffs), len(diffs)]

	}

	#each of these arrays will contain the average, median, min, and max

	return stats


#Function that will calculate the monthly payment
def calculate_monthly_payment(home_price, interest_rate, loan_length, down_payment):

	loan_amount = home_price-down_payment

	numerator = -1 * loan_amount  * (1+interest_rate/12)**loan_length * interest_rate

	denominator = (1-(1+interest_rate/12)**loan_length) * 12

	return round(numerator/denominator, 2)

#Function to run a simulation
def simulate_interest_rate_movement(starting_rate, time_left, stats, n = 10):

	simulation_results = [] #this will contain an array of interest rates at each month

	pct_up = stats["up"][4] / stats["total"][4]

	pct_down = stats["down"][4] / stats["total"][4]

	pct_same = 1-pct_up-pct_down

	real_weights = [pct_down, pct_same, pct_up]

	trial_weights = [0.45, 0.1, 0.45]

	for _ in range(n):

		temp_data = [starting_rate/100] #this will hold the values it has held

		temp_interest_rate = starting_rate

		for i in range(time_left):

			movement = random.choices([-1, 0, 1], weights=trial_weights, k=1)[0]

			if movement == 1: #moved up

				temp_interest_rate += stats["up"][1]

			elif movement == -1: #moved down

				temp_interest_rate = max(0, temp_interest_rate+stats["down"][1])

			#otherwise the interest stays the same

			temp_data.append(temp_interest_rate/100)

		#now from here we append the temp data to the simulation results

		simulation_results.append(temp_data)



	return simulation_results

#Function that evaluates risk with a random walk
def evaluate_risk(home_price, interest_rate, loan_length, down_payment, term_length, max_monthly_payment, interest_rate_scenarios):

	#we have to run a bunch of simulations

	#first get currently monthly payment

	data = []

	current_monthly = calculate_monthly_payment(home_price, interest_rate, loan_length, down_payment)

	curr_paid_off = current_monthly * term_length

	new_balance = (home_price - down_payment)*(1+interest_rate/12)**term_length - curr_paid_off #this gives us the remaining balance on the loan

	time_left = loan_length - term_length #this gives us the current time because
	#we assume the random walk begins at the end of the fixed interest rate period

	total_exceeded = 0

	for each_case in interest_rate_scenarios:

		#basically we want to check with this interest rate movement
		#does the monthly payment exceed it at anytime

		#from here we iterate through the points where the payment changes (every term length)

		temp_monthly_payments = [[current_monthly, interest_rate, (home_price-down_payment)]]

		remaining_adjustments =int(( loan_length-term_length) / term_length)

		temp_new_balance = new_balance

		temp_time_left = time_left

		for each_adj in range(remaining_adjustments):

			#from here we need to define which index we are getting the interest from

			rate_index = term_length *(each_adj+1)

			temp_rate = each_case[rate_index]



			#now we have a rate

			temp_payment = calculate_monthly_payment(temp_new_balance, temp_rate, temp_time_left, 0) #zero becayse no more downpaymnet

			temp_monthly_payments.append([float(temp_payment), float(temp_rate), float(temp_new_balance)])

			temp_paid_off = temp_payment * term_length

			temp_new_balance = temp_new_balance*(1+temp_rate/12)**term_length - temp_paid_off

			temp_time_left -= term_length

		#now from here append the monthly payments made to the data
		data.append(temp_monthly_payments)

	#from here we have our data and want to go through and see wwhat pct have monthly
	scenarios_exceeded = 0
	months_exceeded = 0
	total_scenarios = len(data)
	total_months = total_scenarios * (len(data[0])-1)

	for each_case in data:

		temp_months_exceeded = 0


		for each_term in range(1, len(each_case)):

			if each_case[each_term][0] > max_monthly_payment:

				temp_months_exceeded += 1

		months_exceeded += temp_months_exceeded

		if temp_months_exceeded > 0:

			scenarios_exceeded += 1



	return round(scenarios_exceeded/total_scenarios, 4), round(months_exceeded/total_months, 4)



def main():



	historical_data = load_historical()

	stats = get_average(historical_data)


	#from here we have everything and now want input from the user

	home_price = float(input("Home Price ($): "))
			
	interest_rate = float(input("Interest Rate (%): "))/100

	loan_length = int(input("Loan Length (Years): "))*12

	term_length = int(input("Fixed Rate Term (years): "))*12

	down_payment = float(input("Down Payment ($): "))

	max_monthly_payment = float(input("Maximum Allowable Monthly Payment ($): "))

	"""home_price = HOME_PRICE
	interest_rate = INTEREST_RATE/100
	term_length = TERM_LENGTH*12 #in years
	down_payment = DOWN_PAYMENT
	loan_length= LOAN_LENGTH*12
	max_monthly_payment = MAX_MONTHLY_PAYMENT"""



	interest_rate_scenarios = simulate_interest_rate_movement(interest_rate*100, loan_length, stats, n=25000)
	
	#from here we want to call a function that will go through each case and figure out how many of them exceed the max monthly payment


	monthly_payment_scenarios = evaluate_risk(home_price, interest_rate, loan_length, down_payment, term_length, max_monthly_payment, interest_rate_scenarios)

	print(f"% Chance of Monthly Payments Exceeding Max: {round(100*monthly_payment_scenarios[0], 2)}")
	print(f"% of Simulated Months where Payments Exceed Max: {100*monthly_payment_scenarios[1]}")

	


	return

if __name__ == "__main__":

	main()