import mariadb
import sys,json


# Load database configuration
def load_db_config(config_file="/home/toor/watch/db_config.json"):
    try:
        with open(config_file, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading database configuration: {e}")
        sys.exit(1)


# Database connection
def connect_db():
    # Connect to MariaDB Platform
    config = load_db_config()
    try:
        conn = mariadb.connect(
            user=config["user"],
            password=config["password"],
            host=config["host"],
            port=3306,
            database=config["database"]
        )
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)

    # Get Cursor
    return conn


# Function to escape inputs to prevent SQL injection
def escape_input(connection, input_value):
    cursor = connection.cursor()
    query = f"SELECT QUOTE(%s)"
    cursor.execute(query, (input_value,))
    result = cursor.fetchone()[0]
    cursor.close()
    return result[1:-1]  # Strip the surrounding quotes


# Function to insert subdomain into the database
def insert_subdomain(connection, subdomain, table_name, subEnumCount):
    table_name = escape_input(connection, table_name)
    subdomain = escape_input(connection, subdomain)
    query = f"""
    INSERT IGNORE INTO {table_name} (subdomain, dnsrecord, servicediscovery, hrc, title,sec)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    cursor = connection.cursor()
    cursor.execute(query, (subdomain, 0, "unknown", 0, "",subEnumCount))
    connection.commit()
    cursor.close()


#Function to update sec in DB
def update_records(connection,table_name,subEnumCount,subdomain):
    '''
    UPDATE table_name SET sec = subEnumCount WHERE subdomain = subdomain
    '''
    table_name = escape_input(connection, table_name)
    subdomain = escape_input(connection, subdomain)
    query = f"""
    UPDATE {table_name} SET sec = {subEnumCount} where subdomain =%s
    """
    cursor = connection.cursor()
    cursor.execute(query,(subdomain,))
    connection.commit()
    cursor.close()


# Function to set dnsrecord
def set_dnsrecord(connection, domain, table_name):
    domain = escape_input(connection, domain)
    table_name = escape_input(connection, table_name)
    query = f"UPDATE {table_name} SET dnsrecord=1 WHERE subdomain=%s"
    cursor = connection.cursor()
    cursor.execute(query, (domain,))
    connection.commit()
    cursor.close()


# Function to set servicediscovery
def set_servicediscovery(connection, domain, table_name):
    domain = escape_input(connection, domain)
    table_name = escape_input(connection, table_name)
    query = f"UPDATE {table_name} SET servicediscovery='http' WHERE subdomain=%s"
    cursor = connection.cursor()
    cursor.execute(query, (domain,))
    connection.commit()
    cursor.close()


# Function to read subdomains based on a condition
def read_subdomains(connection, table_name, column=None, value=None):
    table_name = escape_input(connection, table_name)
    if column and value:
        column = escape_input(connection, column)
        value = escape_input(connection, value)
        query = f"SELECT subdomain FROM {table_name} WHERE {column}=%s"
        params = (value,)
    else:
        query = f"SELECT subdomain FROM {table_name}"
        params = ()

    cursor = connection.cursor()
    cursor.execute(query, params)
    results = cursor.fetchall()
    cursor.close()
    return [row[0] for row in results]


# Main logic
def main():
    if len(sys.argv) < 3:
        print("Usage: python script.py {insert|read} <table_name> [options]")
        sys.exit(1)

    command = sys.argv[1]
    table_name = sys.argv[2]
    connection = connect_db()

    if command == "insert":
        if sys.argv[3] == "-sub":
            for line in sys.stdin:
                insert_subdomain(connection, line.strip(), table_name, sys.argv[4])
        elif sys.argv[3] == "-dnsrec":
            for line in sys.stdin:
                set_dnsrecord(connection, line.strip(), table_name)
        elif sys.argv[3] == "-serdis":
            for line in sys.stdin:
                set_servicediscovery(connection, line.strip(), table_name)
        else:
            print("Usage: python script.py insert <table_name> { -sub | -dnsrec | -serdis }")

    elif command == "read":
        if sys.argv[3] == "-sub":
            if len(sys.argv) > 5 and sys.argv[4] == "where":
                column = sys.argv[5]
                value = sys.argv[6]
                results = read_subdomains(connection, table_name, column, value)
            else:
                results = read_subdomains(connection, table_name)
            for result in results:
                print(result)
        else:
            print("Usage: python script.py read <table_name> -sub [where <column> <value>]")
    elif command == "update":
        for line in sys.stdin:
            update_records(connection,sys.argv[2],sys.argv[3],line.strip())
    else:
        print("Usage: python script.py {insert|read} <table_name> [options]")

    connection.close()


if __name__ == "__main__":
    main()
