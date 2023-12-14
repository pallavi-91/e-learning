

# Create your tests here.
import requests

# Where USD is the base currency you want to use
url = 'https://v6.exchangerate-api.com/v6/e873d4874f975703942c3156/latest/USD'

# Making our request
response = requests.get(url)
import pdb
pdb.set_trace()
data = response.json()

# Your JSON object
print (data)