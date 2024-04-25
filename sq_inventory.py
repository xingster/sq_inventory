import tabula
import csv
import re
import sqlite3
from sqlite3 import Error
from square.client import Client
import os
import json
from datetime import datetime,timezone
import uuid
from thefuzz import fuzz

print("Is the vendor psg, rocket, or rudy?")
vendor = input(">")
print("What's the filename?")
file = input(">")

if file == "":
	print("Defaulting...")
	if vendor == "psg":
		file = "bloomsgiving-psg.pdf"
	elif vendor == "rudy":
		file = "bloomsgiving-rudy.pdf"
	elif vendor == "rocket":
		file = "bloomsgiving-rocket.pdf"
	else:
		quit()

df = tabula.read_pdf(file, pages="all", stream=True, guess=False)
print(df)

df[0].to_csv('bg.csv')
for d in df[1:]:
	d.to_csv('bg.csv',mode='a')	

class product:
	def __init__(self, size, name, price, qty, cost = "$0.00"):
		self.size = size
		self.name = name
		self.price = price
		self.qty = qty
		self.cost = cost
		self.sq_variation_id = ""

def create_connection(path):
	connection = None
	try:
		connection = sqlite3.connect(path)
		print("Database connection successful")
	except Error as e:
		print(f"The error '{e}' occured")
	return connection

def select_first_relationship(conn, vendor, v_item_name):
	cur = conn.cursor()
	cur.execute("Select * from vendor_square_product_relationship where vendor=? and vendor_item_name=?", (vendor, v_item_name))
	row = cur.fetchone()
	return row
		

def search_square_items(name):
	#check if name has db mapping first
	row = select_first_relationship(db_connection, vendor, name)
	if row != None:
		item.name = row[2]
		name = row[2]
	
	result = client.catalog.search_catalog_items(
		body = {
			"text_filter": name,
			"category_ids": ["HXPFFG2KCC4DAN4FVRXULYAL"
			]	
		}
	)
	if result.is_success():
		#print(result.body["items"])
		return result.body
	elif result.is_error():
		print(result.errors)

items = []

db_connection = create_connection("bloomsgiving.sqlite")

def read_psg():
	with open('bg.csv', newline='') as csvfile:
		spamreader = csv.reader(csvfile, delimiter=' ', quotechar='|')
		for lines in spamreader:
			if "QTY" in lines[0]:
				break	
		for lines in spamreader:
			if "TOTAL" in lines[1] or "AMOUNT" in lines[1]:
				break
			col = re.findall(r'\d+', lines[0].split(',')[1])[0]
			qty = col
			size = re.findall(r'\d+', lines[2])[0] + '"'
			name = ""
			cost = "$0.00"
			for word in lines[3:]:
				tmp = word.split(',')
				for t in tmp:
					if t == "":
						name = name.replace("\"","")	
						break
					t=t.replace("-","")
					name = name + " " + t
				for t in tmp:
					if "$" in t and cost == "$0.00":
						cost = t

			price = "$0.00"
			items.append(product(size, name, price, qty, cost))
	
	with open (vendor + "-out.csv",'w',newline='') as file:
		writer = csv.writer(file)
		for item in items:
			row = item.qty, item.size, item.name
			print(item.qty + " " + item.size + " " + item.name + " " + item.cost)
			writer.writerow(row)

def read_rudy():
	with open('bg.csv', newline='') as csvfile:
		spamreader = csv.reader(csvfile, delimiter=' ', quotechar='|')
		for lines in spamreader:
			if "Quantity" in lines[0]:
				break
		for lines in spamreader:
			if bool(re.search(r'\d', lines[1])):
				if "Page" in lines[0]:
					continue
				if "Tel" in lines[0]:
					break
				col = re.findall(r'\d+', lines[0].split(',')[1])[0]
				qty = col
				size = re.findall(r'\d+', lines[1])[0] + '"'
				if "GAL".lower() in lines[2].lower():
					gal_size = int(re.findall(r'\d+', lines[1])[0])
					if gal_size == 1: 
						size = "8\""
					elif gal_size == 2:
						size = "10\""	
				name = ""
				cost = "$0.00"
				for word in lines[2:]:
					i = 0
					tmp = word.split(',')
					for t in tmp:

						if "gal" in t.lower():
							continue
						if bool(re.search(r'\d', t)):
							name = name.replace("\"","")
							break
						t=t.replace("-","")
						name = name + " " + t
						i = i+1

					for t in tmp[i:]:
						if re.findall(r'\d+', t) and cost == "$0.00":
							cost = "$" + t.replace("\"","")
				price = "$0.00"
				items.append(product(size, name, price, qty, cost))
	with open (vendor + "-out.csv",'w',newline='') as file:
		writer = csv.writer(file)
		for item in items:
			row = item.qty, item.size, item.name
			print(item.qty + " " + item.size + " " + item.name + " " + item.cost)
			writer.writerow(row)

