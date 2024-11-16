#!/bin/bash

# Database name
DB_NAME="recon"


# Function to escape inputs to prevent SQL injection
escape_input() {
    local input="$1"
    # Use the mysql command line to escape the input
    echo $(mysql $DB_NAME --batch --raw --execute="SELECT QUOTE('$input');" | tail -n 1 |  sed "s/^'//;s/'$//")
}

# Function to insert subdomain into the database
insert_subdomain() {
    local escaped_table_name=$(escape_input "$2")
    local escaped_subdomain=$(escape_input "$1")
    mysql $DB_NAME -e \
    "INSERT IGNORE INTO $escaped_table_name (subdomains, dnsrecord, servicediscovery, hrc, title) \
    VALUES ('$escaped_subdomain', false, 'unknown', 0, '');"

    # mysql $DB_NAME -e \
    # "INSERT IGNORE INTO $table_name (subdomains, dnsrecord, servicediscovery, hrc, title) \
    # VALUES ('$subdomain', false, 'unknown', 0, '');"
}

set_dnsrecord() {
    local escaped_domain=$(escape_input "$1")
    local escaped_table_name=$(escape_input "$2")
    mysql $DB_NAME -e \
    "UPDATE $escaped_table_name SET dnsrecord=1 WHERE subdomains='$escaped_domain';"
}

set_serdisrec(){
    local escaped_domain=$(escape_input "$1")
    local escaped_table_name=$(escape_input "$2")
    mysql $DB_NAME -e \
    "UPDATE $escaped_table_name SET servicediscovery=http WHERE subdomains=$escaped_domain;"
}

# Function to read subdomains from the database based on dnsrecord value
read_subdomains_dnsrecord() {
    local escaped_dnsrecord=$(escape_input $2)
    local escaped_table_name=$(escape_input $1)
    mysql -sN $DB_NAME -e \
    "SELECT subdomains FROM $escaped_table_name WHERE dnsrecord=$escaped_dnsrecord;"
}

# Function to read subdomains from the database based on servicediscovery value
read_subdomains_servicediscovery() {
    local escaped_table_name=$(escape_input "$1")
    local escaped_servicediscovery=$(escape_input "$2")
    mysql -sN $DB_NAME -e \
    "SELECT subdomains FROM $escaped_table_name WHERE servicediscovery=$escaped_servicediscovery;"
}

# Function to read subdomains from the database based on hrc value
read_subdomains_hrc() {
    local escaped_table_name=$(escape_input "$1")
    local escaped_hrc=$(escape_input "$2")
    mysql -sN $DB_NAME -e \
    "SELECT subdomains FROM $escaped_table_name WHERE hrc=$escaped_hrc;"
}

# Function to read subdomains from the database based on title pattern match
read_subdomains_title() {
    local escaped_table_name=$(escape_input "$$1")
    local escaped_title=$(escape_input "$2")
    mysql -sN $DB_NAME -e \
    "SELECT subdomains FROM $escaped_table_name WHERE title LIKE %$escaped_title%;"
}

# Main script logic
case "$1" in
    insert)
        if [[ "$3" == "-sub" ]]; then
            while read -r subdomain; do
                insert_subdomain "$subdomain" "$2"
            done
        elif [[ "$3" == "-dnsrec" ]];then
            while read -r subdomain;do
                set_dnsrecord "$subdomain" "$2"
            done
        elif [[ "$3" == "-serdis" ]];then
            while read -r subdomain;do
                set_serdisrec "$subdomain" "$2"
            done
        else
            echo "Usage: wt insert table_name { -sub | -dnsrec | -serdis }"
        fi
        ;;
    read)
        if [[ "$2" == "-sub" ]] && [[ "$4" == "where" ]]; then
            case "$5" in
                dnsrecord)
                    read_subdomains_dnsrecord "$3" "$6"
                    ;;
                servicediscovery)
                    read_subdomains_servicediscovery "$3" "$6"
                    ;;
                hrc)
                    read_subdomains_hrc "$3" "$6"
                    ;;
                title)
                    read_subdomains_title "$3" "$6"
                    ;;
                *)
                    echo "Invalid usage. Specify 'dnsrecord <value>', 'servicediscovery <value>', 'hrc <value>', or 'title <value>'"
                    ;;
            esac
        else
            echo "Usage: wt read <table name>-sub where {dnsrecord <value> | servicediscovery <value> | hrc <value> | title <value>}"
        fi
        ;;
    *)
        echo "Usage: wt {insert|read} -sub"
        ;;
esac

