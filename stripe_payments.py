# Stripe payment integration for the espionage game
# This module handles Stripe payment processing for diamond purchases
# Updated by Cascade to support both local development and Replit deployment
# Uses LOCAL_DOMAIN environment variable for local development fallback

import os
import stripe
from flask import Blueprint, request, redirect, url_for, flash, render_template
from flask_login import login_required, current_user
from models import User, UserProgress
from app import db

# Initialize Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

# Get domain for success/cancel URLs
# Support both Replit and local development environments
if os.environ.get('REPLIT_DEV_DOMAIN'):
    # Running on Replit
    YOUR_DOMAIN = os.environ.get('REPLIT_DEV_DOMAIN') if os.environ.get('REPLIT_DEPLOYMENT') != '1' else os.environ.get('REPLIT_DOMAINS').split(',')[0]
else:
    # Running locally - use LOCAL_DOMAIN from .env
    local_domain = os.environ.get("LOCAL_DOMAIN", "localhost:5000")
    YOUR_DOMAIN = f"http://{local_domain}"

payments = Blueprint("payments", __name__)

# Diamond packages for purchase
DIAMOND_PACKAGES = {
    'starter': {'diamonds': 100, 'price_cents': 299, 'name': '100 Diamonds - Starter Pack'},
    'premium': {'diamonds': 500, 'price_cents': 999, 'name': '500 Diamonds - Premium Pack'},
    'ultimate': {'diamonds': 1500, 'price_cents': 1999, 'name': '1500 Diamonds - Ultimate Pack'}
}

@payments.route('/buy-diamonds')
@login_required
def buy_diamonds():
    """Show diamond purchase options"""
    return render_template('buy_diamonds.html', packages=DIAMOND_PACKAGES)

@payments.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    """Create Stripe checkout session for diamond purchase"""
    try:
        package_id = request.form.get('package')
        if package_id not in DIAMOND_PACKAGES:
            flash('Invalid package selected.', 'error')
            return redirect(url_for('payments.buy_diamonds'))
        
        package = DIAMOND_PACKAGES[package_id]
        
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': package['name'],
                        'description': f"Get {package['diamonds']} diamonds for your espionage missions!"
                    },
                    'unit_amount': package['price_cents']
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f'https://{YOUR_DOMAIN}/payment-success?session_id={{CHECKOUT_SESSION_ID}}&package={package_id}',
            cancel_url=f'https://{YOUR_DOMAIN}/buy-diamonds',
            customer_email=current_user.email,
            metadata={
                'user_id': current_user.id,
                'package_id': package_id,
                'diamonds': package['diamonds']
            }
        )
        
        return redirect(checkout_session.url, code=303)
        
    except Exception as e:
        flash(f'Payment setup failed: {str(e)}', 'error')
        return redirect(url_for('payments.buy_diamonds'))

@payments.route('/payment-success')
@login_required
def payment_success():
    """Handle successful payment"""
    try:
        session_id = request.args.get('session_id')
        package_id = request.args.get('package')
        
        if not session_id or package_id not in DIAMOND_PACKAGES:
            flash('Invalid payment session.', 'error')
            return redirect(url_for('index'))
        
        # Retrieve the session from Stripe
        session = stripe.checkout.Session.retrieve(session_id)
        
        if session.payment_status == 'paid':
            package = DIAMOND_PACKAGES[package_id]
            
            # Add diamonds to user account
            current_user.diamonds += package['diamonds']
            current_user.is_premium = True  # Mark as premium user
            db.session.commit()
            
            flash(f'Payment successful! {package["diamonds"]} diamonds added to your account.', 'success')
        else:
            flash('Payment was not completed successfully.', 'error')
            
    except Exception as e:
        flash(f'Payment verification failed: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@payments.route('/premium-features')
@login_required
def premium_features():
    """Show premium features available to users"""
    return render_template('premium_features.html')