def read_rocket():
	with open('bg.csv', newline='') as csvfile:
		spamreader = csv.reader(csvfile, delimiter=' ', quotechar='|')
		stop = 0
		for lines in spamreader:
			for line in lines:
				if "Quantity" in line:
					stop=1
					break
			if (stop == 1):
				break

		for lines in spamreader:
			if "Sub" in lines[0]:
					break
			if bool(re.search(r'\d', lines[1])):
				size = re.findall(r'\d+', lines[1].split(',')[1])[0] + "\""

				if lines[2] != "in":
					continue

				name = ""
				for word in lines[3:]:
					i = 0
					tmp = word.split(',')
					for t in tmp:
						if bool(re.search(r'\d', t)):
							name = name.replace("\"","")
							break
						t=t.replace("-","")
						name = name + " " + t
						i = i+1
				cost = "$0.00"
				for word in lines[i:]:
					tmp = word.split(',')
					for t in tmp:
						if bool(re.search(r'\d', t)):
							qty = tmp[0]
							if re.findall(r'\d+', t) and cost == "$0.00":
								cost = "$" + t.replace("\"","")
				price = "$0.00"
				items.append(product(size, name, price, qty, cost))
	with open (vendor + "-out.csv",'w',newline='') as file:
		writer = csv.writer(file)
		for item in items:
			row = item.qty, item.size, item.name
			print(item.qty + " " + item.size + " " + item.name + " " + item.cost)
			writer.writerow(row)

if vendor=='psg':
	read_psg()
elif vendor=='rudy':
	read_rudy()
elif vendor=='rocket':
    read_rocket()

#search for items on square

client = Client(
    #access_token=os.environ['SQUARE_ACCESS_TOKEN'],
	access_token = "EAAAF67iPFG15e3rIRZ7_PM_X736ao0HjNuekYatK53KCtObPIp-99xMPYtSRzA3",
	environment = "production")

i=0
def find_item_in_result(result,name):
	r = None
	if 'items' not in result:
		print("Sorry we couldn't find it")
		return r
		
	for r in result["items"]:
		square_item_name = r["item_data"]["name"].lower()
		str = "Is " + square_item_name + " the right one?"
		print(str)
		confirm = input(">")
		if confirm == "yes" or confirm == "y":
			return r
	r = None
	print("Sorry we couldn't find it")
	return r

def add_item_mapping_db(conn, vendor, vendor_item_name, sq_item_name):
	rel = (vendor, vendor_item_name, sq_item_name)
	sql = ''' INSERT INTO vendor_square_product_relationship(vendor, vendor_item_name, sq_item_name)
		VALUES(?,?,?) '''
	cur = conn.cursor()
	cur.execute(sql, rel)
	conn.commit()
	return cur.lastrowid
		
def get_variation_from_size(size):
	print("Adding variation from size")
	result = client.catalog.retrieve_catalog_object(
		object_id = "MR2EOU2GZYLFDP3KCLXJY2YY",
		include_related_objects = False
	)

	if result.is_success():
		print(result.body)
		variations = result.body["object"]["item_option_data"]["values"]
		for v in variations:
			if size == v["item_option_value_data"]["name"]:
				print("using option Plant Size: " + size)
				return v["id"]
		print("Plant Option doesn't include size: " + size + ". Please add this in Square and try again.")
		quit()
	elif result.is_error():
		print(result.errors)
		print("would you like to retry?")
		retry = input(">")


def add_variation_with_item(result, item, variation_id):
	key = uuid.uuid1()
	price = int(round(float(item.price.strip('$'))*100))
	variations = []
	original_result = result
	variations = result["item_data"]["variations"]
	v = {
		"type": "ITEM_VARIATION",
		"id": "#1",
		"is_deleted": False,
		"present_at_all_locations": True,
		"item_variation_data": {
			"name": item.size,
			"pricing_type": "FIXED_PRICING",
			"price_money": {
				"amount": price,
				"currency": "USD"
			},
			"track_inventory": True,
			"item_option_values": [
				{
					"item_option_id": "MR2EOU2GZYLFDP3KCLXJY2YY",
					"item_option_value_id": variation_id
				}
            ],
			"sellable": True,
			"stockable": True
		}
	}

	variations.append(v)
	result["item_data"]["variations"] = variations
	result = client.catalog.batch_upsert_catalog_objects(
		body = {
			"idempotency_key": str(key),
			"batches": [
				{
					"objects": [
						result
					]
				}
			]
		}
	)

	if result.is_success():
		return item.price
	elif result.is_error():
		print("======== ERROR ========")
		print(result.errors)
		print("Would you like to retry?")
		retry = input(">")
		if retry == "yes" or retry == "y":
			result = original_result
			return update_square_with_size_price(result, item)

