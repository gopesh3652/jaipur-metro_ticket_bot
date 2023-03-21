import os
import random
import time
import asyncio
import qrcode
from twilio.rest import Client
from flask import Flask, request, send_file
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

@app.route("/sms", methods=['POST'])
def receive_sms():
    incoming_message = request.values.get('Body', '')
    # Process the incoming message and generate a response
    response_message = process_message(incoming_message)
    # Create a TwiML response object
    twilio_response = MessagingResponse()
    twilio_response.message(response_message)
    # Send the response back to the user
    return str(twilio_response)


app = Flask(__name__)

METRO_BASE_FARE = 10  # INR
METRO_PER_KM_FARE = 5  # INR
METRO_KM_LIMIT = 3
TWILIO_ACCOUNT_SID = os.environ.get('ACd6cb501bcbc6ea27e033bfbe04b9f56b')
TWILIO_AUTH_TOKEN = os.environ.get('82e0b8d5e88f8cf908d3a84978e044f5')
TWILIO_PHONE_NUMBER = os.environ.get('+15076186951')

fare_cache = {}

def calculate_fare(start_station, end_station):
    # Check if the fare is already cached
    key = f'{start_station}-{end_station}'
    if key in fare_cache:
        return fare_cache[key]

    # Calculate the distance between the stations
    distance = abs(end_station - start_station)

    # Calculate the fare
    if distance <= METRO_KM_LIMIT:
        fare = METRO_BASE_FARE
    else:
        fare = METRO_BASE_FARE + METRO_PER_KM_FARE * (distance - METRO_KM_LIMIT)

    # Cache the fare calculation result
    fare_cache[key] = fare

    return fare

async def generate_qr_code(fare, code):
    data = f'Fare: {fare} INR\nCode: {code}'
    img = qrcode.make(data)
    filename = f'{code}.png'
    img.save(filename)
    return filename

@app.route('/ticket', methods=['POST'])
async def generate_ticket():
    try:
        start_station = int(request.form.get['start_station'])
        end_station = int(request.form.get['end_station'])
        phone_number = request.form.get['phone_number']
    except:
        return 'Invalid parameters', 400

    # Calculate the fare
    fare = calculate_fare(start_station, end_station)

    # Generate a random code for the ticket
    code = ''.join(random.choices('0123456789abcdef', k=10))

    # Generate the QR code
    filename = await generate_qr_code(fare, code)

    # Send the QR code image to the user
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    message = client.messages.create(
        to=phone_number,
        from_=TWILIO_PHONE_NUMBER,
        media_url=[f'https://{request.host}/{filename}']
    )

    # Remove the QR code image file
    os.remove(filename)

    # Return the fare and code
    return f'Fare: {fare} INR\nCode: {code}'

@app.route('/image/<filename>')
def get_image(filename):
    return send_file(filename, mimetype='image/png')

if __name__ == '__main__':
    app.run()