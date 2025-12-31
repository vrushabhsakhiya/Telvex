from flask import render_template, request, redirect, url_for, flash, jsonify, make_response
from models import db, Customer, Category, Measurement, Order, User, ShopProfile, mail
from flask_login import login_user, logout_user, login_required, current_user
from functools import wraps
from werkzeug.utils import secure_filename
import os
import random
import string
from datetime import datetime, timedelta
from flask_mail import Message

def master_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'master':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def register_routes(app):
    
    # Context Processor to inject current year/settings globally if needed
    @app.context_processor
    def inject_defaults():
        try:
            from models import ShopProfile
            shop = ShopProfile.query.first() or ShopProfile() # Fallback
            return dict(active_page='', current_user=current_user, shop=shop)
        except Exception as e:
            print(f"!!! ERROR IN INJECT_DEFAULTS: {e}")
            return dict(active_page='', current_user=current_user, shop=None)

    @app.route('/test')
    def test_db():
        try:
            c = User.query.count()
            return f"User count: {c}"
        except Exception as e:
            return f"DB Error: {e}"

    @app.route('/')
    def index():
        print(">>> INDEX ROUTE HIT")
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        print(">>> LOGIN ROUTE HIT")
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
            
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            user = User.query.filter_by(username=username).first()
            
            if user and user.check_password(password):
                # CHECK EMAIL VERIFICATION
                if not user.is_verified:
                    # Generate OTP and Redirect to Verify
                    otp = ''.join(random.choices(string.digits, k=6))
                    print(f"!!! DEBUG OTP: {otp} !!!")
                    user.reset_otp = otp
                    user.reset_otp_expiry = datetime.utcnow() + timedelta(minutes=15)
                    db.session.commit()
                    
                    try:
                        if not user.email:
                            flash('Account has no email. Contact Admin.', 'error')
                            return redirect(url_for('login'))

                        msg = Message('Verify Login - Taivex Pro', sender=app.config.get('MAIL_USERNAME'), recipients=[user.email])
                        msg.body = f"Your verification OTP is: {otp}. It expires in 15 minutes."
                        mail.send(msg)
                        
                        flash('First login requires verification. OTP sent to email.', 'info')
                        return redirect(url_for('verify_email_otp', email=user.email))
                    except Exception as e:
                        print(f"SMTP Error: {e}")
                        flash(f'Email failed (Dev Mode). Check server console for OTP.', 'warning')
                        return redirect(url_for('verify_email_otp', email=user.email))
                
                # If verified, proceed to login
                login_user(user)
                flash(f'Welcome back, {user.username}!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password', 'error')
        
        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.', 'success')
        return redirect(url_for('login'))

    # --- Forgot Password Routes ---
    @app.route('/forgot-password', methods=['GET', 'POST'])
    def forgot_password():
        if request.method == 'POST':
            email = request.form.get('email')
            user = User.query.filter_by(email=email).first()
            if user:
                # Generate 6-digit OTP
                otp = ''.join(random.choices(string.digits, k=6))
                print(f"!!! DEBUG OTP: {otp} !!!")
                user.reset_otp = otp
                user.reset_otp_expiry = datetime.utcnow() + timedelta(minutes=15)
                db.session.commit()
                
                try:
                    msg = Message('Password Reset OTP - Taivex Pro', sender=app.config.get('MAIL_USERNAME'), recipients=[email])
                    msg.body = f"Your OTP for password reset is: {otp}. It expires in 15 minutes."
                    mail.send(msg)
                    flash('OTP sent to your email.', 'success')
                    return redirect(url_for('verify_otp', email=email))
                except Exception as e:
                    print(f"SMTP Error: {e}")
                    flash(f'Email failed (Dev Mode). Check server console for OTP.', 'warning')
                    return redirect(url_for('verify_otp', email=email))
            else:
                flash('Email not found.', 'error')
        return render_template('forgot_password.html')

    @app.route('/verify-otp', methods=['GET', 'POST'])
    def verify_otp():
        email = request.args.get('email') or request.form.get('email')
        if not email:
            return redirect(url_for('forgot_password'))

        if request.method == 'POST':
            otp = request.form.get('otp')
            user = User.query.filter_by(email=email).first()
            if user and user.reset_otp == otp and user.reset_otp_expiry > datetime.utcnow():
                # Store verified state in session
                from flask import session 
                session['reset_verified_email'] = email
                return redirect(url_for('reset_password'))
            else:
                flash('Invalid or expired OTP.', 'error')
        
        return render_template('verify_otp.html', email=email)

    import os
    from authlib.integrations.flask_client import OAuth

    # OAuth Setup
    oauth = OAuth(app)
    google = oauth.register(
        name='google',
        client_id=os.getenv('GOOGLE_CLIENT_ID', 'YOUR_GOOGLE_CLIENT_ID_HERE'),
        client_secret=os.getenv('GOOGLE_CLIENT_SECRET', 'YOUR_GOOGLE_CLIENT_SECRET_HERE'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )

    @app.route('/google-login')
    def google_login():
        redirect_uri = url_for('google_callback', _external=True)
        return google.authorize_redirect(redirect_uri)

    @app.route('/google-callback')
    def google_callback():
        try:
            token = google.authorize_access_token()
            user_info = token.get('userinfo')
            email = user_info.get('email')
            
            if not email:
                flash('Could not retrieve email from Google.', 'error')
                return redirect(url_for('login'))
                
            # Match user by email
            user = User.query.filter_by(email=email).first()
            
            if user:
                login_user(user)
                flash(f'Welcome back, {user.username}!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('No account found with this Google email.', 'error')
                return redirect(url_for('login'))
                
        except Exception as e:
            print(f"Google Login Error: {e}")
            flash('Google Login failed. Please try again.', 'error')
            return redirect(url_for('login'))

    @app.route('/reset-password', methods=['GET', 'POST'])
    def reset_password():
        from flask import session
        email = session.get('reset_verified_email')
        if not email:
            return redirect(url_for('login'))
        
        if request.method == 'POST':
            password = request.form.get('password')
            user = User.query.filter_by(email=email).first()
            if user:
                user.set_password(password)
                user.reset_otp = None
                user.reset_otp_expiry = None
                db.session.commit()
                session.pop('reset_verified_email', None)
                flash('Password reset successfully. Please login.', 'success')
                return redirect(url_for('login'))
        return render_template('reset_password.html')
    @app.route('/verify-email-otp', methods=['GET', 'POST'])
    def verify_email_otp():
        email = request.args.get('email') or request.form.get('email')
        if not email:
            return redirect(url_for('login'))

        if request.method == 'POST':
            otp = request.form.get('otp')
            user = User.query.filter_by(email=email).first()
            
            if user and user.reset_otp == otp and user.reset_otp_expiry > datetime.utcnow():
                # Success! verify and login
                user.is_verified = True
                user.reset_otp = None
                user.reset_otp_expiry = None
                db.session.commit()
                
                login_user(user)
                flash('Email verified! You are now logged in.', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid or expired OTP.', 'error')
        
        return render_template('verify_otp.html', email=email, mode='verification')

    from functools import wraps
    
    def permission_required(perm):
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if not current_user.has_permission(perm):
                    flash('You do not have permission to access this resource.', 'error')
                    return redirect(request.referrer or url_for('dashboard'))
                return f(*args, **kwargs)
            return decorated_function
        return decorator

    # --- User Management (Master Only) ---
    @app.route('/users')
    @login_required
    def users():
        if current_user.role != 'master':
             flash('Access denied.', 'error')
             return redirect(url_for('dashboard'))
        users_list = User.query.filter(User.role != 'master').all()
        return render_template('users.html', users=users_list, active_page='users')

    @app.route('/users/create', methods=['POST'])
    @login_required
    def create_user():
        if current_user.role != 'master':
             return redirect(url_for('dashboard'))
             
        username = request.form.get('username')
        email = request.form.get('email') # New Field
        password = request.form.get('password')
        perms = request.form.getlist('permissions') # list of checked perms
        
        if not email:
            flash('Email is required for staff accounts.', 'error')
            return redirect(url_for('users'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
        elif User.query.filter_by(email=email).first():
             flash('Email already registered.', 'error')
        else:
            # New users are NOT verified by default, must verify on first login
            new_user = User(username=username, email=email, role='staff', permissions=",".join(perms), is_verified=False)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('User created successfully. They verify email on first login.', 'success')
            
        return redirect(url_for('users'))

    @app.route('/users/delete/<int:id>')
    @login_required
    def delete_user(id):
        if current_user.role != 'master':
             return redirect(url_for('dashboard'))
        
        user = User.query.get_or_404(id)
        if user.role == 'master':
            flash('Cannot delete master admin.', 'error')
        else:
            db.session.delete(user)
            db.session.commit()
            flash('User deleted.', 'success')
        return redirect(request.args.get('next') or url_for('users'))

    @app.route('/users/update_permissions', methods=['POST'])
    @login_required
    def update_user_permissions():
        if current_user.role != 'master':
             return redirect(url_for('dashboard'))
             
        user_id = request.form.get('user_id')
        user = User.query.get_or_404(user_id)
        
        if user.role != 'master':
            perms = request.form.getlist('permissions')
            email = request.form.get('email')
            
            # Check email uniqueness if changed
            if email and email != user.email and User.query.filter_by(email=email).first():
                flash('Email already taken.', 'error')
                return redirect(url_for('users'))

            user.permissions = ",".join(perms)
            user.email = email
            
            # Optional: Password Reset
            new_pass = request.form.get('new_password')
            if new_pass:
                user.set_password(new_pass)
                
            db.session.commit()
            flash('User updated successfully.', 'success')
            
        return redirect(url_for('users'))

    # --- Protected Routes ---
    


    @app.route('/settings', methods=['GET', 'POST'])
    @login_required
    def settings():
        if not current_user.has_permission('manage_settings'):
            flash('Access Denied: You do not have permission to view Settings.', 'error')
            return redirect(url_for('dashboard'))

        staff_members = User.query.all() if current_user.role == 'master' else []
        shop = ShopProfile.query.first()
        if not shop:
             shop = ShopProfile() # Temporary object for template if none exists
             
        # Categories are now handled in custom_categories, but if needed here:
        # categories = Category.query.all() 
        
        return render_template('settings.html', active_page='settings', staff_members=staff_members, shop=shop)

    @app.route('/settings/update_profile', methods=['POST'])
    @login_required
    # @permission_required('manage_settings') # Apply manual check to redirect better
    def update_shop_profile():
        # Strict check for Master Admin as requested
        if current_user.role != 'master':
            flash('Access Denied: Only Master Admin can update Shop Profile.', 'error')
            return redirect(url_for('settings'))
            
        shop = ShopProfile.query.first()
        if not shop:
            shop = ShopProfile()
            db.session.add(shop)
            
        shop.shop_name = request.form.get('shop_name')
        shop.address = request.form.get('address')
        shop.mobile = request.form.get('mobile')

        shop.gst_no = request.form.get('gst_no')
        shop.terms = request.form.get('terms')
        
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

    @app.route('/settings/admin/add', methods=['POST'])
    @login_required
    @master_required
    def add_admin():
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return redirect(url_for('settings'))
            
        new_admin = User(username=username, role='staff', created_by=current_user.id)
        new_admin.set_password(password)
        db.session.add(new_admin)
        db.session.commit()
        flash(f'Admin {username} added successfully.', 'success')
        return redirect(url_for('settings'))

    @app.route('/custom_categories')
    @login_required
    def custom_categories():
        male_categories = Category.query.filter_by(gender='male').all()
        female_categories = Category.query.filter_by(gender='female').all()
        return render_template('custom_categories.html', male_categories=male_categories, female_categories=female_categories, active_page='custom_categories')

    @app.route('/settings/category/add', methods=['POST'])
    @login_required
    def add_category():
        try:
            name = request.form.get('name', '').strip().title() # Force Title Case
            gender = request.form.get('gender')
            fields_json_str = request.form.get('fields_json')
            
            import json
            fields_list = json.loads(fields_json_str) if fields_json_str else []
            
            new_cat = Category(name=name, gender=gender, is_custom=True, fields_json=fields_list)
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
            cat = Category.query.get_or_404(id)
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



    @app.route('/dashboard')
    @login_required
    def dashboard():
        from datetime import date, timedelta
        from sqlalchemy import func
        from sqlalchemy.orm import joinedload
        
        today = date.today()
        yesterday = today - timedelta(days=1)
        week_start = today - timedelta(days=7)
        
        # 1. Customer Stats
        total_customers = Customer.query.count()
        new_customers_week = Customer.query.filter(Customer.last_visit >= week_start).count()
        customers_today = Customer.query.filter(func.date(Customer.last_visit) == today).count()
        customers_yesterday = Customer.query.filter(func.date(Customer.last_visit) == yesterday).count()
        
        diff_today = customers_today - customers_yesterday
        
        # 2. Financials
        # Total Pending Balance across ALL orders
        total_pending = db.session.query(func.sum(Order.balance)).scalar() or 0
        
        # Balance added today (New orders today)
        added_today = db.session.query(func.sum(Order.total_amt)).filter(func.date(Order.created_at) == today).scalar() or 0
        
        # Total Revenue (All time billing)
        total_revenue = db.session.query(func.sum(Order.total_amt)).scalar() or 0

        # --- NEW: Monthly Metrics ---
        # Monthly Customers
        monthly_customers = Customer.query.filter(
            func.extract('month', Customer.created_date) == today.month,
            func.extract('year', Customer.created_date) == today.year
        ).count()

        # Monthly Pending Balance (Orders created this month)
        monthly_pending = db.session.query(func.sum(Order.balance)).filter(
            func.extract('month', Order.created_at) == today.month,
            func.extract('year', Order.created_at) == today.year
        ).scalar() or 0

        # Monthly Revenue (Orders created this month)
        monthly_revenue = db.session.query(func.sum(Order.total_amt)).filter(
            func.extract('month', Order.created_at) == today.month,
            func.extract('year', Order.created_at) == today.year
        ).scalar() or 0
        
        # --- NEW: Yearly Metrics ---
        # Yearly Customers
        yearly_customers = Customer.query.filter(
            func.extract('year', Customer.created_date) == today.year
        ).count()

        # Yearly Revenue
        yearly_revenue = db.session.query(func.sum(Order.total_amt)).filter(
            func.extract('year', Order.created_at) == today.year
        ).scalar() or 0
        # -----------------------------
        
        # 3. Order Stats
        pending_delivery = Order.query.filter(Order.work_status.in_(['Working', 'Ready to Deliver'])).count()
        delivery_today = Order.query.filter(Order.delivery_date == today).filter(Order.work_status != 'Delivered').count()
        
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
        
        # Recent Activity (Last 5 Orders) - Optimized with JoinedLoad
        recent_activity = Order.query.options(joinedload(Order.customer)).order_by(Order.created_at.desc()).limit(5).all()
        
        # Today's Orders (For detailed table) - Optimized
        todays_orders_all = Order.query.options(joinedload(Order.customer)).filter(func.date(Order.created_at) == today).order_by(Order.created_at.desc()).all()
        # Filter out opening balances
        todays_orders = [o for o in todays_orders_all if not (o.items and o.items[0].get('name') == "Previous Balance Due")]
        
        # Urgent Reminders (Aggregation)
        urgent_reminders = []
        
        # 1. Deliveries Due Today/Overdue - OPTIMIZED: Limit 50, Eager Load
        # We limit to 50 because displaying 1000 overdue items on dashboard is bad UX and performance kill.
        due_orders = Order.query.options(joinedload(Order.customer)).filter(Order.delivery_date <= today, Order.work_status != 'Delivered').order_by(Order.delivery_date.asc()).limit(50).all()
        
        for o in due_orders:
            # Skip opening balance dummy orders
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
        # SQLite-specific query for monthly grouping - keeping as is (efficient enough for 6 rows)
        from sqlalchemy import text
        graph_data = db.session.query(
            func.to_char(Customer.created_date, 'MM-YYYY').label('month'),
            func.count(Customer.id)
        ).group_by('month').order_by(func.min(Customer.created_date)).limit(6).all()
        
        # Format for Chart.js
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
        ).group_by(Order.work_status).all()
        
        # Initialize with 0
        pie_data = {'Working': 0, 'Ready to Deliver': 0, 'Delivered': 0}
        for status, count in status_counts:
            # Map old statuses if they exist
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
        
        # Upcoming Deliveries (Next 7 Days) - for middle section - Optimized
        next_week = today + timedelta(days=7)
        upcoming_deliveries_all = Order.query.options(joinedload(Order.customer)).filter(
            Order.delivery_date > today,
            Order.delivery_date <= next_week,
            Order.work_status != 'Delivered'
        ).order_by(Order.delivery_date.asc()).limit(20).all() 
        
        upcoming_deliveries = [o for o in upcoming_deliveries_all if not (o.items and o.items[0].get('name') == "Previous Balance Due")][:5]

        # Top Customers (by Revenue) - Optimized Query
        # Using db.session.query enables explicit join control
        top_customers = db.session.query(
            Customer, func.sum(Order.total_amt).label('total_spend')
        ).join(Order).group_by(Customer.id).order_by(text('total_spend DESC')).limit(5).all()
        
        return render_template('dashboard.html', stats=stats, todays_orders=todays_orders, urgent_reminders=urgent_reminders, upcoming_deliveries=upcoming_deliveries, top_customers=top_customers, active_page='dashboard')

    @app.route('/customers', methods=['GET', 'POST'])
    @login_required
    def customers():
        if request.method == 'POST':
            # Quick Add Customer Logic
            name = request.form.get('name')
            mobile = request.form.get('mobile')
            gender = request.form.get('gender')
            
            if name and mobile:
                new_cust = Customer(
                    name=name, 
                    mobile=mobile, 
                    gender=gender, 
                    city=request.form.get('city'),
                    area=request.form.get('area'),
                    notes=request.form.get('notes')
                )
                db.session.add(new_cust)
                try:
                    db.session.commit()
                    # Removed auto-redirect to measurements
                    flash('Customer added successfully!', 'success')
                except Exception as e:
                    print(e)
                    db.session.rollback()
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
        # We fetch full objects but SQLAlchemy will be optimized by loading only what we access if defer() is used, 
        # OR we just select fields. For ease of use with template (rendering objects), we query Model but optimize relationships.
        query = Customer.query.options(
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
                query = query.filter(Customer.orders.any(Order.balance > 0)) # Subquery
            elif status_filter == 'paid':
                # Customers with orders where sum(balance) <= 0 or no orders? 
                # Simplification: Customers NOT having pending orders (approx)
                query = query.filter(~Customer.orders.any(Order.balance > 0))

        # 4. Standard Pagination
        page = request.args.get('page', 1, type=int)
        per_page = 50
        
        query = query.order_by(Customer.last_visit.desc(), Customer.id.desc())
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        customers_list = pagination.items

        # 5. Optimize N+1 (Fetch Stats for these 50)
        if customers_list:
            cust_ids = [c.id for c in customers_list]
            
            # Count Orders
            from sqlalchemy import func
            order_counts = db.session.query(Order.customer_id, func.count(Order.id))\
                .filter(Order.customer_id.in_(cust_ids))\
                .group_by(Order.customer_id).all()
            count_map = {r[0]: r[1] for r in order_counts}
            
            # Sum Balance
            balance_sums = db.session.query(Order.customer_id, func.sum(Order.balance))\
                .filter(Order.customer_id.in_(cust_ids))\
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
        meas = Measurement.query.get_or_404(id)
        return jsonify({
            "id": meas.id,
            "category_id": meas.category_id,
            "data": meas.measurements_json,
            "remarks": meas.remarks
        })

    @app.route('/api/customer/<int:id>')
    @login_required
    def api_customer_details(id):
        customer = Customer.query.get_or_404(id)
        
        # Serialize Measurements
        measurements_data = []
        for m in customer.measurements:
            measurements_data.append({
                "id": m.id,
                "category": m.category.name if m.category else "Unknown",
                "date": m.date.strftime('%d-%b-%Y'),
                "remarks": m.remarks or "",
                "data": m.measurements_json # Already valid JSON/Dict if using SQLAlchemy JSON type properly, else might need parsing
            })
            
        return jsonify({
            "id": customer.id,
            "name": customer.name,
            "mobile": customer.mobile,
            "gender": customer.gender,
            "city": "Ahmedabad", # Placeholder or add to model
            "total_pending": customer.total_pending,
            "measurements": measurements_data,
            "orders_count": len(customer.orders)
        })

    @app.route('/customer/<int:id>/measurement', methods=['GET', 'POST'])
    @login_required
    def measurement(id):
        customer = Customer.query.get_or_404(id)
        # Fetch categories based on gender (or all if not specified, but usually gender specific)
        categories = Category.query.filter_by(gender=customer.gender.lower()).all()

        if request.method == 'POST':
            # Save Measurement
            cat_id = request.form.get('category_id')
            measurements_data = request.form.get('measurements_json') # JSON string from frontend
            remarks = request.form.get('remarks')
            
            if cat_id and measurements_data:
                # In a real app, parse the JSON
                import json
                try:
                    m_json = json.loads(measurements_data)
                    new_meas = Measurement(
                        customer_id=id,
                        category_id=cat_id,
                        measurements_json=m_json,
                        remarks=remarks
                    )
                    db.session.add(new_meas)
                    db.session.flush() # Get ID
                    
                    app.logger.info(f"Measurement ID {new_meas.id} created/flushed.")
                    
                    app.logger.info(f"Measurement ID {new_meas.id} created/flushed.")
                    
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
                    
                    delivery_date = datetime.strptime(delivery_date_str, '%Y-%m-%d').date() if delivery_date_str else None
                    
                    # Fetch Category Name for Item Description
                    category = Category.query.get(cat_id)
                    item_name = category.name if category else "Custom Tailoring"

                    new_order = Order(
                        customer_id=id,
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
                        created_by=current_user.id
                    )
                    # Note: We are now setting Total Amt if provided.
                    
                    db.session.add(new_order)
                    db.session.commit()
                    flash('Measurement and Order created successfully!', 'success')
                    return redirect(url_for('orders'))

                except Exception as e:
                    print(e)
                    db.session.rollback()
                    flash('Error saving measurement', 'error')
            
            return redirect(url_for('customers'))

        return render_template('measurement.html', customer=customer, categories=categories, active_page='customers')

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
        # Eager Load Customer and Category to fix N+1
        query = Measurement.query.options(
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
        customer = Customer.query.get_or_404(id)
        # Fetch all measurements for this customer, sorted by newest first
        measurements = Measurement.query.filter_by(customer_id=id).order_by(Measurement.date.desc()).all()
        return render_template('measurement_history.html', customer=customer, measurements=measurements)

    @app.route('/orders', methods=['GET'])
    @login_required
    def orders():
        from datetime import datetime
        import calendar

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
        
        # Apply Date Filter (Override 'date' param if Month filter is active by default logic)
        # Assuming user wants "This Month's Customers" primarily
        from sqlalchemy import func
        
        # New: Delivery Date Filter (Overrides month filter)
        delivery_date_param = request.args.get('delivery_date')
        if delivery_date_param:
            if delivery_date_param == 'today':
                filter_date = datetime.today().date()
                query = Order.query.filter(Order.delivery_date == filter_date)
            else:
                try:
                    filter_date = datetime.strptime(delivery_date_param, '%Y-%m-%d').date()
                    query = Order.query.filter(Order.delivery_date == filter_date)
                except:
                    # Fallback to month filter if invalid
                    query = Order.query.filter(Order.created_at >= start_date, Order.created_at <= end_date)
        else:
             query = Order.query.filter(Order.created_at >= start_date, Order.created_at <= end_date)
        
        # Exclude 'Previous Balance Due' if needed (though date filter normally handles this if they are old)
        # However, for robustness, we can filter them out if they don't belong in the "Orders" list view
        # query = query.filter(Order.items... complex JSON check difficult in SQLite/Postgres cleanly without native JSON operators sometimes)
        # Let's rely on date for now.
        
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
            
            order = Order.query.get_or_404(order_id)
            
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

    # Keep bills_update for backward compat if needed, or redirect it?
    # Let's keep it but ensure it doesn't overwrite status with 'Paid' if we can help it.
    # Actually, bills page might still use it. I should probably update bills page later.
    # For now, let's focus on Orders page using the NEW route.


    @app.route('/delete/customer/<int:id>')
    @login_required
    def delete_customer(id):
        if not current_user.has_permission('delete_customer'):
            flash('Permission denied: Delete Customer', 'error')
            return redirect(url_for('customers'))
            
        try:
            cust = Customer.query.get_or_404(id)
            
            # Manually delete related records to avoid FK constraint errors
            # 1. Measurements
            Measurement.query.filter_by(customer_id=id).delete()
            # 2. Orders (and their reminders if any? Reminders linked to orders need care, but if we delete order, we might need to delete its reminders too)
            # Actually, Reminders are linked to Customer AND Order.
            # 3. Reminders
            if 'Reminder' in globals():
                 Reminder.query.filter_by(customer_id=id).delete()
            
            # Delete Orders (after reminders)
            Order.query.filter_by(customer_id=id).delete()
            
            # Finally delete customer
            db.session.delete(cust)
            db.session.commit()
            flash('Customer deleted successfully.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting customer: {str(e)}', 'danger')
        return redirect(url_for('customers'))

    @app.route('/delete/order/<int:id>')
    @login_required
    def delete_order(id):
        if not current_user.has_permission('delete_bill'):
            flash('Permission denied: Delete Bill', 'error')
            return redirect(url_for('orders'))
            
        try:
            order = Order.query.get_or_404(id)
            db.session.delete(order)
            db.session.commit()
            flash('Order deleted successfully.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting order: {str(e)}', 'danger')
        return redirect(url_for('orders'))

    
    @app.route('/bills')
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
        
        # Apply Date Filter (Override 'date' param if Month filter is active by default logic)
        # Assuming user wants "This Month's Customers" primarily
        from sqlalchemy import func
        query = Order.query.filter(Order.created_at >= start_date, Order.created_at <= end_date)
        
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
        
        order = Order.query.get_or_404(order_id)
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
    @master_required
    def reset_data():
        # DANGEROUS: Clear all data except Users and ShopProfile? or just transactional data?
        # Let's clear transactional data: Orders, Measurements, Customers (maybe?)
        # User requested "Reset System", usually implies fresh start for testing.
        try:
            # Delete in order of dependencies
            db.session.query(Order).delete()
            db.session.query(Measurement).delete()
            # db.session.query(Customer).delete() # Keeping customers might be safer? No, usually "Reset" means all.
            # However, deleting customers might break fk if not careful.
            
            # For now, let's keep it safe: Clear Orders and Measurements only?
            # Or ask user? The user said "Reset System".
            # Let's clear Orders and Measurements (Transactional). And Customers.
            # But keep Categories, Users, ShopProfile.
            
            if 'Reminder' in globals():
                 db.session.query(Reminder).delete()
            
            db.session.query(Order).delete()
            db.session.query(Measurement).delete()
            db.session.query(Customer).delete()
            
            db.session.commit()
            flash('System Data (Orders, Customers, Measurements) has been reset.', 'warning')
        except Exception as e:
            db.session.rollback()
            flash(f'Error resetting data: {str(e)}', 'danger')
        return redirect(url_for('settings'))

    @app.route('/reminders')
    @login_required
    def reminders():
        from datetime import date, timedelta
        
        today = date.today()
        tomorrow = today + timedelta(days=1)
        
        # 1. Urgent / Overdue Deliveries (Due <= Today AND Not Delivered)
        urgent_orders = Order.query.filter(
            Order.delivery_date <= today, 
            Order.work_status != 'Delivered'
        ).order_by(Order.delivery_date.asc()).all()
        
        # 2. Upcoming Deliveries (Tomorrow)
        upcoming_orders = Order.query.filter(
            Order.delivery_date == tomorrow,
            Order.work_status != 'Delivered'
        ).all()
        
        # 3. Pending Payments (Orders with Balance > 0)
        pending_payments = Order.query.filter(Order.balance > 0).order_by(Order.balance.desc()).limit(10).all()
        
        return render_template('reminders.html', 
                             urgent_orders=urgent_orders, 
                             upcoming_orders=upcoming_orders,
                             pending_payments=pending_payments,
                             active_page='reminders')
        

    @app.route('/search')
    @login_required
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

    @app.route('/invoice/<int:id>')
    @login_required
    def view_invoice(id):
        order = Order.query.get_or_404(id)
        from models import ShopProfile
        shop = ShopProfile.query.first() or ShopProfile()
        return render_template('invoice.html', order=order, shop=shop)

    @app.route('/invoice/<int:id>/download')
    @login_required
    def download_invoice(id):
        import os
        from flask import send_file
        from datetime import datetime
        
        order = Order.query.get_or_404(id)
        from models import ShopProfile
        shop = ShopProfile.query.first() or ShopProfile()
        
        # Render HTML
        html_content = render_template('invoice.html', order=order, shop=shop, download_mode=True)
        
        # 1. Determine Folder Path: saved_bills / YYYY / Month
        # User requested: "year folder under month folder" -> usually means Year > Month
        year_str = order.created_at.strftime('%Y')
        month_str = order.created_at.strftime('%B') # Full month name e.g. December
        
        folder = os.path.join(app.root_path, 'saved_bills', year_str, month_str)
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
        
    @app.route('/export_csv')
    @login_required
    def export_csv():
        import csv
        import io
        from flask import make_response
        
        # Export Orders Data
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow(['Order ID', 'Date', 'Customer Name', 'Mobile', 'Items', 'Total Amount', 'Advance', 'Balance', 'Status', 'Payment Mode'])
        
        orders = Order.query.order_by(Order.created_at.desc()).all()
        
        for order in orders:
            # Filter out opening balances if needed, or include them with clear label
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
            # Adjust end_date to include the full day
            end_date = end_date.replace(hour=23, minute=59, second=59)
        except ValueError:
            flash('Invalid date format.', 'error')
            return redirect(url_for('settings'))

        si = io.StringIO()
        writer = csv.writer(si)
        
        filename = f"{data_type.capitalize()}_{start_date.strftime('%d-%m-%Y')}_to_{end_date.strftime('%d-%m-%Y')}.csv"
        
        if data_type == 'orders':
            orders = Order.query.filter(Order.created_at >= start_date, Order.created_at <= end_date).all()
            writer.writerow(['Order ID', 'Customer Name', 'Mobile', 'Items', 'Total Amount', 'Advance', 'Balance', 'Status', 'Date'])
            for o in orders:
                items_str = ", ".join([f"{i['name']} (x{i['qty']})" for i in (o.items or [])])
                writer.writerow([o.id, o.customer.name, o.customer.mobile, items_str, o.total_amt, o.advance, o.balance, o.work_status, o.created_at.strftime('%Y-%m-%d')])
                
        elif data_type == 'customers':
            # Filter by created_date if available, or just dump all if date logic ambiguous? 
            # User asked "file name on date to date according". Assuming filtering by creation date.
            customers = Customer.query.filter(Customer.created_date >= start_date, Customer.created_date <= end_date).all()
            writer.writerow(['ID', 'Name', 'Mobile', 'City', 'Total Orders', 'Pending Balance', 'Joined Date'])
            for c in customers:
                writer.writerow([c.id, c.name, c.mobile, c.city, len(c.orders), c.total_pending, c.created_date.strftime('%Y-%m-%d')])

        elif data_type == 'measurements':
            measurements = Measurement.query.filter(Measurement.date >= start_date, Measurement.date <= end_date).all()
            writer.writerow(['ID', 'Customer', 'Mobile', 'Category', 'Date', 'Details'])
            for m in measurements:
                details = str(m.measurements_json)
                writer.writerow([m.id, m.customer.name, m.customer.mobile, m.category.name, m.date.strftime('%Y-%m-%d'), details])
        
        elif data_type == 'bills':
            # Bills essentially Orders but focus on financials
            orders = Order.query.filter(Order.created_at >= start_date, Order.created_at <= end_date).all()
            writer.writerow(['Bill No', 'Date', 'Customer', 'Mobile', 'Total Amount', 'Received', 'Balance', 'Payment Mode'])
            for o in orders:
                writer.writerow([o.id, o.created_at.strftime('%d-%m-%Y'), o.customer.name, o.customer.mobile, o.total_amt, o.advance, o.balance, o.payment_mode])

        csv_content = si.getvalue()
        
        # Save to Server Folder: csv_data/[type]/
        import os
        save_folder = os.path.join(app.root_path, 'csv_data', data_type)
        if not os.path.exists(save_folder):
             os.makedirs(save_folder)
             
        save_path = os.path.join(save_folder, filename)
        with open(save_path, 'w', newline='', encoding='utf-8') as f:
            f.write(csv_content)

        output = make_response(csv_content)
        output.headers["Content-Disposition"] = f"attachment; filename={filename}"
        output.headers["Content-type"] = "text/csv"
        return output

    @app.route('/api/customer/<int:id>')
    @login_required
    def get_customer_details(id):
        # Optimized query with joined load for measurements
        customer = Customer.query.options(db.joinedload(Customer.measurements).joinedload(Measurement.category)).get_or_404(id)
        
        # Prepare measurements data
        measurements_data = []
        for m in customer.measurements:
            measurements_data.append({
                'id': m.id,
                'category': m.category.name,
                'date': m.date.strftime('%d-%b-%Y'),
                'data': m.measurements_json,
                'remarks': m.remarks
            })
            
        return jsonify({
            'id': customer.id,
            'name': customer.name,
            'mobile': customer.mobile,
            'gender': customer.gender.capitalize() if customer.gender else '-',
            'total_pending': getattr(customer, 'total_pending_opt', 0), # Using the hybrid property or optimized field
            'orders_count': len(customer.orders),
            'measurements': measurements_data
        })