def create_item_with_item():
	print(item.size + " " + item.name + " costs " + item.cost + ". What should I set the price as?")
	price = input(">")
	m = re.match(r"^(\$[0-9]+\.[0-9]+)", price)
	while m is None:
		print("Price should be in format $xx.xx.")
		price = input(">")
		m = re.match(r"^(\$[0-9]\.[0-9]+)", price)
		if m != None:
			break
	item.price = price

	#update square with new variation and price
	variation_id = get_variation_from_size(item.size)
	#send to square
	
	key = uuid.uuid1()
	price = int(round(float(item.price.strip('$'))*100))

	result = client.catalog.batch_upsert_catalog_objects(
		body = {
			"idempotency_key": str(key),
			"batches": [
				{
					"objects": [
						{
							"type": "ITEM",
							"id": "#1",
							"present_at_all_locations": True,
							"item_data": {
								"name": item.name,
								"category_id": "HXPFFG2KCC4DAN4FVRXULYAL",
								"tax_ids": [
									"CNKHC7BOXITX6LEBLNBB2KOE"
								],
								"variations": [
									{
										"type": "ITEM_VARIATION",
										"id": "#2",
										"is_deleted": False,
										"present_at_all_locations": True,
										"item_variation_data": {
											"name": item.size,
											"pricing_type": "FIXED_PRICING",
											"price_money": {
											  "amount": price,
											  "currency": "USD"
											},
											"track_inventory": True,
											"item_option_values": [
												{
													"item_option_id": "MR2EOU2GZYLFDP3KCLXJY2YY",
													"item_option_value_id": variation_id
												}
											],
											"sellable": True,
											"stockable": True
										}
									}
								],
								"product_type": "REGULAR",
								"item_options": [
									{
										"item_option_id": "MR2EOU2GZYLFDP3KCLXJY2YY"
									}
								]
							}
						}
					]
				}
			]
		}
	)

	if result.is_success():
		item.sq_variation_id = result.body["objects"][0]["item_data"]["variations"][0]["id"]
		print("Successfully created a new item in square")
	elif result.is_error():
		print(result.errors)


def update_square_with_size_price(result, item):
	print(item.size + " " + item.name + " costs " + item.cost + ". What should I set the price as?")
	price = input(">")
	m = re.match(r"^(\$[0-9]+\.[0-9]+)", price)
	while m is None:
		print("Price should be in format $xx.xx.")
		price = input(">")
		m = re.match(r"^(\$[0-9]\.[0-9]+)", price)
	item.price = price

	#update square with new variation and price
	variation_id = get_variation_from_size(item.size)
	#send to square
	return add_variation_with_item(result, item, variation_id)

def find_price_by_item_size_in_result(result, size, item):
	r = result
	variations = r["item_data"]["variations"]
	for variation in variations:
		sq_size = variation["item_variation_data"]["name"]
		if len(re.findall(r'\d+', sq_size)) > 0:
			sq_size = re.findall(r'\d+', sq_size)[0] + "\""
		else: 
			print(sq_size)
			continue
		if sq_size == size:
			price = "${:,.2f}".format(variation["item_variation_data"]["price_money"]["amount"]/100)
			item.sq_variation_id = variation["id"]
			print("Price: " + price + "\n")
			return price
	print("couldn't find " + item.name + " in size: " + size + " size in square: " + sq_size)
	return update_square_with_size_price(result, item)

def search_by_plant_name():
	print("We couldn't find " + item.name + ". Try searching by plant name and check Square item options. Press s to skip or q to quit c to create a new item")
	search_name = input(">")
	while True:
		if search_name == "s":
			for item_r in items:
				if item_r.name == item.name:
					items.remove(item_r)
			break
		if search_name == "q":
			quit()	
		if search_name == "c":
			print("What's the name of the item?")
			square_name = input(">")
			add_item_mapping_db(db_connection, vendor, item.name, square_name)
			item.name = square_name
			create_item_with_item()
			print("Creating label price: " + item.price)
			break
		manual_search_r = search_square_items(search_name)
		found = find_item_in_result(manual_search_r, search_name)
		if found != None:
			print("Adding the mapping to the database...")
			add_item_mapping_db(db_connection, vendor, item.name, found["item_data"]["name"])
			item.price = find_price_by_item_size_in_result(manual_search_r["items"][0], item.size, item)
			print("Creating label price from square: " + item.price)
			break
		else:
			print("What's the item name? Press q to quit or c to create a new item")
			search_name = input(">")
	return item

