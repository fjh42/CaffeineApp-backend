import json
from flask import Flask, request
import datetime
import db

DB = db.DatabaseDriver()

app = Flask(__name__)

# testing push

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
    if body is None:
        return failure_response("Request body must be JSON", 400)
    
    name = body.get("name")
    image_url = body.get("image_url")
    category = body.get("category")
    caffeine_content_mg = body.get("caffeine_content_mg")
    
    if not name:
        return failure_response("Field 'name' is required", 400)
    if caffeine_content_mg is None:
        return failure_response("Field 'caffeine_content_mg' is required", 400)
    
    try:
        caffeine_content_mg = int(caffeine_content_mg)
        if caffeine_content_mg < 0:
            return failure_response("'caffeine_content_mg' must be non-negative", 400)
    except (TypeError, ValueError):
        return failure_response("'caffeine_content_mg' must be an integer", 400)
    
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
    existing = DB.get_beverage_by_id(bev_id)
    if not existing:
        return failure_response("Beverage not found", 404)
    
    body = request.get_json()
    if body is None:
        return failure_response("Request body must be JSON", 400)
    
    name = body.get("name")
    caffeine_content_mg = body.get("caffeine_content_mg")
    image_url = body.get("image_url")
    category = body.get("category")

    if not name:
        return failure_response("Field 'name' cannot be empty", 400)

    try:
        caffeine_content_mg = int(caffeine_content_mg)
        if caffeine_content_mg < 0:
            return failure_response("'caffeine_content_mg' must be non-negative", 400)
    except (TypeError, ValueError):
        return failure_response("'caffeine_content_mg' must be an integer", 400)
    
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
    if body is None:
        return failure_response("Request body must be JSON", 400)

    username = body.get("username")
    email = body.get("email")
    password_hash = body.get("password_hash")
    daily_caffeine_limit = body.get("daily_caffeine_limit")
    weight_lbs = body.get("weight_lbs", 160.0)
    
    missing = []
    if not username:
        missing.append("username")
    if not email:
        missing.append("email")
    if not password_hash:
        missing.append("password_hash")
    if daily_caffeine_limit is None:
        missing.append("daily_caffeine_limit")

    if missing:
        return failure_response(f"Missing required field(s): {', '.join(missing)}", 400)

    try:
        daily_caffeine_limit = int(daily_caffeine_limit)
        if daily_caffeine_limit <= 0:
            return failure_response("'daily_caffeine_limit' must be > 0", 400)
    except (TypeError, ValueError):
        return failure_response("'daily_caffeine_limit' must be an integer", 400)

    try:
        weight_lbs = float(weight_lbs)
        if weight_lbs <= 0:
            return failure_response("'weight_lbs' must be > 0", 400)
    except (TypeError, ValueError):
        return failure_response("'weight_lbs' must be a number", 400)
    
    user_id = DB.insert_user(username, email, password_hash, daily_caffeine_limit, weight_lbs)
    return success_response({"id": user_id}, 201)


# GET /users/<user_id>/consumption/today - Get caffeine consumed today
@app.route("/users/<int:user_id>/consumption/today", methods=["GET"])
def get_consumption_today(user_id):
    """Get caffeine consumption summary for today"""
    today = datetime.date.today().strftime("%Y-%m-%d")
    consumptions = DB.get_consumption_by_user_and_date(user_id, today)
    
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
    if body is None:
        return failure_response("Request body must be JSON", 400)
    
    user_id = body.get("user_id")
    beverage_id = body.get("beverage_id")
    serving_count = body.get("serving_count", 1)

    if user_id is None or beverage_id is None:
        return failure_response("'user_id' and 'beverage_id' are required", 400)
    
    try:
        user_id = int(user_id)
        beverage_id = int(beverage_id)
        serving_count = int(serving_count)
    except (TypeError, ValueError):
        return failure_response("'user_id', 'beverage_id', and 'serving_count' must be integers", 400)

    if serving_count <= 0:
        return failure_response("'serving_count' must be >= 1", 400)

    if not DB.get_user_by_id(user_id):
        return failure_response("User not found", 404)
    if not DB.get_beverage_by_id(beverage_id):
        return failure_response("Beverage not found", 404)
    
    consumption_id = DB.insert_consumption(user_id, beverage_id, serving_count)
    return success_response({"id": consumption_id}, 201)


# DELETE /users/<user_id> - Delete user account
@app.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    """Delete a user account and all associated data"""
    consumptions = DB.get_consumption_by_user_id(user_id)
    for consumption in consumptions:
        DB.delete_consumption_by_id(consumption["id"])
    
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
    if body is None:
        return failure_response("Request body must be JSON", 400)
    
    new_limit = body.get("daily_caffeine_limit")
    if new_limit is None:
        return failure_response("'daily_caffeine_limit' is required", 400)
    
    try:
        new_limit = int(new_limit)
        if new_limit <= 0:
            return failure_response("'daily_caffeine_limit' must be > 0", 400)
    except (TypeError, ValueError):
        return failure_response("'daily_caffeine_limit' must be an integer", 400)
    
    user = DB.get_user_by_id(user_id)
    if not user:
        return failure_response("User not found", 404)

    DB.update_user_by_id(user_id, user["username"], user["email"], user["password_hash"], new_limit, user["weight_lbs"])
    return success_response({"message": "Daily caffeine limit updated"})


# PUT /consumptions/<log_id> - Edit a consumption entry
@app.route("/consumptions/<int:log_id>", methods=["PUT"])
def update_consumption(log_id):
    """Edit an existing consumption log entry (serving count)"""
    body = request.get_json()
    if body is None:
        return failure_response("Request body must be JSON", 400)
    
    new_serving_count = body.get("serving_count")
    if new_serving_count is None:
        return failure_response("'serving_count' is required", 400)
    
    try:
        new_serving_count = int(new_serving_count)
        if new_serving_count <= 0:
            return failure_response("'serving_count' must be >= 1", 400)
    except (TypeError, ValueError):
        return failure_response("'serving_count' must be an integer", 400)
    
    consumption = None
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
        DB.delete_consumption_by_id(log_id)
        DB.insert_consumption(consumption["user_id"], consumption["beverage_id"], new_serving_count)
        return success_response({"message": "Consumption entry updated"})
    
    return failure_response("Consumption entry not found", 404)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)