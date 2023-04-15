##################################################
# Mandatory variables
##################################################
# Time interval between data source API requests
# It has to be a number and it will be interpreted as seconds
DATA_SOURCE_REQUESTS_RATE = 60 * 1


##################################################
# Optional variables
##################################################
# Max allowed oldness of prices from data souce API.
# An int will be interpreted as seconds and None will be interpreted as no oldness limit
MAX_OLDNESS_PRICE = None # int or None