retry = False
for item in items:
	result = search_square_items(item.name)
	print("Searching for " + item.size + " " + item.name + "...")
	if 'items' not in result:
		search_by_plant_name()
		continue
	if len(result["items"]) > 1:
		print("There's more than one item found for \"" + item.name + "\".")
		found_exact_match = 0
		i = 0
		for r in result["items"]:
			print(r["item_data"]["name"])
			#check for exact match
			if item.name.lower() == r["item_data"]["name"].lower():
				found_exact_match = i+1
				break
			i = i+1

		# confirm = "no"
		# print("")
		if found_exact_match != 0:
			# print("Is " + item.name + " the right one? ")
			# confirm = input(">")
			# if confirm == "yes" or confirm == "y":
			item.price = find_price_by_item_size_in_result(result["items"][found_exact_match-1],item.size,item)
			print("Creating label price from square: " + item.price + " for " + item.size + " " + item.name)

		if found_exact_match == 0:
			print("Which one is the right one? 'None' or 'n' to search manually.")
			new_name = input(">")

			if new_name.lower() == "n" or new_name.lower() == "None":
				search_by_plant_name()
			else: 
				for r in result["items"]:
					if new_name.lower() == r["item_data"]["name"].lower():
						print("Adding mapping to database")
						add_item_mapping_db(db_connection, vendor, item.name,r["item_data"]["name"])
						item.price = find_price_by_item_size_in_result(r, item.size, item)
						print("Creating label price from square: " + item.price)

				
	elif len(result["items"]) == 1:
		score = fuzz.ratio(result["items"][0]["item_data"]["name"].lower(), item.name.lower())
		if score < 95:
			print("Looking for " + item.name + ". Is " + result["items"][0]["item_data"]["name"] + " the right one? Score: " + str(score))
			confirm_item = input(">")
			if confirm_item == 'yes' or confirm_item =='y':
				add_item_mapping_db(db_connection, vendor, item.name,result["items"][0]["item_data"]["name"].lower())
				item.price = find_price_by_item_size_in_result(result["items"][0],item.size,item) 
				print("Creating label price from square: " + item.price)
			else:
				search_by_plant_name()
		else:
			item.price = find_price_by_item_size_in_result(result["items"][0],item.size,item) 
			print("Creating label price from square: " + item.price)
	
with open (vendor + '-' + datetime.today().strftime('%Y-%m-%d') + '.csv','w',newline='') as file:
	writer = csv.writer(file)
	for item in items:
		for i in range(int(item.qty)):
			row = item.size, item.name, item.price
			writer.writerow(row)

#update inventory
print("do you want to update the inventory?")
confirm_update = input(">")

print("Update inventory for Redwood City or Mountain View?")
location_name = input(">")

location = {'Redwood City': "LTKB7T5RDYT28",'Mountain View': "LJWTYFX51ATH9"}

def get_inventory_by_id(ids):
	result = client.inventory.batch_retrieve_inventory_counts(
		body = {
  			"catalog_object_ids":ids,
			"location_ids":[location[location_name]],
			"states": ["IN_STOCK"]
		}
	)

	if result.is_success():
		return result.body["counts"]
	elif result.is_error():
		print(result.errors)
	

def batch_send_update_request(items):
	key = uuid.uuid1()

	n = datetime.now(timezone.utc)
	occurred_at = n.isoformat()

	changes = []
	
	print("adjustment")
	for item in items:
		c = {}
		c["type"] = "ADJUSTMENT"
		adjustment = {
			"from_state": "NONE",
			"to_state": "IN_STOCK",
			"location_id": location[location_name],
			"catalog_object_id": item.sq_variation_id,
			"quantity": item.qty,
			"occurred_at": occurred_at
		}
		print(item.sq_variation_id + " " + item.qty)
		if(item.sq_variation_id == ""):
			continue
		else:
			c["adjustment"] = adjustment
			changes.append(c)
	
	result = client.inventory.batch_change_inventory(
		body = {
			"idempotency_key": str(key),
			"changes": changes,
    			"ignore_unchanged_counts": True
		}
	)

	if result.is_success():
		print("DONE")
	elif result.is_error():
  		print(result.errors)


def batch_update_quantity(inventory):
	for i in inventory:
		variation_id = i["catalog_object_id"] 
		quantity = int(i["quantity"])
		if quantity < 0:
			for item in items:
				if item.sq_variation_id == variation_id:
					item.qty = str(int(item.qty) + -1*quantity)
	batch_send_update_request(items)
	

if confirm_update == "yes" or confirm_update == "y":
	variation_ids = []
	for item in items:	
		variation_ids.append(item.sq_variation_id)
		print(item.sq_variation_id)
	print(variation_ids)	
	inventory = get_inventory_by_id(variation_ids)
	print("Old inventory counts")
	print("==========================")
	for i in inventory:
		print(i["catalog_object_id"] + " " + i["quantity"])

	batch_update_quantity(inventory)

	print("New inventory counts")
	print("==========================")
	inventory = get_inventory_by_id(variation_ids)
	for i in inventory:
		print(i["catalog_object_id"] + " " + i["quantity"])
	
