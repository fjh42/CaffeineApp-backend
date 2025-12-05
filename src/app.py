import json
from flask import Flask, request
import datetime
import db

DB = db.DatabaseDriver()

app = Flask(__name__)

def success_response(data,status_code=200):
    """
    Standardized success response
    """
    return json.dumps(data), status_code

def failure_response(description,status_code=500):
    """
    Standardized failure response
    """
    return json.dumps({"error":description}),status_code

@app.before_first_request
def initialize_database():
    """
    Initialize the database by creating the necessary tables.
    """
    DB.create_users_table()
    DB.create_beverages_table()
    DB.create_consumption_log_table()

@app.route("/")
def hello_world():
    return "Hello world!"


# ==================== ADMIN ONLY ROUTES ====================

# GET /users - Returns all users in the system
@app.route("/users", methods=["GET"])
def get_all_users():
    """Admin endpoint to retrieve all users"""
    users = DB.get_all_users()
    return success_response(users)


# GET /consumption - Returns all consumption logs
@app.route("/consumption", methods=["GET"])
def get_all_consumption():
    """Admin endpoint to retrieve all consumption logs"""
    # Get all users and compile their consumption logs
    users = DB.get_all_users()
    all_consumptions = []
    for user in users:
        consumptions = DB.get_consumption_by_user_id(user["id"])
        all_consumptions.extend(consumptions)
    return success_response(all_consumptions)


# POST /beverages - Create a new beverage
@app.route("/beverages", methods=["POST"])
def create_beverage():
    """Admin endpoint to create a new beverage"""
    body = request.get_json()
    name = body.get("name")
    caffeine_content_mg = body.get("caffeine_content_mg")
    image_url = body.get("image_url")
    category = body.get("category")
    
    beverage_id = DB.insert_beverage(name, caffeine_content_mg, image_url, category)
    return success_response({"id": beverage_id}, 201)


# DELETE /beverages/<bev_id> - Delete a beverage
@app.route("/beverages/<int:bev_id>", methods=["DELETE"])
def delete_beverage(bev_id):
    """Admin endpoint to delete a beverage"""
    DB.delete_beverage_by_id(bev_id)
    return success_response({"message": "Beverage deleted"})


# PUT /beverages/<bev_id> - Update a beverage
@app.route("/beverages/<int:bev_id>", methods=["PUT"])
def update_beverage(bev_id):
    """Admin endpoint to update beverage details"""
    body = request.get_json()
    name = body.get("name")
    caffeine_content_mg = body.get("caffeine_content_mg")
    image_url = body.get("image_url")
    category = body.get("category")
    
    DB.update_beverage_by_id(bev_id, name, caffeine_content_mg, image_url, category)
    return success_response({"message": "Beverage updated"})


# ==================== ADMIN AND USER FRIENDLY ROUTES ====================

# GET /beverages - Returns all available beverages
@app.route("/beverages", methods=["GET"])
def get_beverages():
    """Public endpoint to retrieve all available beverages"""
    beverages = DB.get_all_beverages()
    return success_response(beverages)


# POST /users - Create a new user account
@app.route("/users", methods=["POST"])
def create_user():
    """Create a new user account"""
    body = request.get_json()
    username = body.get("username")
    email = body.get("email")
    password_hash = body.get("password_hash")
    daily_caffeine_limit = body.get("daily_caffeine_limit")
    weight_lbs = body.get("weight_lbs", 160.0)
    
    user_id = DB.insert_user(username, email, password_hash, daily_caffeine_limit, weight_lbs)
    return success_response({"id": user_id}, 201)


# GET /users/<user_id>/consumption/today - Get caffeine consumed today
@app.route("/users/<int:user_id>/consumption/today", methods=["GET"])
def get_consumption_today(user_id):
    """Get caffeine consumption summary for today"""
    today = datetime.date.today().strftime("%Y-%m-%d")
    consumptions = DB.get_consumption_by_user_and_date(user_id, today)
    
    # Calculate total caffeine and breakdown
    total_caffeine = 0
    breakdown = []
    for consumption in consumptions:
        beverage = DB.get_beverage_by_id(consumption["beverage_id"])
        caffeine_amount = beverage["caffeine_content_mg"] * consumption["serving_count"]
        total_caffeine += caffeine_amount
        breakdown.append({
            "beverage": beverage["name"],
            "servings": consumption["serving_count"],
            "caffeine_mg": caffeine_amount
        })
    
    return success_response({
        "date": today,
        "total_caffeine_mg": total_caffeine,
        "breakdown": breakdown
    })


