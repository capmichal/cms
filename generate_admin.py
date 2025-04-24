from app import app, db, User
from werkzeug.security import generate_password_hash

# Create application context
app.app_context().push()

# Create admin user
admin = User(
    username='admin',
    password_hash=generate_password_hash('admin123')  # Change 'admin123' to your desired password
)

# Add to database
db.session.add(admin)
db.session.commit()
