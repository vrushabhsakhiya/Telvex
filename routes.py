from flask import render_template, request, redirect, url_for, flash, jsonify, make_response
from models import db, Customer, Category, Measurement, Order, ShopProfile, mail, Reminder
from werkzeug.utils import secure_filename
import os
import random
import string
from datetime import datetime, timedelta
from flask_mail import Message
import hmac
import hashlib
from flask_login import login_user, logout_user, login_required, current_user
from models import User
from app import limiter

# OTP Helper
def send_otp_email(user):
    otp = ''.join(random.choices(string.digits, k=6))
    user.otp_code = otp
    # OTP Valid for 10 minutes
    user.otp_expiry = datetime.utcnow() + timedelta(minutes=10)
    db.session.commit()
    
    # FOR LOCAL TESTING: Print OTP to Console + Flash to Screen
    print(f"\n{'='*20}\n OTP GENERATED: {otp} \n{'='*20}\n")
    try:
        from flask import current_app
        if current_app.debug: # Only show in debug/local mode
             flash(f'DEV MODE: Your OTP is {otp}', 'info')
    except:
        pass 
    
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Mail Error (OTP not sent via email): {e}")


def register_routes(app):
    
    # Context Processor to inject shop settings globally
    @app.context_processor
    def inject_defaults():
        try:
            if current_user.is_authenticated:
                 # Access via relationship or query
                 shop = ShopProfile.query.filter_by(user_id=current_user.id).first()
                 return dict(active_page='', shop=shop)
            return dict(active_page='', shop=None)
        except Exception as e:
            print(f"!!! ERROR IN INJECT_DEFAULTS: {e}")
            return dict(active_page='', shop=None)

    from app import limiter 

    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))

    # --- Authentication Routes ---

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
            
        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            confirm = request.form.get('confirm_password')
            
            if password != confirm:
                flash('Passwords do not match.', 'error')
                return redirect(url_for('register'))
            
            if User.query.filter_by(email=email).first():
                flash('Email already registered.', 'error')
                return redirect(url_for('register'))
                
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            
            # Send OTP
            send_otp_email(new_user)
            
            # Store ID in session temporarily for OTP verify
            from flask import session
            session['auth_user_id'] = new_user.id
            
            flash('Account created! Please verify your email.', 'success')
            return redirect(url_for('verify_otp'))
            
        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    @limiter.limit("5 per minute") 
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
            
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            
            user = User.query.filter_by(email=email).first()
            
            # Check Lockout
            if user and user.locked_until:
                if user.locked_until > datetime.utcnow():
                    # Still locked
                    wait_seconds = (user.locked_until - datetime.utcnow()).seconds
                    hours = wait_seconds // 3600
                    mins = (wait_seconds % 3600) // 60
                    flash(f'Account locked due to too many failed attempts. Try again in {hours}h {mins}m.', 'danger')
                    return redirect(url_for('login'))
                else:
                    # Lock expired
                    user.locked_until = None
                    user.failed_attempts = 0
                    db.session.commit()

            if user and user.check_password(password):
                # Success
                user.failed_attempts = 0
                db.session.commit()
                
                # Generate OTP for 2FA
                send_otp_email(user)
                
                from flask import session
                session['auth_user_id'] = user.id
                session['remember_me'] = True # Assume true or add checkbox
                
                return redirect(url_for('verify_otp'))
            else:
                # Failure
                if user:
                    user.failed_attempts = (user.failed_attempts or 0) + 1
                    if user.failed_attempts >= 5:
                        user.locked_until = datetime.utcnow() + timedelta(hours=4)
                        flash('Too many failed attempts. Account locked for 4 hours.', 'danger')
                    else:
                        flash('Invalid email or password.', 'error')
                    db.session.commit()
                else:
                     flash('Invalid email or password.', 'error')
                
        return render_template('login.html')

    @app.route('/verify-otp', methods=['GET', 'POST'])
    def verify_otp():
        from flask import session
        user_id = session.get('auth_user_id')
        if not user_id:
            return redirect(url_for('login'))
            
        user = User.query.get(user_id)
        if not user:
            return redirect(url_for('login'))
            
        if request.method == 'POST':
            otp = request.form.get('otp')
            
            if user.otp_code == otp and user.otp_expiry > datetime.utcnow():
                # Success
                user.otp_code = None
                user.otp_expiry = None
                user.is_verified = True
                db.session.commit()
                
                # Login proper
                login_user(user, remember=session.get('remember_me', False))
                session.pop('auth_user_id', None)
                session.pop('remember_me', None)
                
                flash(f'Welcome back, {user.username}!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid or expired OTP.', 'error')
                
        return render_template('otp_verify.html')

    @app.route('/resend-otp')
    def resend_otp():
        from flask import session
        user_id = session.get('auth_user_id')
        if user_id:
            user = User.query.get(user_id)
            if user:
                send_otp_email(user)
                flash('New code sent.', 'info')
                return redirect(url_for('verify_otp'))
        return redirect(url_for('login'))

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('login'))

    @app.route('/forgot-password', methods=['GET', 'POST'])
    def forgot_password():
        if request.method == 'POST':
            email = request.form.get('email')
            user = User.query.filter_by(email=email).first()
            if user:
                send_otp_email(user)
                from flask import session
                session['reset_user_id'] = user.id
                flash('Reset code sent to your email.', 'info')
                return redirect(url_for('reset_password'))
            else:
                flash('Email not found.', 'error')
        return render_template('forgot_password.html')

    @app.route('/reset-password', methods=['GET', 'POST'])
    def reset_password():
        from flask import session
        user_id = session.get('reset_user_id')
        if not user_id:
            return redirect(url_for('forgot_password'))
            
        if request.method == 'POST':
            otp = request.form.get('otp')
            password = request.form.get('password')
            confirm = request.form.get('confirm_password')
            
            user = User.query.get(user_id)
            if user and user.otp_code == otp and user.otp_expiry > datetime.utcnow():
                if password == confirm:
                    user.set_password(password)
                    user.otp_code = None
                    db.session.commit()
                    session.pop('reset_user_id', None)
                    flash('Password reset successfully. Please login.', 'success')
                    return redirect(url_for('login'))
                else:
                    flash('Passwords do not match.', 'error')
            else:
                flash('Invalid or expired OTP.', 'error')
                
        return render_template('reset_password.html')


    # --- Protected Routes ---
    


    @app.route('/settings', methods=['GET', 'POST'])
    @login_required
    def settings():
        staff_members = []
        shop = ShopProfile.query.filter_by(user_id=current_user.id).first()
        if not shop:
             shop = ShopProfile(user_id=current_user.id) # Create generic if missing
             db.session.add(shop)
             db.session.commit()
              
        # Categories are now handled in custom_categories, but if needed here:
        # categories = Category.query.all() 
        
        return render_template('settings.html', active_page='settings', staff_members=staff_members, shop=shop)


    @app.route('/settings/update_profile', methods=['POST'])
    @login_required
    def update_shop_profile():
        shop = ShopProfile.query.filter_by(user_id=current_user.id).first()
        if not shop:
            shop = ShopProfile(user_id=current_user.id)
            db.session.add(shop)
            
        shop.shop_name = request.form.get('shop_name')
        shop.address = request.form.get('address')
        shop.mobile = request.form.get('mobile')

        shop.gst_no = request.form.get('gst_no')
        shop.gst_no = request.form.get('gst_no')
        shop.terms = request.form.get('terms')
        
        # Handle Bill Creators (List)
        creators_str = request.form.get('bill_creators', '')
        # Split by comma, strip whitespace, remove empty
        shop.bill_creators = [x.strip() for x in creators_str.split(',') if x.strip()]
        
        # Handle Logo Logic
        file = request.files.get('logo')
        
        # 1. Check for New Upload
        if file and file.filename:
            filename = secure_filename(file.filename)
            # Ensure static/uploads exists
            upload_folder = os.path.join(app.root_path, 'static', 'uploads')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
                
            # Save file
            filepath = os.path.join(upload_folder, filename)
            file.save(filepath)
            
            # Store relative path for template
            shop.logo = f'uploads/{filename}'
            
        # 2. Check for Deletion (Only if no new file uploaded)
        elif request.form.get('delete_logo'):
             shop.logo = None
             
        db.session.commit()
        flash('Shop profile updated!', 'success')
        return redirect(url_for('settings'))



    @app.route('/custom_categories')
    @login_required
    def custom_categories():
        # Fetch System defaults (user_id=None) OR My Custom (user_id=current_user.id)
        # However, for simplicity, maybe we list them separately or merged?
        # Let's filter strictly for what they can MANAGE (Custom ones)
        # But for display in measurements, we need both.
        # Here we only show list to MANAGE custom categories presumably.
        
        my_male = Category.query.filter_by(gender='male', user_id=current_user.id).all()
        my_female = Category.query.filter_by(gender='female', user_id=current_user.id).all()
        
        # Optionally fetch system ones to show? prompt says "verify User A sees system categories".
        # Assume system ones are not editable here.
        
        return render_template('custom_categories.html', male_categories=my_male, female_categories=my_female, active_page='custom_categories')

    @app.route('/settings/category/add', methods=['POST'])
    @login_required
    def add_category():
        try:
            name = request.form.get('name', '').strip().title() # Force Title Case
            gender = request.form.get('gender')
            fields_json_str = request.form.get('fields_json')
            
            import json
            fields_list = json.loads(fields_json_str) if fields_json_str else []
            
            new_cat = Category(name=name, gender=gender, is_custom=True, fields_json=fields_list, user_id=current_user.id)
            db.session.add(new_cat)
            db.session.commit()
            flash(f'Category "{name}" added successfully.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding category: {str(e)}', 'danger')
        return redirect(url_for('custom_categories'))


    @app.route('/settings/category/delete/<int:id>')
    @login_required
    def delete_category(id):
        try:
            # Only allow deleting OWN categories
            cat = Category.query.filter_by(id=id, user_id=current_user.id).first_or_404()
            # Check if used?? cascading?
            # For now simple delete.
            # Measurements using this category might break or just keep ID.
            # Ideally restrict delete if used. 
            count = Measurement.query.filter_by(category_id=id).count()
            if count > 0:
                 flash(f'Cannot delete category "{cat.name}" because it is used in {count} measurements.', 'warning')
            else:
                db.session.delete(cat)
                db.session.commit()
                flash('Category deleted successfully.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting category: {str(e)}', 'danger')
        return redirect(url_for('custom_categories'))

    @app.route('/api/category/add', methods=['POST'])
    @login_required
    def api_add_quick_category():
        try:
            data = request.get_json()
            name = data.get('name', '').strip().title()
            gender = data.get('gender', 'male') # Default male if missing
            
            if not name:
                return jsonify({'success': False, 'message': 'Category name is required'}), 400
                
            # Check for duplicates (Case insensitive within user scope)
            existing = Category.query.filter_by(user_id=current_user.id, gender=gender).filter(Category.name.ilike(name)).first()
            if existing:
                return jsonify({
                    'success': True, 
                    'message': 'Category exists', 
                    'category': {
                        'id': existing.id, 
                        'name': existing.name, 
                        'fields': existing.fields_json
                    }
                })
                
            # Create New
            new_cat = Category(
                name=name, 
                gender=gender, 
                is_custom=True, 
                fields_json=[], # Empty by default for "Other"
                user_id=current_user.id
            )
            db.session.add(new_cat)
            db.session.commit()
            
            return jsonify({
                'success': True, 
                'message': 'Category created', 
                'category': {
                    'id': new_cat.id, 
                    'name': new_cat.name, 
                    'fields': new_cat.fields_json
                }
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500



    @app.route('/dashboard')
    @login_required
    def dashboard():
        from datetime import date, timedelta
        from sqlalchemy import func
        from sqlalchemy.orm import joinedload
        from sqlalchemy import text
        
        today = date.today()
        yesterday = today - timedelta(days=1)
        week_start = today - timedelta(days=7)
        
        # 1. Customer Stats
        total_customers = Customer.query.filter_by(user_id=current_user.id).count()
        new_customers_week = Customer.query.filter(Customer.user_id==current_user.id, Customer.last_visit >= week_start).count()
        customers_today = Customer.query.filter(Customer.user_id==current_user.id, func.date(Customer.last_visit) == today).count()
        customers_yesterday = Customer.query.filter(Customer.user_id==current_user.id, func.date(Customer.last_visit) == yesterday).count()
        
        diff_today = customers_today - customers_yesterday
        
        # 2. Financials
        # Total Pending Balance
        total_pending = db.session.query(func.sum(Order.balance)).filter(Order.user_id==current_user.id).scalar() or 0
        
        # Balance added today
        added_today = db.session.query(func.sum(Order.total_amt)).filter(Order.user_id==current_user.id, func.date(Order.created_at) == today).scalar() or 0
        
        # Total Revenue
        total_revenue = db.session.query(func.sum(Order.total_amt)).filter(Order.user_id==current_user.id).scalar() or 0

        # --- NEW: Monthly Metrics ---
        # Monthly Customers
        monthly_customers = Customer.query.filter(
            Customer.user_id == current_user.id,
            func.extract('month', Customer.created_date) == today.month,
            func.extract('year', Customer.created_date) == today.year
        ).count()

        # Monthly Pending Balance
        monthly_pending = db.session.query(func.sum(Order.balance)).filter(
            Order.user_id == current_user.id,
            func.extract('month', Order.created_at) == today.month,
            func.extract('year', Order.created_at) == today.year
        ).scalar() or 0

        # Monthly Revenue
        monthly_revenue = db.session.query(func.sum(Order.total_amt)).filter(
            Order.user_id == current_user.id,
            func.extract('month', Order.created_at) == today.month,
            func.extract('year', Order.created_at) == today.year
        ).scalar() or 0
        
        # --- NEW: Yearly Metrics ---
        # Yearly Customers
        yearly_customers = Customer.query.filter(
            Customer.user_id == current_user.id,
            func.extract('year', Customer.created_date) == today.year
        ).count()

        # Yearly Revenue
        yearly_revenue = db.session.query(func.sum(Order.total_amt)).filter(
            Order.user_id == current_user.id,
            func.extract('year', Order.created_at) == today.year
        ).scalar() or 0
        # -----------------------------
        
        # 3. Order Stats
        pending_delivery = Order.query.filter_by(user_id=current_user.id).filter(Order.work_status.in_(['Working', 'Ready to Deliver'])).count()
        delivery_today = Order.query.filter_by(user_id=current_user.id).filter(Order.delivery_date == today).filter(Order.work_status != 'Delivered').count()
        
        stats = {
            "total_customers": total_customers,
            "customers_this_week": new_customers_week,
            "today_customers": customers_today,
            "today_vs_yesterday": diff_today,
            "pending_balance": total_pending,
            "balance_added": added_today, 
            "pending_delivery": pending_delivery,
            "delivery_today": delivery_today,
            "total_revenue": total_revenue,
            "monthly_customers": monthly_customers,
            "monthly_pending": monthly_pending,
            "monthly_revenue": monthly_revenue,
            "yearly_customers": yearly_customers,
            "yearly_revenue": yearly_revenue
        }
        
        # Recent Activity (Last 5 Orders)
        recent_activity = Order.query.filter_by(user_id=current_user.id).options(joinedload(Order.customer)).order_by(Order.created_at.desc()).limit(5).all()
        
        # Today's Orders
        todays_orders_all = Order.query.filter_by(user_id=current_user.id).options(joinedload(Order.customer)).filter(func.date(Order.created_at) == today).order_by(Order.created_at.desc()).all()
        # Filter out opening balances
        todays_orders = [o for o in todays_orders_all if not (o.items and o.items[0].get('name') == "Previous Balance Due")]
        
        # Urgent Reminders
        urgent_reminders = []
        due_orders = Order.query.filter_by(user_id=current_user.id).options(joinedload(Order.customer)).filter(Order.delivery_date <= today, Order.work_status != 'Delivered').order_by(Order.delivery_date.asc()).limit(50).all()
        
        for o in due_orders:
            if o.items and o.items[0].get('name') == "Previous Balance Due":
                continue
            days_diff = (o.delivery_date - today).days
            date_str = "Today" if days_diff == 0 else f"Overdue ({o.delivery_date.strftime('%d-%b')})"
            urgent_reminders.append({
                'title': o.customer.name, 
                'desc': f"Delivery {date_str} - Order {o.id}",
                'type': 'delivery',
                'link': url_for('orders'),
                'icon': 'fa-shirt',
                'color': 'var(--danger-color)'
            })
            
        # Graph Data: Monthly Customers (Last 6 Months)
        graph_data = db.session.query(
            func.strftime('%m-%Y', Customer.created_date).label('month'),
            func.count(Customer.id)
        ).filter(Customer.user_id == current_user.id).group_by('month').order_by(func.min(Customer.created_date)).limit(6).all()
        
        chart_labels = []
        chart_values = []
        for month_str, count in graph_data:
            try:
                m_obj = datetime.strptime(month_str, '%m-%Y')
                chart_labels.append(m_obj.strftime('%b'))
            except:
                chart_labels.append(month_str)
            chart_values.append(count)

        # Pie Chart Data: Order Status Distribution
        status_counts = db.session.query(
            Order.work_status, func.count(Order.id)
        ).filter(Order.user_id == current_user.id).group_by(Order.work_status).all()
        
        pie_data = {'Working': 0, 'Ready to Deliver': 0, 'Delivered': 0}
        for status, count in status_counts:
            if status in ['Pending', 'Processing']: key = 'Working'
            elif status == 'Ready': key = 'Ready to Deliver'
            else: key = status
            
            if key in pie_data:
                pie_data[key] += count
            else:
                pie_data.setdefault('Other', 0)
                pie_data['Other'] += count
                
        pie_labels = list(pie_data.keys())
        pie_values = list(pie_data.values())
        
        # Upcoming Deliveries
        next_week = today + timedelta(days=7)
        upcoming_deliveries_all = Order.query.filter_by(user_id=current_user.id).options(joinedload(Order.customer)).filter(
            Order.delivery_date > today,
            Order.delivery_date <= next_week,
            Order.work_status != 'Delivered'
        ).order_by(Order.delivery_date.asc()).limit(20).all() 
        
        upcoming_deliveries = [o for o in upcoming_deliveries_all if not (o.items and o.items[0].get('name') == "Previous Balance Due")][:5]

        # Top Customers
        top_customers = db.session.query(
            Customer, func.sum(Order.total_amt).label('total_spend')
        ).join(Order).filter(Customer.user_id == current_user.id).group_by(Customer.id).order_by(text('total_spend DESC')).limit(5).all()
        
        return render_template('dashboard.html', stats=stats, todays_orders=todays_orders, urgent_reminders=urgent_reminders, upcoming_deliveries=upcoming_deliveries, top_customers=top_customers, active_page='dashboard', chart_labels=chart_labels, chart_values=chart_values, pie_labels=pie_labels, pie_values=pie_values)

    @app.route('/customers', methods=['GET', 'POST'])
    @app.route('/customers', methods=['GET', 'POST'])
    @login_required
    def customers():
        if request.method == 'POST':
            # Quick Add / Edit Customer Logic
            cust_id = request.form.get('customer_id')
            name = request.form.get('name')
            mobile = request.form.get('mobile')
            gender = request.form.get('gender')
            
            if name and mobile:
                if cust_id:
                    # Edit Existing Customer
                    cust = Customer.query.filter_by(id=cust_id, user_id=current_user.id).first()
                    if cust:
                        cust.name = name
                        cust.mobile = mobile
                        cust.gender = gender
                        cust.city = request.form.get('city')
                        cust.area = request.form.get('area')
                        cust.notes = request.form.get('notes')
                        
                        # Handle Photo Upload (Update)
                        if 'photo' in request.files:
                            file = request.files['photo']
                            if file and file.filename != '':
                                from werkzeug.utils import secure_filename
                                import os
                                
                                filename = secure_filename(file.filename)
                                import uuid
                                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                                
                                upload_folder = os.path.join(app.root_path, 'static', 'uploads', 'customers')
                                if not os.path.exists(upload_folder):
                                    os.makedirs(upload_folder)
                                    
                                file.save(os.path.join(upload_folder, unique_filename))
                                cust.photo = f"uploads/customers/{unique_filename}"
                                
                        try:
                            db.session.commit()
                            flash('Customer updated successfully!', 'success')
                        except Exception as e:
                            print(e)
                            db.session.rollback()
                            if 'UNIQUE constraint failed: customer.mobile' in str(e) or 'IntegrityError' in str(e):
                                flash('Error: This mobile number is already registered.', 'error')
                            else:
                                flash(f'Error updating customer: {str(e)}', 'error')
                else:
                    # Create New Customer
                    new_cust = Customer(
                        name=name, 
                        mobile=mobile, 
                        gender=gender, 
                        city=request.form.get('city'),
                        area=request.form.get('area'),
                        notes=request.form.get('notes'),
                        user_id=current_user.id
                    )

                    # Handle Photo Upload
                    if 'photo' in request.files:
                        file = request.files['photo']
                        if file and file.filename != '':
                            from werkzeug.utils import secure_filename
                            import os
                            
                            filename = secure_filename(file.filename)
                            # Use a unique name to prevent collisions
                            import uuid
                            unique_filename = f"{uuid.uuid4().hex}_{filename}"
                            
                            upload_folder = os.path.join(app.root_path, 'static', 'uploads', 'customers')
                            if not os.path.exists(upload_folder):
                                os.makedirs(upload_folder)
                                
                            file.save(os.path.join(upload_folder, unique_filename))
                            new_cust.photo = f"uploads/customers/{unique_filename}"

                    db.session.add(new_cust)
                    try:
                        db.session.commit()
                        # Removed auto-redirect to measurements
                        flash('Customer added successfully!', 'success')
                    except Exception as e:
                        db.session.rollback()
                        if 'UNIQUE constraint failed: customer.mobile' in str(e) or 'IntegrityError' in str(e):
                             flash('Error: This mobile number is already registered.', 'error')
                        else:
                             flash(f'Error adding customer: {str(e)}', 'error')
            
            return redirect(url_for('customers'))



        # GET: List customers with Keyset Pagination & Optimization
        
        # 1. Filters
        search_query = request.args.get('q')
        gender_filter = request.args.get('gender')
        status_filter = request.args.get('status')
        date_filter = request.args.get('date') # Specific date filter

        # Month Filter (Logic: Month Range)
        try:
            current_month = int(request.args.get('month', datetime.now().month))
            current_year = int(request.args.get('year', datetime.now().year))
        except ValueError:
            current_month = datetime.now().month
            current_year = datetime.now().year

        import calendar
        _, last_day = calendar.monthrange(current_year, current_month)
        start_date = datetime(current_year, current_month, 1)
        end_date = datetime(current_year, current_month, last_day, 23, 59, 59)

        # 2. Keyset Params
        cursor_visit_str = request.args.get('cursor_visit')
        cursor_id = request.args.get('cursor_id', type=int)
        direction = request.args.get('dir', 'next') # next or prev
        limit = 50

        # Parse Cursor Visit
        cursor_visit = None
        if cursor_visit_str and cursor_visit_str != 'None':
             try:
                 cursor_visit = datetime.fromisoformat(cursor_visit_str)
             except:
                 cursor_visit = None
        
        # 3. Build Query (Select only necessary fields)
        # Filter by User FIRST
        query = Customer.query.filter_by(user_id=current_user.id).options(
            db.load_only(Customer.id, Customer.name, Customer.mobile, Customer.gender, Customer.last_visit, Customer.photo)
        )

        # Apply Filters
        if search_query:
            search = f"%{search_query}%"
            query = query.filter((Customer.name.ilike(search)) | (Customer.mobile.ilike(search)))
        
        if gender_filter:
            query = query.filter(Customer.gender == gender_filter)
        
        if date_filter:
            from sqlalchemy import func
            query = query.filter(func.date(Customer.last_visit) == date_filter)
        else:
            # Default Month filter (only if no specific date selected)
            query = query.filter(Customer.last_visit >= start_date, Customer.last_visit <= end_date)

        # Optimized Status Filter (EXISTS instead of list of IDs)
        if status_filter:
            if status_filter == 'pending':
                # Filter customers who have orders with balance > 0 check order user_id too for safety
                query = query.filter(Customer.orders.any((Order.balance > 0) & (Order.user_id == current_user.id))) 
            elif status_filter == 'paid':
                # Customers with no pending orders
                query = query.filter(~Customer.orders.any((Order.balance > 0) & (Order.user_id == current_user.id)))

        # 4. Standard Pagination
        page = request.args.get('page', 1, type=int)
        per_page = 50
        
        query = query.order_by(Customer.last_visit.desc(), Customer.id.desc())
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        customers_list = pagination.items

        # 5. Optimize N+1 (Fetch Stats for these 50)
        if customers_list:
            cust_ids = [c.id for c in customers_list]
            
            # Count Orders (filtered by user_id)
            from sqlalchemy import func
            order_counts = db.session.query(Order.customer_id, func.count(Order.id))\
                .filter(Order.customer_id.in_(cust_ids), Order.user_id==current_user.id)\
                .group_by(Order.customer_id).all()
            count_map = {r[0]: r[1] for r in order_counts}
            
            # Sum Balance (filtered by user_id)
            balance_sums = db.session.query(Order.customer_id, func.sum(Order.balance))\
                .filter(Order.customer_id.in_(cust_ids), Order.user_id==current_user.id)\
                .group_by(Order.customer_id).all()
            balance_map = {r[0]: (r[1] or 0) for r in balance_sums}
            
            # Attach to objects
            for c in customers_list:
                c.order_count_opt = count_map.get(c.id, 0)
                c.total_pending_opt = balance_map.get(c.id, 0)

        # Navigation Links Logic for Month
        prev_m = current_month - 1
        prev_y = current_year

        if prev_m == 0:
            prev_m = 12
            prev_y -= 1
            
        next_m = current_month + 1
        next_y = current_year
        if next_m == 13:
            next_m = 1
            next_y += 1
            
        month_nav = {
            'current': f"{calendar.month_name[current_month]} {current_year}",
            'prev_url': url_for('customers', month=prev_m, year=prev_y, status=status_filter, gender=gender_filter, q=search_query),
            'next_url': url_for('customers', month=next_m, year=next_y, status=status_filter, gender=gender_filter, q=search_query)
        }
        
        return render_template('customers.html', customers=customers_list, pagination=pagination, month_nav=month_nav, active_page='customers')

    @app.route('/api/measurement/<int:id>')
    @login_required
    def api_measurement_single(id):
        # Enforce User Ownership
        meas = Measurement.query.filter_by(id=id, user_id=current_user.id).first_or_404()
        return jsonify({
            "id": meas.id,
            "category_id": meas.category_id,
            "data": meas.measurements_json,
            "remarks": meas.remarks
        })

    @app.route('/api/customer/<int:id>')
    @login_required
    def api_customer_details(id):
        customer = Customer.query.filter_by(id=id, user_id=current_user.id).first_or_404()
        
        # Serialize Measurements
        measurements_data = []
        for m in customer.measurements:
            measurements_data.append({
                "id": m.id,
                "category": m.category.name if m.category else "Unknown",
                "date": m.date.strftime('%d-%b-%Y'),
                "remarks": m.remarks or "",
                "data": m.measurements_json 
            })
            
        return jsonify({
            "id": customer.id,
            "name": customer.name,
            "mobile": customer.mobile,
            "gender": customer.gender,
            "city": "Ahmedabad", 
            "total_pending": customer.total_pending,
            "measurements": measurements_data,
            "orders_count": len(customer.orders),
            "photo": customer.photo
        })

    @app.route('/customer/<int:id>/measurement', methods=['GET', 'POST'])
    @login_required
    def measurement(id):
        customer = Customer.query.filter_by(id=id, user_id=current_user.id).first_or_404()
        # Fetch categories: Custom (mine) OR System Default (None) for THIS user's gender or generic?
        # Categories usually filtered by gender.
        # Filter: gender match AND (user_id is None OR user_id is mine)
        # Custom Categories Only: User requested to remove "pre-existing" (System) categories.
        # So we ONLY fetch categories belonging to the current user.
        categories = Category.query.filter(Category.gender == customer.gender.lower()).filter(Category.user_id == current_user.id).all()
        
        # Handle Reuse Measurement
        reuse_id = request.args.get('reuse_id')
        reuse_measurement = None
        if reuse_id:
            reuse_measurement = Measurement.query.filter_by(id=reuse_id, user_id=current_user.id).first()
            if reuse_measurement and reuse_measurement.customer_id != customer.id:
                 reuse_measurement = None

        if request.method == 'POST':
            # Save Measurement
            cat_id = request.form.get('category_id')
            measurements_data = request.form.get('measurements_json') 
            remarks = request.form.get('remarks')
            
            if cat_id and measurements_data:
                import json
                try:
                    m_json = json.loads(measurements_data)
                    
                    # 1. Validation: Check if empty (all values empty)
                    has_data = any(str(v).strip() for v in m_json.values() if v is not None)
                    
                    if has_data:
                        # 2. Check for Duplicates (Equality with last active measurement)
                        last_meas = Measurement.query.filter_by(
                            customer_id=id, 
                            category_id=cat_id, 
                            is_active=True,
                            user_id=current_user.id
                        ).order_by(Measurement.date.desc()).first()

                        # Only save if different
                        if not last_meas or last_meas.measurements_json != m_json or (remarks and last_meas.remarks != remarks):
                            new_meas = Measurement(
                                customer_id=id,
                                category_id=cat_id,
                                measurements_json=m_json,
                                remarks=remarks,
                                user_id=current_user.id
                            )
                            db.session.add(new_meas)
                            db.session.flush() # Get ID
                            app.logger.info(f"Measurement ID {new_meas.id} created/flushed.")
                        else:
                             app.logger.info("Duplicate measurement detected. Skipping save.")
                    else:
                        app.logger.info("Empty measurement data. Skipping save.")
                    
                    # ALWAYS Create Order
                    start_date_str = request.form.get('start_date')
                    delivery_date_str = request.form.get('delivery_date')
                    work_status = request.form.get('order_status') or 'Processing'
                    order_notes = request.form.get('order_notes')
                    
                    total = round(float(request.form.get('total_amt') or 0.0), 2)
                    advance = round(float(request.form.get('advance') or 0.0), 2)
                    payment_mode = request.form.get('payment_mode')
                    
                    # Determine Payment Status
                    balance = round(total - advance, 2)
                    pay_status = 'Pending'
                    
                    if total > 0:
                        if balance <= 0: 
                            pay_status = 'Paid'
                        elif advance > 0: 
                            pay_status = 'Partial'
                    
                    from datetime import datetime
                    
                    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None
                    delivery_date = datetime.strptime(delivery_date_str, '%Y-%m-%d').date() if delivery_date_str else None
                    
                    # Fetch Category Name for Item Description
                    category = Category.query.get(cat_id)
                    item_name = category.name if category else "Custom Tailoring"

                    new_order = Order(
                        customer_id=id,
                        user_id=current_user.id,
                        items=[{"name": item_name, "qty": 1}], # Dynamic item name
                        work_status=work_status,
                        payment_status=pay_status,
                        start_date=start_date,
                        delivery_date=delivery_date,
                        notes=order_notes,
                        total_amt=total, 
                        advance=advance,
                        balance=total - advance, 
                        payment_mode=payment_mode,
                        bill_created_by=request.form.get('created_by') or 'System'
                    )
                    
                    db.session.add(new_order)
                    db.session.commit()
                    
                    
                    # Log History
                    # History removed
                    db.session.commit()

                    flash('Measurement saved and Order created successfully!', 'success')
                    # Redirect to customers instead of invoice as per user request
                    return redirect(url_for('customers'))

                except Exception as e:
                    print(e)
                    db.session.rollback()
            
            return redirect(url_for('customers'))

        return render_template('measurement.html', customer=customer, categories=categories, active_page='customers', reuse_measurement=reuse_measurement)

    @app.route('/measurements')
    @login_required
    def measurements():
        from sqlalchemy.orm import joinedload
        from sqlalchemy import tuple_
        import calendar

        # 1. Month Filter (Consistency)
        try:
            current_month = int(request.args.get('month', datetime.now().month))
            current_year = int(request.args.get('year', datetime.now().year))
        except ValueError:
            current_month = datetime.now().month
            current_year = datetime.now().year
            
        _, last_day = calendar.monthrange(current_year, current_month)
        start_date = datetime(current_year, current_month, 1)
        end_date = datetime(current_year, current_month, last_day, 23, 59, 59)

        # 2. Keyset Params
        cursor_date_str = request.args.get('cursor_date')
        cursor_id = request.args.get('cursor_id', type=int)
        direction = request.args.get('dir', 'next')
        limit = 50

        cursor_date = None
        if cursor_date_str and cursor_date_str != 'None':
             try:
                 cursor_date = datetime.fromisoformat(cursor_date_str)
             except:
                 cursor_date = None

        # 3. Build Query
        # Filter by User FIRST
        query = Measurement.query.filter_by(user_id=current_user.id).options(
            joinedload(Measurement.customer),
            joinedload(Measurement.category)
        )

        # Filter by Month (Default)
        query = query.filter(Measurement.date >= start_date, Measurement.date <= end_date)

        # 4. Standard Pagination
        page = request.args.get('page', 1, type=int)
        
        query = query.order_by(Measurement.date.desc(), Measurement.id.desc())
        
        pagination = query.paginate(page=page, per_page=limit, error_out=False)
        measurements_list = pagination.items

        # Month Navigation Links
        prev_m = current_month - 1
        prev_y = current_year
        if prev_m == 0:
            prev_m = 12
            prev_y -= 1
        next_m = current_month + 1
        next_y = current_year
        if next_m == 13:
            next_m = 1
            next_y += 1
            
        month_nav = {
            'current': f"{calendar.month_name[current_month]} {current_year}",
            'prev_url': url_for('measurements', month=prev_m, year=prev_y),
            'next_url': url_for('measurements', month=next_m, year=next_y)
        }

        return render_template('measurements.html', measurements=measurements_list, pagination=pagination, month_nav=month_nav, active_page='measurements')

    @app.route('/customer/<int:id>/history')
    @login_required
    def customer_measurement_history(id):
        customer = Customer.query.filter_by(id=id, user_id=current_user.id).first_or_404()
        # Fetch all measurements for this customer, sorted by newest first
        measurements = Measurement.query.filter_by(customer_id=id, user_id=current_user.id).order_by(Measurement.date.desc()).all()
        return render_template('measurement_history.html', customer=customer, measurements=measurements, active_page='customers')

    @app.route('/orders', methods=['GET'])
    @login_required
    def orders():
        import calendar
        from sqlalchemy import func

        # Filters
        search_query = request.args.get('q')
        status_filter = request.args.get('status')
        
        # Month Filter (Logic: One Month One Page)
        try:
            current_month = int(request.args.get('month', datetime.now().month))
            current_year = int(request.args.get('year', datetime.now().year))
        except ValueError:
            current_month = datetime.now().month
            current_year = datetime.now().year
            
        # Calculate Start and End of the selected month
        _, last_day = calendar.monthrange(current_year, current_month)
        start_date = datetime(current_year, current_month, 1)
        end_date = datetime(current_year, current_month, last_day, 23, 59, 59)
        
        # Base Query scoped to User
        query = Order.query.filter_by(user_id=current_user.id)
        
        # New: Delivery Date Filter (Overrides month filter)
        delivery_date_param = request.args.get('delivery_date')
        if delivery_date_param:
            if delivery_date_param == 'today':
                from datetime import date
                filter_date = date.today()
                query = query.filter(Order.delivery_date == filter_date)
            else:
                try:
                    filter_date = datetime.strptime(delivery_date_param, '%Y-%m-%d').date()
                    query = query.filter(Order.delivery_date == filter_date)
                except:
                    # Fallback to month filter if invalid
                    query = query.filter(Order.created_at >= start_date, Order.created_at <= end_date)
        else:
             query = query.filter(Order.created_at >= start_date, Order.created_at <= end_date)
        
        if search_query:
            search = f"%{search_query}%"
            # Join with Customer to search by name/mobile
            query = query.join(Customer).filter((Customer.name.ilike(search)) | (Customer.mobile.ilike(search)))
            
        if status_filter:
            if status_filter == 'pending':
                query = query.filter(Order.balance > 0)
            elif status_filter == 'paid':
                 query = query.filter(Order.balance <= 0)

        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = 50
        pagination = query.order_by(Order.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
        orders_list = pagination.items
        
        # Navigation Links
        prev_m = current_month - 1
        prev_y = current_year
        if prev_m == 0:
            prev_m = 12
            prev_y -= 1
            
        next_m = current_month + 1
        next_y = current_year
        if next_m == 13:
            next_m = 1
            next_y += 1
            
        month_nav = {
            'current': f"{calendar.month_name[current_month]} {current_year}",
            'prev_url': url_for('orders', month=prev_m, year=prev_y, status=status_filter, q=search_query),
            'next_url': url_for('orders', month=next_m, year=next_y, status=status_filter, q=search_query)
        }

        return render_template('orders.html', orders=orders_list, pagination=pagination, month_nav=month_nav, active_page='orders')

    @app.route('/orders/update_details', methods=['POST'])
    @login_required
    def orders_update_details():
        order_id = request.form.get('order_id')
        
        # 1. Update Production Status
        status = request.form.get('status')
        
        # 2. Update Payment Details
        try:
            total = round(float(request.form.get('total_amt') or 0), 2)
            advance = round(float(request.form.get('advance') or 0), 2)
            mode = request.form.get('payment_mode')
            delivery_date_str = request.form.get('delivery_date')
            
            # Check ownership
            order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
            
            # Update fields
            if status:
                order.work_status = status
            
            if delivery_date_str:
                from datetime import datetime
                order.delivery_date = datetime.strptime(delivery_date_str, '%Y-%m-%d').date()
                
            order.total_amt = total
            order.advance = advance
            order.balance = round(total - advance, 2)
            order.payment_mode = mode
            
            created_by = request.form.get('bill_created_by')
            if created_by:
                order.bill_created_by = created_by
            
            # Recalculate Payment Status
            if order.total_amt > 0:
                if order.balance <= 0:
                    order.payment_status = 'Paid'
                elif order.advance > 0:
                     order.payment_status = 'Partial'
                else:
                     order.payment_status = 'Pending'
            else:
                 order.payment_status = 'Pending'
    
            db.session.commit()
            flash('Order details updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating order: {str(e)}', 'danger')
            
        return redirect(url_for('orders'))

    @app.route('/delete-customer/<int:id>', methods=['POST'])
    @login_required
    def delete_customer(id):
        customer = Customer.query.filter_by(id=id, user_id=current_user.id).first_or_404()
        try:
            # Delete related records
            Measurement.query.filter_by(customer_id=id).delete() # Cascade technically handles this but ok
            Order.query.filter_by(customer_id=id).delete()
            Reminder.query.filter_by(customer_id=id).delete()
            
            db.session.delete(customer)
            db.session.commit()
            flash('Customer deleted successfully.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting customer: {str(e)}', 'danger')
            
        return redirect(url_for('customers'))

    @app.route('/delete/order/<int:id>', methods=['POST'])
    @login_required
    def delete_order(id):
        order = Order.query.filter_by(id=id, user_id=current_user.id).first_or_404()
        try:
            db.session.delete(order)
            db.session.commit()
            flash('Order deleted successfully.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting order: {str(e)}', 'danger')
            
        return redirect(url_for('orders'))

    @app.route('/bills')
    @login_required
    def bills():
        from datetime import datetime
        import calendar

        # Logic for Bills is same as Orders but simplified view
        search_query = request.args.get('q')
        status_filter = request.args.get('status')
        date_filter = request.args.get('date')
        
        # Month Filter (Logic: One Month One Page)
        try:
            current_month = int(request.args.get('month', datetime.now().month))
            current_year = int(request.args.get('year', datetime.now().year))
        except ValueError:
            current_month = datetime.now().month
            current_year = datetime.now().year
            
        # Calculate Start and End of the selected month
        _, last_day = calendar.monthrange(current_year, current_month)
        start_date = datetime(current_year, current_month, 1)
        end_date = datetime(current_year, current_month, last_day, 23, 59, 59)
        
        from sqlalchemy import func
        # Filter by User
        query = Order.query.filter_by(user_id=current_user.id).filter(Order.created_at >= start_date, Order.created_at <= end_date)
        
        if search_query:
             search = f"%{search_query}%"
             query = query.join(Customer).filter((Customer.name.ilike(search)) | (Customer.mobile.ilike(search)))
             
        if status_filter:
            if status_filter == 'pending':
                 query = query.filter(Order.balance > 0)
            elif status_filter == 'paid':
                 query = query.filter(Order.balance <= 0)

        if date_filter:
            from sqlalchemy import func
            query = query.filter(func.date(Order.created_at) == date_filter)

        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = 50
        pagination = query.order_by(Order.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
        bills_list = pagination.items
        
        # Navigation Links
        prev_m = current_month - 1
        prev_y = current_year
        if prev_m == 0:
            prev_m = 12
            prev_y -= 1
            
        next_m = current_month + 1
        next_y = current_year
        if next_m == 13:
            next_m = 1
            next_y += 1
            
        month_nav = {
            'current': f"{calendar.month_name[current_month]} {current_year}",
            'prev_url': url_for('bills', month=prev_m, year=prev_y, status=status_filter, q=search_query),
            'next_url': url_for('bills', month=next_m, year=next_y, status=status_filter, q=search_query)
        }

        return render_template('bills.html', bills=bills_list, pagination=pagination, month_nav=month_nav, active_page='bills')
    
    @app.route('/bills/update', methods=['POST'])
    @login_required
    def bills_update():
        order_id = request.form.get('order_id')
        total = round(float(request.form.get('total_amt') or 0), 2)
        advance = round(float(request.form.get('advance') or 0), 2)
        mode = request.form.get('payment_mode')
        delivery_date_str = request.form.get('delivery_date')
        
        # Check ownership
        order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
        
        order.total_amt = total
        order.advance = advance
        order.balance = round(total - advance, 2)
        
        if delivery_date_str:
            from datetime import datetime
            order.delivery_date = datetime.strptime(delivery_date_str, '%Y-%m-%d').date()
        
        # Recalculate Payment Status (Enforce Consistency)
        if order.total_amt > 0:
            if order.balance <= 0:
                order.payment_status = 'Paid'
            elif order.advance > 0:
                 order.payment_status = 'Partial'
            else:
                 order.payment_status = 'Pending'
        else:
             order.payment_status = 'Pending'

        order.payment_mode = mode
        
        db.session.commit()
        return redirect(url_for('bills'))

    # --- Additional Features (Reminders, Search, Invoices) ---
    @app.route('/settings/reset_data', methods=['POST'])
    @login_required
    def reset_data():
        try:
            # 1. Clear Database Tables (Scoped to User)
            
            # Delete Reminders
            db.session.query(Reminder).filter(Reminder.customer.has(user_id=current_user.id)).delete(synchronize_session=False)

            # Delete Transactional Data
            db.session.query(Order).filter_by(user_id=current_user.id).delete()
            db.session.query(Measurement).filter_by(user_id=current_user.id).delete()
            db.session.query(Customer).filter_by(user_id=current_user.id).delete()
            
            db.session.commit()
            
            # 2. Clear Saved Bills Directory (Skipped for multi-tenant safety unless per-user folder)
            # import shutil
            # bills_dir = os.path.join(app.root_path, 'saved_bills')
            # ...
            
            flash('Your data (Orders, Customers, Measurements) has been reset.', 'success')
        except Exception as e:
            db.session.rollback()
            print(f"Reset Error: {e}")
            flash(f'Error resetting data: {str(e)}', 'danger')
        return redirect(url_for('settings'))

    @app.route('/reminders')
    @login_required
    def reminders():
        from datetime import date, timedelta
        
        today = date.today()
        tomorrow = today + timedelta(days=1)
        
        # 1. Urgent / Overdue Deliveries (Due <= Today AND Not Delivered)
        urgent_orders = Order.query.filter_by(user_id=current_user.id).filter(
            Order.delivery_date <= today, 
            Order.work_status != 'Delivered'
        ).order_by(Order.delivery_date.asc()).all()
        
        # 2. Upcoming Deliveries (Tomorrow)
        upcoming_orders = Order.query.filter_by(user_id=current_user.id).filter(
            Order.delivery_date == tomorrow,
            Order.work_status != 'Delivered'
        ).all()
        
        # 3. Pending Payments (Orders with Balance > 0)
        pending_payments = Order.query.filter_by(user_id=current_user.id).filter(Order.balance > 0).order_by(Order.balance.desc()).limit(10).all()
        
        return render_template('reminders.html', 
                             urgent_orders=urgent_orders, 
                             upcoming_orders=upcoming_orders,
                             pending_payments=pending_payments,
                             active_page='reminders')
        

    @app.route('/search')
    def search():
        query = request.args.get('q', '').strip()
        if not query:
            return redirect(url_for('dashboard'))
            
        # Search Customers (Name or Mobile)
        customers = Customer.query.filter(
            (Customer.name.ilike(f'%{query}%')) | 
            (Customer.mobile.ilike(f'%{query}%'))
        ).all()
        
        # Search Orders
        if query.isdigit():
             orders = Order.query.filter(Order.id == int(query)).all()
        else:
             orders = Order.query.join(Customer).filter(Customer.name.ilike(f'%{query}%')).all()

        return render_template('search_results.html', query=query, customers=customers, orders=orders, active_page='dashboard')

    # Helper for Secure Public Links
    def generate_bill_token(order_id):
        data = f"bill_view_{order_id}"
        return hmac.new(app.secret_key.encode(), data.encode(), hashlib.sha256).hexdigest()

    @app.route('/bill/view/<int:id>')
    def public_bill_view(id):
        token = request.args.get('token')
        expected_token = generate_bill_token(id)
        
        if not token or not hmac.compare_digest(token, expected_token):
             return "Invalid or Expired Link", 403
        
        order = Order.query.get_or_404(id)
        from models import ShopProfile
        shop = ShopProfile.query.first() or ShopProfile()
        
        return render_template('invoice.html', order=order, shop=shop, is_public=True)

    @app.route('/invoice/<int:id>')
    @login_required
    def view_invoice(id):
        order = Order.query.filter_by(id=id, user_id=current_user.id).first_or_404()
        
        # Determine Shop Profile
        from models import ShopProfile
        shop = ShopProfile.query.filter_by(user_id=current_user.id).first()
        if not shop:
             shop = ShopProfile(user_id=current_user.id) # Should exist by now usually
        
        # Generate Public Link for Sharing (Optional: Verify if token logic needs User ID salt?)
        # For now, token is based on ID + secret, ID is unique globally so safe-ish.
        # But if we want to secure it more, token logic might need checking. 
        # Assuming generate_bill_token uses SECRET_KEY.
        from utils import generate_bill_token
        token = generate_bill_token(id)
        public_url = url_for('public_bill_view', id=id, token=token, _external=True)
        
        return render_template('invoice.html', order=order, shop=shop, public_url=public_url)

    @app.route('/invoice/<int:id>/download')
    @login_required
    def download_invoice(id):
        import os
        from flask import send_file
        from datetime import datetime
        
        order = Order.query.filter_by(id=id, user_id=current_user.id).first_or_404()
        from models import ShopProfile
        shop = ShopProfile.query.filter_by(user_id=current_user.id).first()
        if not shop: shop = ShopProfile(user_id=current_user.id)
        
        # Render HTML
        html_content = render_template('invoice.html', order=order, shop=shop, download_mode=True)
        
        # 1. Determine Folder Path: saved_bills / user_id / YYYY / Month
        # ISOLATION: Add user_id to path
        year_str = order.created_at.strftime('%Y')
        month_str = order.created_at.strftime('%B') 
        
        folder = os.path.join(app.root_path, 'saved_bills', str(current_user.id), year_str, month_str)
        if not os.path.exists(folder):
            os.makedirs(folder)
            
        # 2. Determine Filename: Customer_Date_ID
        date_str = order.created_at.strftime('%d-%m-%Y')
        sanitized_name = order.customer.name.replace(' ', '_').replace('/', '-')
        filename = f"Bill_{sanitized_name}_{date_str}_{order.id}.html"
        
        filepath = os.path.join(folder, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        return send_file(filepath, as_attachment=True)

    @app.route('/invoice/<int:id>/save_pdf_copy', methods=['POST'])
    @login_required
    def save_pdf_copy(id):
        if 'pdf' not in request.files:
            return jsonify({'success': False, 'message': 'No file part'}), 400
            
        file = request.files['pdf']
        if file.filename == '':
             return jsonify({'success': False, 'message': 'No selected file'}), 400

        order = Order.query.filter_by(id=id, user_id=current_user.id).first_or_404()
        
        # Date Logic
        year_str = order.created_at.strftime('%Y')
        month_str = order.created_at.strftime('%B')
        
        # ISOLATION: Add user_id to path
        folder = os.path.join(app.root_path, 'saved_bills', str(current_user.id), year_str, month_str)
        
        if not os.path.exists(folder):
            os.makedirs(folder)
            
        # Determine Filename
        date_str = order.created_at.strftime('%d-%m-%Y')
        sanitized_name = order.customer.name.replace(' ', '_').replace('/', '-')
        filename = f"Bill_{sanitized_name}_{date_str}_{order.id}.pdf"
        filepath = os.path.join(folder, filename)
        
        try:
            file.save(filepath)
            
            # Remove HTML Copy (if exists) - "Replace HTML with PDF"
            html_filename = filename.replace('.pdf', '.html')
            html_filepath = os.path.join(folder, html_filename)
            if os.path.exists(html_filepath):
                try:
                    os.remove(html_filepath)
                except Exception:
                    pass

            return jsonify({'success': True, 'message': 'PDF Saved Successfully'})
        except Exception as e:
             return jsonify({'success': False, 'message': str(e)}), 500
        
    @app.route('/export_csv')
    @login_required
    def export_csv():
        import csv
        import io
        from flask import make_response
        
        # Export Orders Data for Current User
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow(['Order ID', 'Date', 'Customer Name', 'Mobile', 'Items', 'Total Amount', 'Advance', 'Balance', 'Status', 'Payment Mode'])
        
        orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
        
        for order in orders:
            items_str = ", ".join([item.get('name', '') for item in order.items]) if order.items else ""
            
            writer.writerow([
                order.id,
                order.created_at.strftime('%Y-%m-%d'),
                order.customer.name,
                order.customer.mobile,
                items_str,
                order.total_amt,
                order.advance,
                order.balance,
                order.work_status,
                order.payment_status,
                order.payment_mode
            ])
            
        output.seek(0)
        
        response = make_response(output.getvalue())
        response.headers["Content-Disposition"] = "attachment; filename=taivex_orders_export.csv"
        response.headers["Content-type"] = "text/csv"
        return response

    @app.route('/settings/export_data', methods=['POST'])
    @login_required
    def export_custom_data():
        import csv
        import io
        from datetime import datetime
        
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        data_type = request.form.get('data_type')
        
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            end_date = end_date.replace(hour=23, minute=59, second=59)
        except ValueError:
            flash('Invalid date format.', 'error')
            return redirect(url_for('settings'))

        si = io.StringIO()
        writer = csv.writer(si)
        
        filename = f"{data_type.capitalize()}_{start_date.strftime('%d-%m-%Y')}_to_{end_date.strftime('%d-%m-%Y')}.csv"
        
        if data_type == 'orders':
            orders = Order.query.filter(Order.created_at >= start_date, Order.created_at <= end_date, Order.user_id==current_user.id).all()
            writer.writerow(['Order ID', 'Customer Name', 'Mobile', 'Items', 'Total Amount', 'Advance', 'Balance', 'Status', 'Date'])
            for o in orders:
                items_str = ", ".join([f"{i['name']} (x{i['qty']})" for i in (o.items or [])])
                writer.writerow([o.id, o.customer.name, o.customer.mobile, items_str, o.total_amt, o.advance, o.balance, o.work_status, o.created_at.strftime('%Y-%m-%d')])
                
        elif data_type == 'customers':
            customers = Customer.query.filter(Customer.created_date >= start_date, Customer.created_date <= end_date, Customer.user_id==current_user.id).all()
            writer.writerow(['ID', 'Name', 'Mobile', 'City', 'Total Orders', 'Pending Balance', 'Joined Date'])
            for c in customers:
                writer.writerow([c.id, c.name, c.mobile, c.city, len(c.orders), c.total_pending, c.created_date.strftime('%Y-%m-%d')])

        elif data_type == 'measurements':
            measurements = Measurement.query.filter(Measurement.date >= start_date, Measurement.date <= end_date, Measurement.user_id==current_user.id).all()
            writer.writerow(['ID', 'Customer', 'Mobile', 'Category', 'Date', 'Details'])
            for m in measurements:
                details = str(m.measurements_json)
                writer.writerow([m.id, m.customer.name, m.customer.mobile, m.category.name, m.date.strftime('%Y-%m-%d'), details])
        
        elif data_type == 'bills':
            orders = Order.query.filter(Order.created_at >= start_date, Order.created_at <= end_date, Order.user_id==current_user.id).all()
            writer.writerow(['Bill No', 'Date', 'Customer', 'Mobile', 'Total Amount', 'Received', 'Balance', 'Payment Mode'])
            for o in orders:
                writer.writerow([o.id, o.created_at.strftime('%d-%m-%Y'), o.customer.name, o.customer.mobile, o.total_amt, o.advance, o.balance, o.payment_mode])

        csv_content = si.getvalue()
        
        output = make_response(csv_content)
        output.headers["Content-Disposition"] = f"attachment; filename={filename}"
        output.headers["Content-type"] = "text/csv"
        return output

    # Duplicate get_customer_details removed
    
    @app.route('/delete/measurement/<int:id>', methods=['POST'])
    @login_required
    def delete_measurement(id):
        m = Measurement.query.filter_by(id=id, user_id=current_user.id).first_or_404()
        try:
            db.session.delete(m)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Measurement deleted successfully'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500
