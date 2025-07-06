import os

# Define the directory structure (relative to current directory)
structure = {
    "main.py": "# Main app integration\n",
    "config.py": "# Configuration and constants\n",
    "components/": {
        "sidebar.py": "# Sidebar navigation\n",
        "voice_ui.py": "# Voice interface components\n",
        "flight_tab.py": "# Flight search functionality\n",
        "hotel_tab.py": "# Hotel search functionality\n",
        "shopping_tab.py": "# Shopping functionality\n",
        "recipe_tab.py": "# Recipe functionality\n",
        "chat_tab.py": "# Chat interface\n",
        "ui_utils.py": "# UI helper functions\n"
    },
    "agents/": {
        "flight_agent.py": "# Flight booking agent\n",
        "hotel_agent.py": "# Hotel booking agent\n",
        "shopping_agent.py": "# Shopping agent\n",
        "chat_agent.py": "# Conversation agent\n"
    }
}

def create_structure(base_path, structure):
    for name, content in structure.items():
        path = os.path.join(base_path, name)
        if name.endswith('/'):  # It's a directory
            os.makedirs(path, exist_ok=True)
            if isinstance(content, dict):
                create_structure(path, content)
        else:  # It's a file
            with open(path, 'w') as f:
                f.write(content)

# Create the structure in the current directory
create_structure('.', structure)

print("Directory structure created successfully!")