# Use a base image that includes Python and necessary dependencies
FROM python:3.10.6

# Create a group and user to avoid running as root
#RUN groupadd -r appgroup && useradd -r -g appgroup appuser
# Change to the new user
#USER appuser

# Set the working directory inside the container
WORKDIR /app

# Create additional folders in the container
RUN mkdir sonarftdata
RUN mkdir sonarftdata/history
RUN mkdir sonarftdata/bots
RUN mkdir sonarftdata/config

# Copy config files into the container
COPY sonarftdata/config/parameters.json /app/sonarftdata/config/parameters.json
COPY sonarftdata/config/indicators.json /app/sonarftdata/config/indicators.json

COPY sonarftdata/config.json /app/sonarftdata/config.json
COPY sonarftdata/config_markets.json /app/sonarftdata/config_markets.json
COPY sonarftdata/config_parameters.json /app/sonarftdata/config_parameters.json
COPY sonarftdata/config_exchanges.json /app/sonarftdata/config_exchanges.json
COPY sonarftdata/config_symbols.json /app/sonarftdata/config_symbols.json
COPY sonarftdata/config_fees.json /app/sonarftdata/config_fees.json

# Backend Bot Management
COPY sonarft.py /app/sonarft.py
COPY sonarft_server.py /app/sonarft_server.py
COPY sonarft_manager.py /app/sonarft_manager.py

# Bot software
COPY sonarft_bot.py /app/sonarft_bot.py
COPY sonarft_api_manager.py /app/sonarft_api_manager.py
COPY sonarft_helpers.py /app/sonarft_helpers.py
COPY sonarft_math.py /app/sonarft_math.py
COPY sonarft_prices.py /app/sonarft_prices.py
COPY sonarft_validators.py /app/sonarft_validators.py
COPY sonarft_indicators.py /app/sonarft_indicators.py
COPY sonarft_search.py /app/sonarft_search.py
COPY sonarft_execution.py /app/sonarft_execution.py

COPY .env /app/.env

COPY requirements.txt /app/requirements.txt    
RUN pip install -r requirements.txt

EXPOSE 5000

# Define the command to run the application
CMD [ "python3", "sonarft.py" ]