# GET /users/<user_id>/consumption/weekly - Get weekly consumption summary
@app.route("/users/<int:user_id>/consumption/weekly", methods=["GET"])
def get_consumption_weekly(user_id):
    """Get day-by-day caffeine consumption summary for the past 7 days"""
    weekly_summary = {}
    
    # Iterate through the past 7 days
    for i in range(7):
        date = (datetime.date.today() - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
        consumptions = DB.get_consumption_by_user_and_date(user_id, date)
        
        total_caffeine = 0
        for consumption in consumptions:
            beverage = DB.get_beverage_by_id(consumption["beverage_id"])
            total_caffeine += beverage["caffeine_content_mg"] * consumption["serving_count"]
        
        weekly_summary[date] = total_caffeine
    
    return success_response(weekly_summary)


# GET /users/<user_id>/stats - Get user stats
@app.route("/users/<int:user_id>/stats", methods=["GET"])
def get_user_stats(user_id):
    """Get user's caffeine stats including daily total, limit, and percentage"""
    user = DB.get_user_by_id(user_id)
    today = datetime.date.today().strftime("%Y-%m-%d")
    consumptions = DB.get_consumption_by_user_and_date(user_id, today)
    
    # Calculate total caffeine consumed today
    total_caffeine = 0
    for consumption in consumptions:
        beverage = DB.get_beverage_by_id(consumption["beverage_id"])
        total_caffeine += beverage["caffeine_content_mg"] * consumption["serving_count"]
    
    daily_limit = user["daily_caffeine_limit"]
    percentage = (total_caffeine / daily_limit * 100) if daily_limit > 0 else 0
    
    return success_response({
        "user_id": user_id,
        "daily_total_caffeine_mg": total_caffeine,
        "daily_limit_mg": daily_limit,
        "percentage_of_limit": round(percentage, 2),
        "remaining_mg": max(0, daily_limit - total_caffeine)
    })


# POST /consumptions - Log a beverage consumption
@app.route("/consumptions", methods=["POST"])
def log_consumption():
    """Log a new beverage consumption"""
    body = request.get_json()
    user_id = body.get("user_id")
    beverage_id = body.get("beverage_id")
    serving_count = body.get("serving_count", 1)
    
    consumption_id = DB.insert_consumption(user_id, beverage_id, serving_count)
    return success_response({"id": consumption_id}, 201)


# DELETE /users/<user_id> - Delete user account
@app.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    """Delete a user account and all associated data"""
    # Delete all consumption logs for this user
    consumptions = DB.get_consumption_by_user_id(user_id)
    for consumption in consumptions:
        DB.delete_consumption_by_id(consumption["id"])
    
    # Delete the user
    DB.delete_user_by_id(user_id)
    return success_response({"message": "User account deleted"})


# DELETE /consumptions/<log_id> - Delete a consumption entry
@app.route("/consumptions/<int:log_id>", methods=["DELETE"])
def delete_consumption(log_id):
    """Remove a consumption log entry"""
    DB.delete_consumption_by_id(log_id)
    return success_response({"message": "Consumption entry deleted"})


# PUT /users/<user_id>/limit - Update daily caffeine limit
@app.route("/users/<int:user_id>/limit", methods=["PUT"])
def update_caffeine_limit(user_id):
    """Update a user's daily caffeine limit"""
    body = request.get_json()
    new_limit = body.get("daily_caffeine_limit")
    
    user = DB.get_user_by_id(user_id)
    DB.update_user_by_id(user_id, user["username"], user["email"], user["password_hash"], new_limit, user["weight_lbs"])
    return success_response({"message": "Daily caffeine limit updated"})


# PUT /consumptions/<log_id> - Edit a consumption entry
@app.route("/consumptions/<int:log_id>", methods=["PUT"])
def update_consumption(log_id):
    """Edit an existing consumption log entry (serving count)"""
    body = request.get_json()
    new_serving_count = body.get("serving_count")
    
    # Get consumption details to update
    consumptions = DB.get_consumption_by_user_id(0)  # Temporary approach
    consumption = None
    
    # Find the consumption entry with matching ID
    all_users = DB.get_all_users()
    for user in all_users:
        user_consumptions = DB.get_consumption_by_user_id(user["id"])
        for c in user_consumptions:
            if c["id"] == log_id:
                consumption = c
                break
        if consumption:
            break
    
    if consumption:
        beverage = DB.get_beverage_by_id(consumption["beverage_id"])
        DB.delete_consumption_by_id(log_id)
        DB.insert_consumption(consumption["user_id"], consumption["beverage_id"], new_serving_count)
        return success_response({"message": "Consumption entry updated"})
    
    return failure_response("Consumption entry not found", 404)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
    initialize_database()