import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medical_agent.settings')
django.setup()

from knowledge_graph.data_initialization import init_knowledge_graph

if __name__ == "__main__":
    print("Initializing knowledge graph...")
    init_knowledge_graph()
    print("Knowledge graph initialization completed!")
