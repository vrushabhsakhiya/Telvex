from flask import Flask
from config import Config
from models import db
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

csrf = CSRFProtect()
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_talisman import Talisman
from datetime import timedelta

csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address)
migrate = Migrate()
login_manager = LoginManager()
talisman = Talisman()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize Plugins
    # Initialize Plugins
    db.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    # Talisman (HTTPS) - Disable in Debug/Local if needed, or configure content_security_policy
    if not app.debug:
        talisman.init_app(app, content_security_policy=None) # CSP can be strict, set None for now to avoid breaking scripts
    
    # Session Config
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=9)
    app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-prod' # Ensure this is set

    login_manager.login_view = 'login'

    # --- I18n / Translations ---
    translations = {
        'en': {
            'dashboard': 'Dashboard',
            'customers': 'Customers',
            'orders': 'Orders',
            'bills': 'Bills',
            'measurements': 'Measurements',
            'reminders': 'Reminders',
            'users': 'Users',
            'history': 'History',
            'settings': 'Control',
            'sign_out': 'Sign Out',
            'total_customers': 'Total Customers',
            'all_time_revenue': 'All Time Revenue',
            'pending_balance': 'Pending Balance',
            'due_today': 'Due Today',
            'recent_activity': 'Recent Activity',
            'today_customers': 'Today',
            'this_week': 'This Week',
            # Common
            'name': 'Name',
            'mobile': 'Mobile',
            'status': 'Status',
            'date': 'Date',
            'actions': 'Actions',
            'search': 'Search',
            'add_new': 'Add New',
            'delete': 'Delete',
            'edit': 'Edit',
            'save': 'Save',
            'cancel': 'Cancel',
            'id': 'ID',
            'photo': 'Photo',
            'gender': 'Gender',
            # Customers
            'last_visit': 'Last Visit',
            'total_orders': 'Total Orders',
            'male': 'Male',
            'female': 'Female',
            'all_paid': 'All Paid',
            # Orders
            'order_id': 'Order ID',
            'delivery_date': 'Delivery Date',
            'items': 'Items',
            'total_amount': 'Total Amount',
            'advance': 'Advance',
            'balance': 'Balance',
            'worker': 'Worker',
            'delivered': 'Delivered',
            'working': 'Working',
            'cancelled': 'Cancelled',
            'Monthly Customers':'Monthly Customers',
            # Custom Categories
            'category': 'Category',
            'custom_categories': 'Custom Categories',
            'manage_categories_info': 'Manage your measurement categories and app preferences.',
            'gents_wear': "Gent's Wear",
            'ladies_wear': "Ladies' Wear",
            'add_category': 'Add Category',
            'no_gents_items': "No Gent's items added yet. Click \"Add Category\" to start.",
            'no_ladies_items': "No Ladies' items added yet. Click \"Add Category\" to start.",
            'add_new_category': 'Add New Category',
            'category_name': 'Category Name',
            'category_placeholder': 'e.g. Waistcoat, Blazer',
            'category_help': 'Name of the clothing item (e.g. Shirt, Pant)',
            'measurement_fields': 'Measurement Fields',
            'what_do_you_measure': 'What do you measure?',
            'part_name_placeholder': 'Part name (e.g. Length)',
            'add': 'Add',
            # Bills
            'bills_and_payments': 'Bills & Payments',
            'search_name_mobile': 'Search Name or Mobile...',
            'all_genders': 'All Genders',
            'balance_all': 'Balance: All',
            'bill_id': 'Bill ID',
            'customer': 'Customer',
            'total_bill': 'Total Bill',
            'advance_payment': 'Advance Payment',
            'pending_payment': 'Pending Payment',
            'payment_status': 'Payment Status',
            'action': 'Action',
            'no_bills_found': 'No bills found.',
            'showing_page': 'Showing page',
            'go_to': 'Go to',
            'prev': 'Prev',
            'next': 'Next',
            # Customers
            'add_new_customer': 'Add New Customer',
            'clothes_status': 'Clothes Status',
            'no_data_yet': 'No data yet.',
            # Orders
            'no_orders_found': 'No orders found.',
            'no_upcoming_deliveries': 'No upcoming deliveries.',
            # Measurement History
            'measurements_history': 'Measurements History',
            'no_measurements_found': 'No measurements found for this month.',
            # Dashboard
            'yearly_overview': 'Yearly Overview',
            'monthly_report': 'Monthly Report',
            'monthly_customers': 'Monthly Customers',
            'monthly_pending': 'Monthly Pending',
            'monthly_revenue': 'Monthly Revenue',
            'urgent_reminders': 'Urgent Reminders',
            'upcoming_deliveries': 'Upcoming Deliveries',
            'next_7_days': 'Next 7 Days',
            'top_customers': 'Top Customers',
            'today_customers': "Today's Customers",
            'no_orders_today': 'No orders created today.',
            'view': 'View',
            'pending_delivery': 'Pending Delivery',
            'this_month': 'This Month',
            'total_outstanding': 'Total Outstanding',
            # Reminders
            'reminders_activity': 'Reminders & Activity',
            'urgent_today': 'Urgent / Today',
            'no_urgent_deliveries': 'No urgent deliveries.',
            'tomorrow': 'Tomorrow',
            'due_tomorrow': 'Due: Tomorrow',
            'no_deliveries_tomorrow': 'No deliveries tomorrow.',
            'pending_payments': 'Pending Payments',
            'no_pending_payments': 'No pending payments.',
            'go_to_bills': 'Go to Bills',
            'due': 'Due',
            # Settings
            'manage_app_prefs': 'Manage your app preferences.',
            'shop_profile': 'Shop Profile',
            'shop_logo': 'Shop Logo',
            'keep_current_logo': 'Leave empty to keep current logo',
            'delete_current_logo': 'Delete Current Logo',
            'shop_name': 'Shop Name',
            'shop_contact_no': 'Shop Contact No.',
            'gst_reg_no': 'GST / Reg No.',
            'optional': 'Optional',
            'address': 'Address',
            'full_shop_address': 'Full Shop Address',
            'bill_terms': 'Bill Terms & Conditions',
            'terms_placeholder': 'Terms printed on bottom of bill...',
            'save_profile': 'Save Profile',
            'data_management': 'Data Management',
            'from_date': 'From Date',
            'to_date': 'To Date',
            'data_type': 'Data Type',
            'download_data': 'Download Data',
            'reset_system_data': 'Reset System Data',
            'reset_warning': 'WARNING: This will delete ALL Customers, Orders, and Measurements. This action cannot be undone. Are you sure?',
            # Forms & Extra
            'full_name': 'Full Name',
            'name_placeholder': 'e.g. Rajesh Patel',
            'mobile_number': 'Mobile Number',
            'city': 'City',
            'area': 'Area',
            'note_reference': 'Note / Reference',
            'save_customer': 'Save Customer',
            'new_measurement': 'New Measurement',
            'manage_order': 'Manage Order',
            'delivery_status': 'Delivery Status',
            'work_status': 'Work Status',
            'paid_amount': 'Paid Amount',
            'mark_full_paid': 'Mark Full Paid',
            'balance_due': 'Balance Due',
            'payment_mode': 'Payment Mode',
            'update_order': 'Update Order',
            'cash': 'Cash',
            'card': 'Card',
            'online_upi': 'Online / UPI',
            'bank_transfer': 'Bank Transfer',
            'status_pending': 'Pending',
            'status_processing': 'Processing',
            'status_ready': 'Ready to Deliver',
            'status_delivered': 'Delivered',
            'bill_created_by': 'Bill Created By',
            'bill_created_by_names': 'Bill Creator Names (Staff)',
            'bill_creators_placeholder': 'e.g. Rahul, Priya, System',
            'bill_creators_help': 'Enter names separated by comma. These will appear in the Bill Created By dropdown.'
        },
        'hi': {
            'dashboard': 'डैशबोर्ड',
            'customers': 'ग्राहक',
            'orders': 'ऑर्डर',
            'bills': 'बिल',
            'measurements': 'माप',
            'reminders': 'रिमाइंडर',
            'users': 'कर्मचारी',
            'history': 'इतिहास',
            'settings': 'सेटिंग्स',
            'sign_out': 'साइन आउट',
            'total_customers': 'कुल ग्राहक',
            'all_time_revenue': 'कुल कमाई',
            'pending_balance': 'बकाया राशि',
            'due_today': 'आज की डिलीवरी',
            'recent_activity': 'हाल की गतिविधि',
            'today_customers': 'आज के ग्राहक',
            'this_week': 'इस सप्ताह',
            # Common
            'name': 'नाम',
            'mobile': 'मोबाइल',
            'status': 'स्थिति',
            'date': 'दिनांक',
            'actions': 'क्रियाएँ',
            'search': 'खोजें',
            'add_new': 'नया जोड़ें',
            'delete': 'हटाएं',
            'edit': 'संपादित करें',
            'save': 'सहेजें',
            'cancel': 'रद्द करें',
            'id': 'आईडी',
            'photo': 'फोटो',
            'gender': 'लिंग',
            # Customers
            'last_visit': 'अंतिम विजिट',
            'total_orders': 'कुल ऑर्डर',
            'male': 'पुरुष',
            'female': 'महिला',
            'all_paid': 'पूर्ण भुगतान',
            # Orders
            'order_id': 'ऑर्डर आईडी',
            'delivery_date': 'डिलीवरी दिनांक',
            'items': 'आइटम',
            'total_amount': 'कुल राशि',
            'advance': 'एडवांस',
            'balance': 'बकाया',
            'worker': 'कारीगर',
            'delivered': 'डिलीवर किया',
            'working': 'कार्य प्रगति पर',
            'cancelled': 'रद्द',
            'Monthly Customers':'मासिक ग्राहक',
            # Custom Categories
            'category': 'श्रेणी',
            'custom_categories': 'कस्टम श्रेणियां',
            'manage_categories_info': 'अपनी माप श्रेणियां और ऐप प्राथमिकताएं प्रबंधित करें।',
            'gents_wear': 'पुरुष परिधान',
            'ladies_wear': 'महिला परिधान',
            'add_category': 'श्रेणी जोड़ें',
            'no_gents_items': 'अभी तक कोई पुरुष आइटम नहीं जोड़ा गया। शुरू करने के लिए "श्रेणी जोड़ें" पर क्लिक करें।',
            'no_ladies_items': 'अभी तक कोई महिला आइटम नहीं जोड़ा गया। शुरू करने के लिए "श्रेणी जोड़ें" पर क्लिक करें।',
            'add_new_category': 'नई श्रेणी जोड़ें',
            'category_name': 'श्रेणी का नाम',
            'category_placeholder': 'जैसे: वेस्टकोट, ब्लेज़र',
            'category_help': 'कपड़े का नाम (जैसे: शर्ट, पैंट)',
            'measurement_fields': 'माप के क्षेत्र',
            'what_do_you_measure': 'आप क्या मापते हैं?',
            'part_name_placeholder': 'भाग का नाम (जैसे: लंबाई)',
            'add': 'जोड़ें',
            'type_above_enter': 'ऊपर लिखें और एन्टर दबाएं',
            # Bills
            'bills_and_payments': 'बिल और भुगतान',
            'search_name_mobile': 'नाम या मोबाइल खोजें...',
            'all_genders': 'सभी लिंग',
            'balance_all': 'बकाया: सभी',
            'bill_id': 'बिल आईडी',
            'customer': 'ग्राहक',
            'total_bill': 'कुल बिल',
            'advance_payment': 'अग्रिम भुगतान',
            'pending_payment': 'लंबित भुगतान',
            'payment_status': 'भुगतान स्थिति',
            'action': 'क्रिया',
            'no_bills_found': 'कोई बिल नहीं मिला।',
            'showing_page': 'पृष्ठ',
            'go_to': 'पर जाएं',
            'prev': 'पिछला',
            'next': 'अगला',
            # Customers (Extra)
            'add_new_customer': 'नया ग्राहक जोड़ें',
            'clothes_status': 'कपड़ों की स्थिति',
            'no_data_yet': 'अभी कोई डेटा नहीं।',
            # Orders (Extra)
            'no_orders_found': 'कोई ऑर्डर नहीं मिला।',
            'no_upcoming_deliveries': 'कोई आगामी डिलीवरी नहीं।',
             # Measurement History
            'measurements_history': 'माप इतिहास',
            'no_measurements_found': 'इस महीने कोई माप नहीं मिला।',
             # Dashboard
            'yearly_overview': 'वार्षिक अवलोकन',
            'monthly_report': 'मासिक रिपोर्ट',
            'monthly_customers': 'मासिक ग्राहक',
            'monthly_pending': 'मासिक बकाया',
            'monthly_revenue': 'मासिक राजस्व',
            'urgent_reminders': 'जरूरी रिमाइंडर',
            'upcoming_deliveries': 'आगामी डिलीवरी',
            'next_7_days': 'अगले 7 दिन',
            'top_customers': 'शीर्ष ग्राहक',
            'no_orders_today': 'आज कोई ऑर्डर नहीं बनाया गया।',
            'view': 'देखें',
            'pending_delivery': 'लंबित डिलीवरी',
            'this_month': 'इस महीने',
            'total_outstanding': 'कुल बकाया',
            # Reminders
            'reminders_activity': 'रिमाइंडर और गतिविधि',
            'urgent_today': 'जरूरी / आज',
            'no_urgent_deliveries': 'कोई जरूरी डिलीवरी नहीं।',
            'tomorrow': 'कल',
            'due_tomorrow': 'देय: कल',
            'no_deliveries_tomorrow': 'कल कोई डिलीवरी नहीं।',
            'pending_payments': 'लंबित भुगतान',
            'no_pending_payments': 'कोई लंबित भुगतान नहीं।',
            'go_to_bills': 'बिल पर जाएं',
            'due': 'देय',
            # Settings
            'manage_app_prefs': 'अपनी ऐप प्राथमिकताएं प्रबंधित करें।',
            'shop_profile': 'दुकान प्रोफ़ाइल',
            'shop_logo': 'दुकान का लोगो',
            'keep_current_logo': 'वर्तमान लोगो रखने के लिए खाली छोड़ दें',
            'delete_current_logo': 'वर्तमान लोगो हटाएं',
            'shop_name': 'दुकान का नाम',
            'shop_contact_no': 'दुकान संपर्क नंबर',
            'gst_reg_no': 'जीएसटी / पंजीकरण संख्या',
            'optional': 'वैकल्पिक',
            'address': 'पता',
            'full_shop_address': 'पुर्ण दुकान का पता',
            'bill_terms': 'बिल नियम और शर्तें',
            'terms_placeholder': 'बिल के नीचे मुद्रित शर्तें...',
            'save_profile': 'प्रोफ़ाइल सहेजें',
            'data_management': 'डेटा प्रबंधन',
            'from_date': 'दिनांक से',
            'to_date': 'दिनांक तक',
            'data_type': 'डेटा प्रकार',
            'download_data': 'डेटा डाउनलोड करें',
            'reset_system_data': 'सिस्टम डेटा रीसेट करें',
            'reset_warning': 'चेतावनी: यह सभी ग्राहकों, ऑर्डर और माप को हटा देगा। यह क्रिया पूर्ववत नहीं की जा सकती। क्या आप सुनिश्चित हैं?',
            # Forms & Extra
            'full_name': 'पूरा नाम',
            'name_placeholder': 'जैसे: राजेश पटेल',
            'mobile_number': 'मोबाइल नंबर',
            'city': 'शहर',
            'area': 'क्षेत्र / इलाका',
            'note_reference': 'नोट / संदर्भ',
            'save_customer': 'ग्राहक सहेजें',
            'new_measurement': 'नया माप',
            'manage_order': 'ऑर्डर प्रबंधित करें',
            'delivery_status': 'डिलीवरी स्थिति',
            'work_status': 'कार्य स्थिति',
            'paid_amount': 'भुगतान की गई राशि',
            'mark_full_paid': 'पूर्ण भुगतान चिह्नित करें',
            'balance_due': 'बकाया राशि',
            'payment_mode': 'भुगतान का प्रकार',
            'update_order': 'ऑर्डर अपडेट करें',
            'cash': 'नकद',
            'card': 'कार्ड',
            'online_upi': 'ऑनलाइन / यूपीआई',
            'bank_transfer': 'बैंक ट्रांसफर',
            'status_pending': 'लंबित',
            'status_processing': 'प्रक्रिया में',
            'status_ready': 'डिलीवरी के लिए तैयार',
            'status_delivered': 'डिलीवर किया गया',
            'bill_created_by': 'बिल किसके द्वारा बनाया गया',
            'bill_created_by_names': 'बिल निर्माता के नाम (स्टाफ)',
            'bill_creators_placeholder': 'जैसे: राहुल, प्रिया, सिस्टम',
            'bill_creators_help': 'नाम अल्पविराम (comma) से अलग करके दर्ज करें।'
        },
        'gu': {
            'dashboard': 'ડેશબોર્ડ',
            'customers': 'ગ્રાહકો',
            'orders': 'ઓર્ડર',
            'bills': 'બિલ',
            'measurements': 'માપ',
            'reminders': 'રિમાઇન્ડર',
            'users': 'વપરાશકર્તાઓ',
            'history': 'ઇતિહાસ',
            'settings': 'સેટિંગ્સ',
            'sign_out': 'લૉગ આઉટ',
            'total_customers': 'કુલ ગ્રાહકો',
            'all_time_revenue': 'કુલ આવક',
            'pending_balance': 'બાકી રકમ',
            'due_today': 'આજે આપવાનાં',
            'recent_activity': 'તાજેતરની પ્રવૃત્તિ',
            'today_customers': 'આજના ગ્રાહકો',
            'this_week': 'આ અઠવાડિયે',
            # Common
            'name': 'નામ',
            'mobile': 'મોબાઇલ',
            'status': 'સ્થિતિ',
            'date': 'તારીખ',
            'actions': 'ક્રિયાઓ',
            'search': 'શોધો',
            'add_new': 'નવું ઉમેરો',
            'delete': 'કાઢી નાખો',
            'edit': 'ફેરફાર કરો',
            'save': 'સાચવો',
            'cancel': 'રદ કરો',
            'id': 'આઈડી',
            'photo': 'ફોટો',
            'gender': 'લિંગ',
            # Customers
            'last_visit': 'છેલ્લી મુલાકાત',
            'total_orders': 'કુલ ઓર્ડર',
            'male': 'પુરુષ',
            'female': 'સ્ત્રી',
            'all_paid': 'બધું ચૂકવાઈ ગયું',
            # Orders
            'order_id': 'ઓર્ડર આઈડી',
            'delivery_date': 'ડિલિવરી તારીખ',
            'items': 'વસ્તુઓ',
            'total_amount': 'કુલ રકમ',
            'advance': 'એડવાન્સ',
            'balance': 'બાકી',
            'worker': 'કારીગર',
            'delivered': 'ડિલિવર થયું',
            'working': 'કામ ચાલુ',
            'cancelled': 'રદ થયેલ',
            'Monthly Customers':'માસિક ગ્રાહક',
            # Custom Categories
            'category': 'શ્રેણી',
            'custom_categories': 'કસ્ટમ શ્રેણીઓ',
            'manage_categories_info': 'તમારી માપ શ્રેણીઓ અને એપ્લિકેશન પસંદગીઓનું સંચાલન કરો.',
            'gents_wear': 'જેન્ટ્સ વેર',
            'ladies_wear': 'લેડીઝ વેર',
            'add_category': 'શ્રેણી ઉમેરો',
            'no_gents_items': 'હજી સુધી કોઈ જેન્ટ્સ આઈટમ ઉમેરવામાં આવી નથી. શરૂ કરવા માટે "શ્રેણી ઉમેરો" પર ક્લિક કરો.',
            'no_ladies_items': 'હજી સુધી કોઈ લેડીઝ આઈટમ ઉમેરવામાં આવી નથી. શરૂ કરવા માટે "શ્રેણી ઉમેરો" પર ક્લિક કરો.',
            'add_new_category': 'નવી શ્રેણી ઉમેરો',
            'category_name': 'શ્રેણીનું નામ',
            'category_placeholder': 'દા.ત. વેસ્ટકોટ, બ્લેઝર',
            'category_help': 'કપડાંનું નામ (દા.ત. શર્ટ, પેન્ટ)',
            'measurement_fields': 'માપન ક્ષેત્રો',
            'what_do_you_measure': 'તમે શું માપો છો?',
            'part_name_placeholder': 'ભાગનું નામ (દા.ત. લંબાઈ)',
            'add': 'ઉમેરો',
            'type_above_enter': 'ઉપર લખો અને એન્ટર દબાવો',
            # Bills
            'bills_and_payments': 'બિલ અને ચૂકવણી',
            'search_name_mobile': 'નામ અથવા મોબાઇલ શોધો...',
            'all_genders': 'બધા લિંગ',
            'balance_all': 'બાકી: બધા',
            'bill_id': 'બિલ આઈડી',
            'customer': 'ગ્રાહક',
            'total_bill': 'કુલ બિલ',
            'advance_payment': 'અગાઉથી ચૂકવણી',
            'pending_payment': 'બાકી ચૂકવણી',
            'payment_status': 'ચુકવણી સ્થિતિ',
            'action': 'ક્રિયા',
            'no_bills_found': 'કોઈ બિલ મળ્યા નથી.',
            'showing_page': 'પૃષ્ઠ',
            'go_to': 'પર જાઓ',
            'prev': 'પાછળ',
            'next': 'આગળ',
            # Customers (Extra)
            'add_new_customer': 'નવો ગ્રાહક ઉમેરો',
            'clothes_status': 'કપડાંની સ્થિતિ',
            'no_data_yet': 'હજુ સુધી કોઈ ડેટા નથી.',
            # Orders (Extra)
            'no_orders_found': 'કોઈ ઓર્ડર મળ્યા નથી.',
            'no_upcoming_deliveries': 'કોઈ આગામી ડિલિવરી નથી.',
             # Measurement History
            'measurements_history': 'માપનો ઇતિહાસ',
            'no_measurements_found': 'આ મહિના માટે કોઈ માપ મળ્યા નથી.',
             # Dashboard
            'yearly_overview': 'વાર્ષિક વિહંગાવલોકન',
            'monthly_report': 'માસિક અહેવાલ',
            'monthly_customers': 'માસિક ગ્રાહકો',
            'monthly_pending': 'માસિક બાકી',
            'monthly_revenue': 'માસિક આવક',
            'urgent_reminders': 'તાત્કાલિક રિમાઇન્ડર્સ',
            'upcoming_deliveries': 'આગામી ડિલિવરી',
            'next_7_days': 'આગામી 7 દિવસ',
            'top_customers': 'ટોચના ગ્રાહકો',
            'today_customers': 'આજના ગ્રાહકો',
            'no_orders_today': 'આજે કોઈ ઓર્ડર બનાવ્યો નથી.',
            'view': 'જુઓ',
            'pending_delivery': 'બાકી ડિલિવરી',
            'this_month': 'આ મહિને',
            'total_outstanding': 'કુલ બાકી',
             # Reminders
            'reminders_activity': 'રિમાઇન્ડર અને પ્રવૃત્તિ',
            'urgent_today': 'તાત્કાલિક / આજે',
            'no_urgent_deliveries': 'કોઈ તાત્કાલિક ડિલિવરી નથી.',
            'tomorrow': 'આવતીકાલે',
            'due_tomorrow': 'બાકી: આવતીકાલે',
            'no_deliveries_tomorrow': 'આવતીકાલે કોઈ ડિલિવરી નથી.',
            'pending_payments': 'બાકી ચૂકવણી',
            'no_pending_payments': 'કોઈ ચૂકવણી બાકી નથી.',
            'go_to_bills': 'બીલ પર જાઓ',
            'due': 'બાકી',
            # Settings
            'manage_app_prefs': 'તમારી એપ્લિકેશન પસંદગીઓનું મેનેજ કરો.',
            'shop_profile': 'દુકાન પ્રોફાઇલ',
            'shop_logo': 'દુકાનનો લોગો',
            'keep_current_logo': 'વર્તમાન લોગો રાખવા માટે ખાલી છોડો',
            'delete_current_logo': 'વર્તમાન લોગો કાઢી નાખો',
            'shop_name': 'દુકાનનું નામ',
            'shop_contact_no': 'દુકાન સંપર્ક નંબર',
            'gst_reg_no': 'જીએસટી / નોંધણી નંબર',
            'optional': 'વૈકલ્પિક',
            'address': 'સરનામું',
            'full_shop_address': 'દુકાનનું પૂરું સરનામું',
            'bill_terms': 'બિલના નિયમો અને શરતો',
            'terms_placeholder': 'બિલની નીચે છપાયેલી શરતો...',
            'save_profile': 'પ્રોફાઇલ સાચવો',
            'data_management': 'ડેટા મેનેજમેન્ટ',
            'from_date': 'તારીખથી',
            'to_date': 'તારીખ સુધી',
            'data_type': 'ડેટા પ્રકાર',
            'download_data': 'ડેટા ડાઉનલોડ કરો',
            'reset_system_data': 'સિસ્ટમ ડેટા રીસેટ કરો',
            'reset_warning': 'ચેતવણી: આ તમામ ગ્રાહકો, ઓર્ડર અને માપને કાઢી નાખશે. આ ક્રિયા રદ કરી શકાતી નથી. શું તમને ખાતરી છે?',
            # Forms & Extra
            'full_name': 'પૂરું નામ',
            'name_placeholder': 'દા.ત. રાજેશ પટેલ',
            'mobile_number': 'મોબાઇલ નંબર',
            'city': 'શહેર',
            'area': 'વિસ્તાર',
            'note_reference': 'નોંધ / સંદર્ભ',
            'save_customer': 'ગ્રાહક સાચવો',
            'new_measurement': 'નવું માપ',
            'manage_order': 'ઓર્ડર મેનેજ કરો',
            'delivery_status': 'ડિલિવરી સ્થિતિ',
            'work_status': 'કામની સ્થિતિ',
            'paid_amount': 'ચૂકવેલ રકમ',
            'mark_full_paid': 'સંપૂર્ણ ચૂકવેલ માર્ક કરો',
            'balance_due': 'બાકી લેણાં',
            'payment_mode': 'ચુકવણી પદ્ધતિ',
            'update_order': 'ઓર્ડર અપડેટ કરો',
            'cash': 'રોકડ',
            'card': 'કાર્ડ',
            'online_upi': 'ઓનલાઇન / યુપીઆઈ',
            'bank_transfer': 'બેંક ટ્રાન્સફર',
            'status_pending': 'બાકી',
            'status_processing': 'પ્રક્રિયામાં',
            'status_ready': 'ડિલિવરી માટે તૈયાર',
            'status_delivered': 'ડિલિવર થયું',
            'bill_created_by': 'બિલ કોણે બનાવ્યું',
            'bill_created_by_names': 'બિલ બનાવનારના નામ (સ્ટાફ)',
            'bill_creators_placeholder': 'દા.ત. રાહુલ, પ્રિયા, સિસ્ટમ',
            'bill_creators_help': 'અલ્પવિરામ (comma) દ્વારા અલગ કરીને નામ દાખલ કરો.'
        }
    }

    @app.context_processor
    def inject_i18n():
        from flask import session, request
        try:
            from googletrans import Translator
            translator = Translator()
        except ImportError:
            translator = None
            print("!!! Googletrans not installed")

        # Get lang from Query or Session, default 'en'
        lang = request.args.get('lang', session.get('lang', 'en'))
        session['lang'] = lang # Persist
        
        def t(key):
            # 1. Check if key exists in Target Language Dict
            if key in translations.get(lang, {}):
                return translations[lang][key]
            
            # 2. If 'en' (default), just return the key (assuming key is the English text)
            # OR if key is in 'en' dict, return that value
            en_val = translations['en'].get(key, key)
            
            if lang == 'en':
                return en_val

            # 3. If missing in Target Lang, try Google Translate (Dynamic Fallback)
            if translator:
                try:
                    # Check if we already cached this dynamic translation in memory
                    if key not in translations[lang]:
                         # Translate from English (en_val) to Target (lang)
                        translated = translator.translate(en_val, dest=lang).text
                        # Cache it so we don't hit API again this session
                        translations[lang][key] = translated
                        print(f"Translated '{en_val}' to {lang}: {translated}")
                    
                    return translations[lang][key]
                except Exception as e:
                    print(f"Translation Error for {key}: {e}")
                    return en_val # Fallback to English
            
            return en_val
        
        return dict(t=t, current_lang=lang)
    
    from models import mail
    mail.init_app(app)
    
    # Register Routes
    with app.app_context():
        from routes import register_routes
        register_routes(app)
        
        # Create DB Tables if they don't exist
        db.create_all()
        
        
        # --- Seed Data ---
        from models import Category
        if not Category.query.first():
            print("Seeding Categories...")
            categories = [
                Category(name='Shirt', gender='male', fields_json=['Length', 'Chest', 'Shoulder', 'Sleeve', 'Collar', 'Cuff']),
                Category(name='Pant', gender='male', fields_json=['Length', 'Waist', 'Seat', 'Thigh', 'Knee', 'Bottom']),
                Category(name='Kurta', gender='male', fields_json=['Length', 'Chest', 'Shoulder', 'Sleeve']),
                Category(name='Blouse', gender='female', fields_json=['Length', 'Chest', 'Waist', 'Shoulder', 'Sleeve', 'Front Depth', 'Back Depth']),
                Category(name='Kurti', gender='female', fields_json=['Length', 'Chest', 'Waist', 'Hip', 'Shoulder']),
                Category(name='Salwar', gender='female', fields_json=['Length', 'Waist', 'Hip', 'Bottom'])
            ]
            db.session.bulk_save_objects(categories)
            db.session.commit()




    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id))

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
