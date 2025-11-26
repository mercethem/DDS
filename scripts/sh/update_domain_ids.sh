#!/bin/bash
echo "Starting dynamic domain ID update..."

# Get script directory and project root dynamically
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
IDL_DIR="$PROJECT_ROOT/IDL"

# Navigate to IDL directory
cd "$IDL_DIR"

# Process each IDL file
for idl_file in *.idl; do
    if [ -f "$idl_file" ]; then
        # Read the first line to check for domain comment
        first_line=$(head -n 1 "$idl_file")
        
        if [[ $first_line =~ //domain=([0-9]+) ]]; then
            domain_id="${BASH_REMATCH[1]}"
            base_name=$(basename "$idl_file" .idl)
            generated_folder="${base_name}_idl_generated"
            main_file="${generated_folder}/${base_name}main.cxx"
            
            if [ -f "$main_file" ]; then
                echo "Updating $main_file with domain_id = $domain_id"
                # Use sed to replace the domain_id line
                sed -i "s/int domain_id = [0-9]\+;/int domain_id = $domain_id;/g" "$main_file"
            else
                echo "Warning: $main_file not found"
            fi
        else
            echo "Warning: No domain found in $idl_file"
        fi
    fi
done

echo "Dynamic domain ID update complete."

exit 0