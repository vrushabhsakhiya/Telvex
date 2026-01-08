try:
    from app import create_app
    print("Importing create_app successful")
    app = create_app()
    print("App created successfully")
    with app.app_context():
        from models import db
        print("Models imported")
except Exception as e:
    import traceback
    traceback.print_exc()
