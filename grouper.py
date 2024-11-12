import json
import os
from pathlib import Path
import re


with open("api-reference/openapi.json", "r") as f:
    data = json.load(f)


def escape_single_quotes(text: str) -> str:
    """
    Escapes single quotes in text by replacing ' with \'.
    Also handles other special characters that might need escaping.
    """
    return text.replace("'", "''")

def path_to_filename(path: str, method: str) -> str:
    """
    Converts a path and method to a filename base.
    Examples:
        /pets/{petId} + GET -> get-pets-petid
        /store/inventory + POST -> post-store-inventory
    """
    # Remove leading and trailing slashes
    path = path.strip('/')
    
    # Replace path parameters {param} with just param
    path = re.sub(r'{(.+?)}', r'\1', path)
    
    # Replace special characters with hyphens
    path = re.sub(r'[^a-zA-Z0-9]+', '-', path)
    
    # Combine method and path, convert to lowercase
    filename = f"{method.lower()}-{path}".lower()
    
    # Remove any duplicate or trailing hyphens
    filename = re.sub(r'-+', '-', filename).strip('-')
    
    return filename

def generate_mdx_files_per_endpoint(data: dict, output_dir: str) -> None:
    """
    Generates MDX files for each endpoint in the OpenAPI spec.
    Write them to the output_dir.
    """
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    paths = data.get('paths', {})
    
    for path, methods in paths.items():
        for method, endpoint_data in methods.items():
            # Skip if not an HTTP method
            if method.startswith('x-'):
                continue

            if isinstance(endpoint_data, list):
                continue
                
            filename = path_to_filename(path, method)
            
            # Escape the title and path
            title = escape_single_quotes(endpoint_data.get('summary', path))
            api_path = escape_single_quotes(path)
            
            # Build MDX content with escaped strings
            content = [
                '---',
                f"title: '{title}'",
                f"openapi: '{method.upper()} {api_path}'",
                '---',
                '',
                endpoint_data.get('description', ''),
                ''
            ]
            
            # Write content to file
            mdx_path = os.path.join(output_dir, f"{filename}.mdx")
            with open(mdx_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content))

def generate_groups(data: dict) -> list[dict]:
    """
    Generates nested groups based on the x-tagGroups extension.
    Returns a list of dictionaries with group names and their nested tag groups with associated pages.
    """
    # Get tag groups from extension
    tag_groups = data.get('x-tagGroups', [])
    
    # Get all paths and their tags
    paths = data.get('paths', {})
    tag_to_pages = {}
    
    # Build mapping of tags to their page filenames
    for path, methods in paths.items():
        for method, endpoint_data in methods.items():
            if method.startswith('x-'):
                continue
            if isinstance(endpoint_data, list):
                continue
                
            filename = path_to_filename(path, method)
            
            # Add filename to each tag's list of pages
            for tag in endpoint_data.get('tags', []):
                if tag not in tag_to_pages:
                    tag_to_pages[tag] = []
                tag_to_pages[tag].append(f"output/{filename}")

    # Build the nested groups structure
    groups = []
    
    for group in tag_groups:
        group_name = group.get('name')
        group_tags = group.get('tags', [])
        version = group.get('version', '2024-10-01')  # Default version if not specified
        
        # Create subgroups for each tag
        subgroups = []
        for tag in group_tags:
            pages = tag_to_pages.get(tag, [])
            if pages:  # Only add subgroup if it has pages
                subgroups.append({
                    "group": tag,
                    "pages": sorted(list(set(pages)))
                })
        
        if subgroups:  # Only add main group if it has subgroups
            groups.append({
                "group": group_name,
                "version": version,
                "pages": subgroups
            })
    
    return groups


generate_mdx_files_per_endpoint(data, "output")


with open("groups.json", "w") as f:
    json.dump(generate_groups(data), f, indent=2)

# print(generate_groups(data))

# print(data["x-tagGroups"])
