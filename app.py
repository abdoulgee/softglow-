import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from datetime import timedelta
from products import PRODUCTS
from dotenv import load_dotenv
from datetime import datetime
import requests

load_dotenv()



def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev_secret_key_change_me")
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)
    app.config["DELIVERY_FEE"] = 5.00
    app.config["CURRENCY"] = "usd"
    # Load your LIVE PayPal credentials
    PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID", "YAZQ9qF7TIIm94-CLgZHWwo5SzKSriFVsj1pT4jN9c1hZ6kVXhusiQwLbas7fSRXARhsBJka4J5mK00oi")
    PAYPAL_SECRET = os.getenv("PAYPAL_SECRET", "YEB-d7StEQM99EhEZOdZzxPyzK1g9HdSawMRI4HXA5jlglS9iLSs31zF4xYOwxmxFtg2N-poDdVM39KWA")
    PAYPAL_API_BASE = "https://api-m.paypal.com"   # sandbox: https://api-m.sandbox.paypal.com
    
    def get_paypal_access_token():
        """Get OAuth access token from PayPal"""
        auth = (PAYPAL_CLIENT_ID, PAYPAL_SECRET)
        headers = {"Accept": "application/json", "Accept-Language": "en_US"}
        data = {"grant_type": "client_credentials"}
        r = requests.post(f"{PAYPAL_API_BASE}/v1/oauth2/token", auth=auth, data=data, headers=headers)
        r.raise_for_status()
        return r.json()["access_token"]
    @app.route("/paypal-success", methods=["POST"])
    def paypal_success():
        data = request.get_json()
        order_id = data.get("orderID")

        # Step 1: Get PayPal token
        token = get_paypal_access_token()
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}

        # Step 2: Verify order from PayPal
        r = request.get(f"{PAYPAL_API_BASE}/v2/checkout/orders/{order_id}", headers=headers)
        order_data = r.json()

        if order_data.get("status") == "COMPLETED":
            payer = order_data.get("payer", {})
            purchase_units = order_data.get("purchase_units", [])

            # ✅ Handle order storage/email/DB updates here
            #print(f"✅ PayPal Order Verified: {order_id}, Payer: {payer}")

            # ✅ Log to console and append to file
            log_message = f"✅ PayPal Order Verified: {order_id}, Payer: {payer}"
            print(log_message)
        
        # Append to log file
            with open("paypal_orders.txt", "a") as file:
                file.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {log_message}\n")

            # Clear cart after successful payment
            session["cart"] = {}
            session.modified = True

            return jsonify({"status": "success", "orderID": order_id})
        else:
            # Log failed attempts
            with open("paypal_orders.txt", "a") as file:
                file.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - ❌ Failed Order: {order_id}\n")
            return jsonify({"status": "failed", "orderID": order_id}), 400


    def get_cart_items():
        cart = session.get("cart", {})
        items = []
        for pid, qty in cart.items():
            product = next((p for p in PRODUCTS if p["id"] == int(pid)), None)
            if product:
                items.append({
                    "id": product["id"],
                    "name": product["name"],
                    "price": product["price"],
                    "qty": qty,
                    "subtotal": round(product["price"] * qty, 2),
                    "image": product["images"][0]
                })
        return items

    @app.context_processor
    def inject_globals():
        return {
            "DELIVERY_FEE": app.config["DELIVERY_FEE"]
        }

    @app.before_request
    def make_session_permanent():
        session.permanent = True

    @app.route("/")
    def home():
        return render_template("home.html", products=PRODUCTS)

    @app.route("/shop")
    def shop():
        return render_template("shop.html", products=PRODUCTS)

    @app.route("/product/<int:pid>")
    def product_detail(pid):
        product = next((p for p in PRODUCTS if p["id"] == pid), None)
        if not product:
            return redirect(url_for("shop"))
        return render_template("product_detail.html", product=product)

    @app.route("/add-to-cart", methods=["POST"])
    def add_to_cart():
        pid = int(request.form.get("product_id"))
        qty = max(1, int(request.form.get("quantity", 1)))
        product = next((p for p in PRODUCTS if p["id"] == pid), None)
        if not product:
            flash("Product not found.", "error")
            return redirect(url_for("shop"))
        
        if "cart" not in session:
            session["cart"] = {}
            
        cart = session["cart"]
        cart[str(pid)] = cart.get(str(pid), 0) + qty
        session["cart"] = cart
        session.modified = True   
        
        flash("Added to cart.", "success")
        return redirect(url_for("checkout"))

    @app.route("/cart/update", methods=["POST"])
    def cart_update():
        if "cart" not in session:
            session["cart"] = {}
            
        cart = session["cart"]
        for key, value in request.form.items():
            if key.startswith("qty_"):
                pid = key.split("_",1)[1]
                try:
                    q = int(value)
                    if q <= 0:
                        cart.pop(pid, None)
                    else:
                        cart[pid] = q
                except ValueError:
                    pass
        session["cart"] = cart
        session.modified = True   
        flash("Cart updated.", "success")
        return redirect(url_for("checkout"))

    @app.route("/checkout", methods=["GET", "POST"])
    def checkout():
        if "cart" not in session:
            session["cart"] = {}
            
        items = get_cart_items()
        subtotal = round(sum(i["subtotal"] for i in items), 2)
        delivery = app.config["DELIVERY_FEE"] if items else 0
        total = round(subtotal + delivery, 2)

        if request.method == "POST":
            name = request.form.get("name")
            email = request.form.get("email")
            address = request.form.get("address")
            city = request.form.get("city")
            country = request.form.get("country")
            phone = request.form.get("phone")

            session["customer"] = {
                "name": name, "email": email, "address": address,
                "city": city, "country": country, "phone": phone
            }

            # ✅ Redirect user to thank you after PayPal completes (PayPal JS handles payment)
            return redirect(url_for("thankyou_contact"))

        return render_template("checkout.html",
                               items=items, subtotal=subtotal,
                               delivery=delivery, total=total)

    @app.route("/thank-you", methods=["GET", "POST"])
    def thankyou_contact():
        customer = session.get("customer", {})
        submitted = False
        if request.method == "POST":
            submitted = True
        session["cart"] = {}
        session.modified = True
        return render_template("thankyou_contact.html", customer=customer, submitted=submitted)

    @app.route("/api/cart")
    def api_cart():
        if "cart" not in session:
            session["cart"] = {}
        return jsonify(session.get("cart", {}))
    
    

    @app.route("/test-session")
    def test_session():
        if "test" not in session:
            session["test"] = 0
        session["test"] += 1
        session.modified = True
        return f"Session test value: {session['test']}"

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5001)
