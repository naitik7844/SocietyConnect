import os
import sys
import pymysql
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = int(os.environ.get('DB_PORT', '3306'))
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
DB_NAME = os.environ.get('DB_NAME', 'society_management')

def init_db():
    print(f"Connecting to MySQL server at {DB_HOST}:{DB_PORT} as {DB_USER}...")
    
    # Connect without database first to create it
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            autocommit=True
        )
    except Exception as e:
        print(f"Error connecting to MySQL: {e}")
        print("Please check your .env file and ensure MySQL is running.")
        return False

    try:
        with connection.cursor() as cursor:
            # Recreate Database for a fresh start
            print(f"Dropping database '{DB_NAME}' if exists for clean seed...")
            cursor.execute(f"DROP DATABASE IF EXISTS {DB_NAME};")
            print(f"Creating database '{DB_NAME}'...")
            cursor.execute(f"CREATE DATABASE {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            
            # Select Database
            cursor.execute(f"USE {DB_NAME};")
            
            # Read and execute schema.sql
            schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
            print(f"Reading schema from {schema_path}...")
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
                
            # Strip comments and execute queries
            schema_lines = [line for line in schema_sql.split('\n') if not line.strip().startswith('--')]
            queries = '\n'.join(schema_lines).split(';')
            for query in queries:
                cleaned_query = query.strip()
                if cleaned_query:
                    cursor.execute(cleaned_query)
            
            print("Schema initialized successfully.")
            
            # Read and execute seed.sql (Roles seed only)
            seed_path = os.path.join(os.path.dirname(__file__), 'seed.sql')
            print(f"Reading seed data from {seed_path}...")
            with open(seed_path, 'r', encoding='utf-8') as f:
                seed_sql = f.read()
                
            seed_lines = [line for line in seed_sql.split('\n') if not line.strip().startswith('--')]
            queries = '\n'.join(seed_lines).split(';')
            for query in queries:
                cleaned_query = query.strip()
                if cleaned_query:
                    cursor.execute(cleaned_query)
                    
            print("Role seeds loaded successfully.")

            # Programmatically seed Buildings (Tower A to J)
            towers = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
            print("Generating towers A to J and corresponding wing flats (e.g. A1-101 to J4-404)...")
            
            for b_id, t in enumerate(towers, start=1):
                cursor.execute(
                    "INSERT INTO buildings (id, name, description, floors_count) VALUES (%s, %s, %s, %s);",
                    (b_id, f"Tower {t}", f"Residential Tower {t}", 4)
                )
                
                # Seed flats dynamically: Wing 1-4, Floor 1-4, Flat 1-4 per floor
                for wing_num in [1, 2, 3, 4]:
                    wing_label = f"{t}{wing_num}"
                    for floor in [1, 2, 3, 4]:
                        for num in [1, 2, 3, 4]:
                            flat_label = f"{wing_label}-{floor}0{num}"
                            cursor.execute(
                                "INSERT INTO flats (building_id, flat_number, floor_number, flat_type, occupancy_status) VALUES (%s, %s, %s, %s, %s);",
                                (b_id, flat_label, floor, '2BHK', 'Vacant')
                            )
            print("All Towers and Flats generated completely.")
            
            # Create default Admin and Security users if they don't exist
            cursor.execute("SELECT id FROM users WHERE username = 'admin';")
            if not cursor.fetchone():
                admin_pass = generate_password_hash('admin123')
                cursor.execute(
                    "INSERT INTO users (username, email, password_hash, phone, role_id, status) VALUES (%s, %s, %s, %s, %s, %s);",
                    ('admin', 'admin@societyconnect.com', admin_pass, '1234567890', 1, 'Active')
                )
                print("Default Admin user created (username: admin, password: admin123).")
                
            cursor.execute("SELECT id FROM users WHERE username = 'security';")
            if not cursor.fetchone():
                security_pass = generate_password_hash('security123')
                cursor.execute(
                    "INSERT INTO users (username, email, password_hash, phone, role_id, status) VALUES (%s, %s, %s, %s, %s, %s);",
                    ('security', 'security@societyconnect.com', security_pass, '0987654321', 4, 'Active')
                )
                print("Default Security user created (username: security, password: security123).")

            cursor.execute("SELECT id FROM users WHERE username = 'resident';")
            if not cursor.fetchone():
                resident_pass = generate_password_hash('resident123')
                cursor.execute(
                    "INSERT INTO users (username, email, password_hash, phone, role_id, status) VALUES (%s, %s, %s, %s, %s, %s);",
                    ('resident', 'resident@societyconnect.com', resident_pass, '5555555555', 3, 'Active')
                )
                # Link resident to Flat A1-101 of Tower A (building_id = 1)
                cursor.execute("SELECT id FROM users WHERE username = 'resident';")
                res_user_id = cursor.fetchone()[0]
                cursor.execute("SELECT id FROM flats WHERE building_id = 1 AND flat_number = 'A1-101';")
                flat_row = cursor.fetchone()
                if flat_row:
                    flat_id = flat_row[0]
                    cursor.execute(
                        "INSERT INTO residents (user_id, flat_id, resident_type, emergency_contact, move_in_date) VALUES (%s, %s, %s, %s, CURDATE());",
                        (res_user_id, flat_id, 'Tenant', '9999999999')
                    )
                    # Update flat occupancy status
                    cursor.execute(
                        "UPDATE flats SET occupancy_status = 'Tenant-Occupied' WHERE id = %s;",
                        (flat_id,)
                    )
                print("Default Resident user created (username: resident, password: resident123) linked to Tower A - Flat A1-101.")

    except Exception as e:
        print(f"Error during DB initialization: {e}")
        return False
    finally:
        connection.close()
        
    print("Database initialization complete.")
    return True

if __name__ == '__main__':
    init_db()
