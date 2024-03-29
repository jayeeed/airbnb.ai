from flask import request, jsonify, make_response, Blueprint
from pymongo import MongoClient
from sklearn.impute import SimpleImputer
from sklearn.neighbors import NearestNeighbors
from models.price_model import X_test_scaled,HistGradientBoostingRegressor_model,google_locations,property_df
import numpy as np
from textblob import TextBlob
from flask_cors import CORS

price_predict_routes = Blueprint('price_predict_routes', __name__)

# CORS(search_properties_route, resources={r"/api/recommended/*": {"origins": "http://localhost:3009"}})

@price_predict_routes.route('/price', methods=['POST', 'OPTIONS'])
def handle_price_options():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        # response.headers.add("Access-Control-Allow-Origin", "http://localhost:3003")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "OPTIONS, POST")
        return response

    elif request.method == 'POST':
        responseData = request.json
        data = responseData.get('values', {})
        print("Received data:", data)

        placeDescribesId = data.get('placeDescibe')
        typeOfPlaceId = data.get('typeOfPlace')
        located = data.get('locatedPlace', {})
        address = data.get('addAddress', {})
        guests = data.get('guests', {})
        amenitiesIds = data.get('offer', [])
        images = data.get('uploadPhoto', [])
        title = data.get('shortTitle')

        suggested_price = get_pred(X_test_scaled)
        print("suggested_price", suggested_price)
        nearest_price = get_nearest(located)
        print("nearest_price", nearest_price)
        print("placeDescribesId", placeDescribesId)
        print("typeOfPlaceId", typeOfPlaceId)
        print("address", address)
        print("title", title)

    if title and placeDescribesId and typeOfPlaceId and located and address and guests and amenitiesIds and images and request.method == 'POST':
        id = MongoClient.db.prediction.insert_one({
            "shortTitle": title, "placeDescibe": placeDescribesId, "typeOfPlace": typeOfPlaceId,
            "locatedPlace": located, "addAddress": address, "guests": guests, "offer": amenitiesIds, "uploadPhoto": images,
            "suggested_price": suggested_price,
            "nearest_price": nearest_price
        })

        resp = jsonify({'message': 'Suggested price successfully created!',
                       "suggested_price": suggested_price, "nearest_price": nearest_price})
        resp.status_code = 201  # Created status code
        return resp

    else:
        resp = jsonify({'error': 'Invalid data or missing values'})
        resp.status_code = 400  # Bad Request status code
        return resp

def get_pred(X_test_scaled):
    suggested_price = HistGradientBoostingRegressor_model.predict(X_test_scaled)[0]
    formatted_price = round(np.exp(suggested_price), 2)
    return formatted_price

def get_nearest(located):
    latitude = located.get('lat')
    longitude = located.get('lon')
    if latitude is not None and longitude is not None:
        latitude = float(latitude)
        longitude = float(longitude)
        location_data = np.array([[latitude, longitude]])
        print(location_data)
        imputer = SimpleImputer(strategy='median')
        location_data = imputer.fit_transform(location_data)
        k = 3
        nn_model = NearestNeighbors(n_neighbors=k)
        nn_model.fit(google_locations)
        neighbors_indices = nn_model.kneighbors(
            location_data, n_neighbors=k, return_distance=False)
        print(neighbors_indices)
        avg_neighbor_price = round(
            property_df.loc[neighbors_indices[0], "price"].mean(), 2)
        return avg_neighbor_price
    else:
        # Handle the case where 'lat' or 'lon' are None
        return None







# @cross_origin(origin="localhost", headers=["Content-Type", "authorization"])
@price_predict_routes.route('/description', methods=['POST', 'OPTIONS'])
def handle_description_options():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        # response.headers.add("Access-Control-Allow-Origin", "http://localhost:3003")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "OPTIONS, POST")
        return response

    elif request.method == 'POST':

        data = request.json
        print("Received data:", data)
        description = data.get('text')

        sentiment = get_predict(description)
        print(sentiment)
        print("description", description)
        emotion = get_emotion_from_text(description)
        print(emotion)

    if description and request.method == 'POST':
        id = MongoClient.db.description.insert_one({
            "description": description,
            "sentiment": sentiment,
            "emotion": emotion
        })
        resp = jsonify({'message': 'Emotion and sentiment successfully created!',
                       "sentiment": sentiment, "emotion": emotion})
        resp.status_code = 201  # Created status code
        return resp

    else:
        resp = jsonify({'error': 'Invalid data or missing values'})
        resp.status_code = 400  # Bad Request status code
        return resp


def get_predict(description):
    if description is not None and isinstance(description, str):
        sentiment_polarity = TextBlob(description).sentiment.polarity

        # Classify the sentiment based on the sentiment score
        if sentiment_polarity >= 0.05:
            return 'positive'
        elif sentiment_polarity <= -0.05:
            return 'negative'
        else:
            return 'neutral'


def get_emotion_from_text(description):
    if description is not None and isinstance(description, str):
        blob = TextBlob(description)
        polarity = blob.sentiment.polarity
        if "fear" in description.lower() or "anxious" in description.lower() or "nervous" in description.lower():
            return "fear"
        elif "surprised" in description.lower() or "shocked" in description.lower() or "amazed" in description.lower():
            return "surprise"
        elif polarity > 0.2:
            return "happiness"
        elif polarity < -0.2:
            return "sadness"
        elif polarity < 0 and polarity >= -0.2:
            return "anger"
        else:
            return "neutral"
    else:
        return 'neutral'
